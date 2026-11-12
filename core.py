"""Configuração do Flask e funções compartilhadas pelas rotas.

Serviços especializados ficam em media_service.py e schema_service.py.
Este módulo mantém imports de compatibilidade para as rotas existentes.
"""

import os
from dotenv import load_dotenv
load_dotenv()
import re
import secrets
import string
import uuid  # Mantido para compatibilidade com as rotas existentes.
import threading
from urllib.parse import urlsplit
from datetime import datetime
from decimal import Decimal
from functools import wraps


from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import close_db, execute, get_db as db, query, DatabaseIntegrityError
from services.wallet_service import wallet_balance
from media_service import process_profile_photo, store_product_photo, migrate_legacy_product_photos
from schema_service import initialize_database
from domain_utils import (
    format_br_phone, format_datetime_br, money,
    normalize_username as _normalize_username,
    profile_form_values, username_base as _username_base,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# MySQL 8 é o banco oficial. Credenciais são lidas do ambiente/.env.
app = Flask(__name__)


@app.template_filter("matricula_br")
def format_enrollment_br(value):
    """Formata matrículas de até 14 dígitos em grupos 4-4-5-1 para exibição."""
    digits = re.sub(r"\\D", "", str(value or ""))[:14]
    if not digits:
        return "—"
    if len(digits) == 14:
        return f"{digits[:4]} {digits[4:8]} {digits[8:13]} {digits[13:]}"
    return digits
app.config.update(DATABASE_BACKEND="mysql")
# Senhas temporárias são exibidas uma única vez ao administrador criador, sem
# armazená-las em cookie/sessão assinada. Em execução local, o aviso fica em memória.
TEMP_PASSWORD_NOTICES = {}
TEMP_PASSWORD_NOTICES_LOCK = threading.Lock()
IS_PRODUCTION = os.environ.get("APP_ENV", "development").strip().lower() == "production"
secret_key = os.environ.get("CANTINA_SECRET_KEY")
if IS_PRODUCTION and (not secret_key or len(secret_key) < 32 or secret_key == "troque-esta-chave-em-producao"):
    raise RuntimeError("Em produção, configure uma CANTINA_SECRET_KEY privada com pelo menos 32 caracteres antes de iniciar o Confia+.")
if not secret_key:
    # Chave fixa apenas para desenvolvimento local: evita que cada processo/worker
    # invalide os cookies e tokens CSRF gerados por outro processo. Nunca usar em produção.
    secret_key = "confia-dev-only-change-before-production-2026"
    print("AVISO: usando chave fixa de desenvolvimento. Configure CANTINA_SECRET_KEY antes de publicar.")
app.config.update(
    SECRET_KEY=secret_key,
    PERMANENT_SESSION_LIFETIME=1800,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=IS_PRODUCTION,
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
)



def _safe_internal_destination(destination):
    """Valida o destino de redirecionamento para aceitar apenas caminhos internos seguros."""
    if not destination:
        return None
    parsed = urlsplit(destination)
    if parsed.scheme or parsed.netloc or not destination.startswith("/") or destination.startswith("//") or "\\" in destination:
        return None
    return destination


# O app também pode ser iniciado por `flask --app apli run`, caso em que o bloco
# `if __name__ == "__main__"` não é executado. Inicializamos/migramos o banco na
# primeira requisição para garantir que colunas novas (como usuarios.username)
# existam antes de qualquer rota consultar a tabela.
_database_initialized = False
_database_init_lock = threading.Lock()


@app.before_request
def ensure_database_initialized():
    """Garante que a estrutura do banco esteja inicializada antes de atender a requisição."""
    global _database_initialized
    if _database_initialized:
        return None
    with _database_init_lock:
        if not _database_initialized:
            migrate_legacy_product_photos()
            initialize_database()
            _database_initialized = True
    return None

@app.before_request
def protect_state_changing_requests():
    # Cria o token no início da sessão de navegação, inclusive antes de renderizar páginas
    # cujo JavaScript fará POST/DELETE por fetch.
    """Aplica a proteção CSRF às requisições que alteram dados."""
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        if not session.get("_csrf_token"):
            session["_csrf_token"] = secrets.token_urlsafe(32)
        return None

    # Aceita os formatos usados por formulários HTML, fetch e clientes JSON.
    expected = session.get("_csrf_token")
    supplied = (
        request.form.get("csrf_token")
        or request.headers.get("X-CSRF-Token")
        or request.headers.get("X-CSRFToken")
    )
    if not supplied and request.is_json:
        payload = request.get_json(silent=True) or {}
        supplied = payload.get("csrf_token") if isinstance(payload, dict) else None
    if not expected or not supplied or not secrets.compare_digest(str(expected), str(supplied)):
        if request.path.startswith("/api/") or request.is_json or request.headers.get("Accept", "").find("application/json") >= 0:
            return jsonify(error="A sessão de segurança expirou. Atualize a página e tente novamente."), 400
        abort(400, description="Token de segurança ausente ou inválido. Atualize a página e tente novamente.")


@app.context_processor
def inject_security_helpers():
    """Disponibiliza funções auxiliares de segurança para os templates."""
    def csrf_token():
        """Obtém ou cria o token CSRF associado à sessão atual."""
        token = session.get("_csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["_csrf_token"] = token
        return token
    return {"csrf_token": csrf_token}


app.teardown_appcontext(close_db)


def current_user():
    """Carrega o usuário uma única vez por requisição e reutiliza o resultado."""
    if not hasattr(g, "current_user_cache"):
        user_id = session.get("user_id")
        g.current_user_cache = (
            query(
                "SELECT id, nome, sobrenome, matricula, email, cpf, username, "
                "senha_hash, telefone, data_nascimento, pin_hash, foto_perfil, "
                "perfil, ativo, precisa_definir_acesso, criado_em "
                "FROM usuarios WHERE id = ? AND ativo = 1",
                (user_id,), one=True,
            )
            if user_id else None
        )
    return g.current_user_cache


app.jinja_env.filters["telefone_br"] = format_br_phone

app.jinja_env.filters["data_hora_br"] = format_datetime_br
app.jinja_env.filters["data_br"] = lambda value: format_datetime_br(value, include_time=False)


@app.context_processor
def globals_for_templates():
    """Disponibiliza variáveis e funções globais utilizadas pelos templates."""
    user = current_user()
    unread = []
    unread_count = 0
    if user and user["perfil"] == "cliente":
        # Limita os campos transferidos e usa o índice composto de notificações.
        unread = query(
            "SELECT id, mensagem, criado_em FROM notificacoes "
            "WHERE usuario_id = ? AND lida = 0 ORDER BY criado_em DESC, id DESC LIMIT 5",
            (user["id"],),
        )
        unread_count = query(
            "SELECT COUNT(*) AS total FROM notificacoes WHERE usuario_id = ? AND lida = 0",
            (user["id"],), one=True,
        )["total"]
    return {"usuario_logado": user, "saldo_atual": wallet_balance(user["id"]) if user else None, "notificacoes_nao_lidas": unread, "notificacoes_nao_lidas_count": unread_count}


def login_required(view):
    """Restringe a rota a usuários que possuem uma sessão autenticada."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        """Executa a rota protegida após validar sessão e/ou perfil de acesso."""
        if not current_user():
            flash("Faça login para acessar esta página.", "warning")
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    """Cria um decorador que restringe o acesso aos perfis informados."""
    def decorator(view):
        """Aplica a regra de autorização aos métodos de uma rota."""
        @wraps(view)
        def wrapped(*args, **kwargs):
            """Executa a rota protegida após validar sessão e/ou perfil de acesso."""
            user = current_user()
            if not user:
                return redirect(url_for("login"))
            if user["perfil"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.before_request
def require_initial_access_setup():
    """Bloqueia todos os perfis até concluir a configuração inicial de suas credenciais."""
    user = current_user()
    allowed_endpoints = {"first_access", "logout", "static"}
    if user and user["precisa_definir_acesso"] and request.endpoint not in allowed_endpoints:
        return redirect(url_for("first_access"))


def _available_username(first_name, surname, exclude_user_id=None):
    """Gera um nome de usuário disponível, evitando conflitos com outras contas."""
    base = _username_base(first_name, surname)
    candidate = base
    suffix = 2
    while True:
        sql = "SELECT id FROM usuarios WHERE lower(username) = lower(?)"
        params = [candidate]
        if exclude_user_id is not None:
            sql += " AND id != ?"
            params.append(exclude_user_id)
        if not query(sql, tuple(params), one=True):
            return candidate
        candidate = f"{base}{suffix}"
        suffix += 1


def registrar_auditoria(acao, alvo=None, detalhes="", connection=None):
    """Registra ações relevantes para rastreabilidade, sem guardar senhas ou PINs."""
    actor = current_user()
    if not actor:
        return
    target_id = alvo["id"] if alvo else None
    target_name = alvo["nome"] if alvo else "—"
    target_profile = alvo["perfil"] if alvo and "perfil" in alvo.keys() else ""
    conn = connection or db()
    conn.execute(
        "INSERT INTO logs_auditoria (responsavel_id, responsavel_nome, responsavel_perfil, acao, alvo_id, alvo_nome, alvo_perfil, detalhes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (actor["id"], actor["nome"], actor["perfil"], acao, target_id, target_name, target_profile, str(detalhes or "")[:500]),
    )
    if connection is None:
        conn.commit()



# Tratamento global de erros HTTP.
@app.errorhandler(403)
def forbidden(_error):
    """Renderiza a página de erro para acessos sem autorização."""
    return render_template("error.html", code=403, message="Você não tem permissão para esta página."), 403

@app.errorhandler(404)
def not_found(_error):
    """Renderiza a página apresentada quando uma rota não existe."""
    return render_template("error.html", code=404, message="Página não encontrada."), 404
