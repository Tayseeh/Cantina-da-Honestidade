"""Rotas de auth do Confia+."""

from routes.shopping import cart_items
from services.login_attempt_service import (
    account_attempt_key,
    clear_login_attempts,
    login_is_blocked,
    register_failed_login,
)
from core import (
    DatabaseIntegrityError,
    TEMP_PASSWORD_NOTICES,
    TEMP_PASSWORD_NOTICES_LOCK,
    _normalize_username,
    _safe_internal_destination,
    abort,
    app,
    check_password_hash,
    current_user,
    db,
    execute,
    flash,
    generate_password_hash,
    jsonify,
    login_required,
    query,
    re,
    redirect,
    registrar_auditoria,
    render_template,
    request,
    role_required,
    secrets,
    session,
    string,
    url_for,
    uuid,
    wallet_balance,
)

@app.route("/api/carteira/saldo", methods=["GET"])
@login_required
def wallet_balance_api():
    """Retorna o saldo atual do cliente para sincronizar páginas abertas."""
    user = current_user()
    if not user or user["perfil"] != "cliente":
        abort(403)
    saldo = wallet_balance(user["id"])
    response = jsonify({"saldo": float(saldo)})
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def home():
    """Exibe a página inicial adequada ao perfil do usuário."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    # Clientes devem ver a página inicial Confia+; antes, esta rota os
    # redirecionava direto ao catálogo e a Home nunca chegava a aparecer.
    if user["perfil"] == "cliente":
        movimentacoes_recentes = query(
            "SELECT * FROM movimentacoes WHERE usuario_id = ? ORDER BY criado_em DESC, id DESC LIMIT 5",
            (user["id"],),
        )
        carteira = query("SELECT saldo FROM carteiras WHERE usuario_id = ?", (user["id"],), one=True)
        saldo_atual = float(carteira["saldo"]) if carteira else 0.0
        produtos_destaque = query(
            """SELECT p.id, p.nome, p.preco, p.foto, p.estoque,
                      COALESCE(SUM(ic.quantidade), 0) AS unidades_vendidas
               FROM produtos p
               LEFT JOIN itens_compra ic ON ic.produto_id = p.id
               LEFT JOIN compras c ON c.id = ic.compra_id
               WHERE p.ativo = 1 AND p.estoque > 0
               GROUP BY p.id
               ORDER BY unidades_vendidas DESC, p.nome ASC
               LIMIT 4"""
        )
        return render_template(
            "home.html", movimentacoes_recentes=movimentacoes_recentes,
            saldo_atual=saldo_atual, produtos_destaque=produtos_destaque,
        )
    if user["perfil"] == "operador":
        resumo_operador = {
            "clientes": query("SELECT COUNT(*) AS total FROM usuarios WHERE perfil = 'cliente' AND ativo = 1", one=True)["total"],
            "produtos": query("SELECT COUNT(*) AS total FROM produtos WHERE ativo = 1", one=True)["total"],
            "estoque_baixo": query("SELECT COUNT(*) AS total FROM produtos WHERE ativo = 1 AND estoque > 0 AND estoque <= estoque_baixo", one=True)["total"],
            "sem_estoque": query("SELECT COUNT(*) AS total FROM produtos WHERE ativo = 1 AND estoque <= 0", one=True)["total"],
        }
        movimentacoes_operador = query(
            "SELECT m.*, u.nome AS cliente FROM movimentacoes m JOIN usuarios u ON u.id = m.usuario_id ORDER BY m.criado_em DESC, m.id DESC LIMIT 5"
        )
        return render_template("operator_home.html", resumo=resumo_operador, movimentacoes_recentes=movimentacoes_operador)
    if user["perfil"] == "admin":
        # Indicadores voltados à gestão de acessos e ao uso geral do sistema.
        # Resumos administrativos: acessos ativos e atividade financeira recente.
        # A janela de sete dias usa o relógio do banco e inclui hoje.
        resumo = {
            "administradores": query("SELECT COUNT(*) AS total FROM usuarios WHERE perfil = 'admin' AND ativo = 1", one=True)["total"],
            "operadores": query("SELECT COUNT(*) AS total FROM usuarios WHERE perfil = 'operador' AND ativo = 1", one=True)["total"],
            "clientes_cadastrados": query("SELECT COUNT(*) AS total FROM usuarios WHERE perfil = 'cliente'", one=True)["total"],
            "compras_semana": query("SELECT COUNT(*) AS total FROM compras WHERE criado_em >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)", one=True)["total"],
            "vendas_semana": query("SELECT COALESCE(SUM(total), 0) AS total FROM compras WHERE criado_em >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)", one=True)["total"],
            "clientes_compradores_semana": query("SELECT COUNT(DISTINCT usuario_id) AS total FROM compras WHERE criado_em >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)", one=True)["total"],
            "recargas_semana": query("SELECT COALESCE(SUM(valor), 0) AS total FROM movimentacoes WHERE operacao = 'recarga' AND criado_em >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)", one=True)["total"],
            "clientes_saldo_negativo": query("SELECT COUNT(*) AS total FROM carteiras WHERE saldo < 0", one=True)["total"],
            "valor_saldo_negativo": query("SELECT COALESCE(SUM(ABS(saldo)), 0) AS total FROM carteiras WHERE saldo < 0", one=True)["total"],
        }
        return render_template("admin_home.html", resumo=resumo)
    return redirect(url_for("users"))

@app.route("/cardapio")
@role_required("cliente", "operador")
def catalog():
    """Apresenta o cardápio de produtos disponíveis para cliente ou operador."""
    if current_user()["perfil"] == "operador":
        # A tela de catálogo do operador foi descontinuada; o gerenciamento ocorre em Estoque.
        return redirect(url_for("products"))
    products = query("SELECT * FROM produtos WHERE ativo = 1 AND estoque > 0 ORDER BY nome")
    items, total = cart_items()
    return render_template(
        "catalog.html",
        produtos=products,
        itens_carrinho=items,
        total_carrinho=total,
        saldo_atual=wallet_balance(current_user()["id"]),
        saldo_negativo_ciencia_registrada=bool(query(
            "SELECT id FROM logs_auditoria WHERE alvo_id = ? AND acao = ? LIMIT 1",
            (current_user()["id"], "CIENCIA_SALDO_NEGATIVO"), one=True
        )),
        checkout_key=uuid.uuid4().hex,
    )

@app.route("/cadastro", methods=["GET", "POST"])
def register():
    """Trata a rota pública de cadastro, respeitando as regras de criação de contas."""
    if request.method == "POST":
        flash("Contas de clientes são criadas pela equipe da cantina. Solicite o cadastro ao operador.", "info")
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Valida credenciais e aplica limite persistente de tentativas por conta."""
    if request.method == "POST":
        identifier = request.form.get("identificador", "").strip().lower()
        # Resolver a conta antes do limite faz username e e-mail compartilharem
        # o mesmo contador. Identificadores inexistentes recebem chave derivada.
        user = query(
            "SELECT id, nome, username, email, senha_hash, perfil, ativo, precisa_definir_acesso "
            "FROM usuarios WHERE (lower(username) = ? OR lower(email) = ?) AND ativo = 1",
            (identifier, identifier),
            one=True,
        )
        attempt_key = account_attempt_key(identifier, user["id"] if user else None)
        connection = db()
        if login_is_blocked(connection, attempt_key):
            flash("Muitas tentativas de acesso. Aguarde alguns minutos e tente novamente.", "danger")
            return render_template("login.html"), 429

        if user and check_password_hash(user["senha_hash"], request.form.get("senha", "")):
            clear_login_attempts(connection, attempt_key)
            session.clear()
            session.permanent = True
            session["user_id"] = user["id"]
            if user["precisa_definir_acesso"]:
                return redirect(url_for("first_access"))
            destination = _safe_internal_destination(request.args.get("next"))
            if not destination:
                destination = url_for("home")
            return redirect(destination)

        register_failed_login(connection, attempt_key)
        flash("Dados de acesso inválidos.", "danger")
    return render_template("login.html")

@app.route("/primeiro-acesso", methods=["GET", "POST"])
@login_required
def first_access():
    """Conduz o usuário pela definição inicial de senha e, para clientes, PIN."""
    user = current_user()
    if not user["precisa_definir_acesso"]:
        return redirect(url_for("catalog" if user["perfil"] == "cliente" else "home"))
    if request.method == "POST":
        password = request.form.get("senha", "")
        password_confirmation = request.form.get("confirmar_senha", "")
        pin = request.form.get("pin", "")
        pin_confirmation = request.form.get("confirmar_pin", "")
        is_customer = user["perfil"] == "cliente"
        if not 8 <= len(password) <= 20 or not re.search(r"[^\W\d_]", password, flags=re.UNICODE) or not re.search(r"\d", password):
            flash("Use de 8 a 20 caracteres, incluindo uma letra e um número.", "danger")
        elif password != password_confirmation:
            flash("A confirmação da senha não corresponde.", "danger")
        elif is_customer and not re.fullmatch(r"\d{4}", pin):
            flash("O PIN deve conter exatamente 4 números.", "danger")
        elif is_customer and pin != pin_confirmation:
            flash("A confirmação do PIN não corresponde.", "danger")
        else:
            if is_customer:
                execute(
                    "UPDATE usuarios SET senha_hash = ?, pin_hash = ?, precisa_definir_acesso = 0 WHERE id = ?",
                    (generate_password_hash(password), generate_password_hash(pin), user["id"]),
                )
            else:
                execute(
                    "UPDATE usuarios SET senha_hash = ?, pin_hash = NULL, precisa_definir_acesso = 0 WHERE id = ?",
                    (generate_password_hash(password), user["id"]),
                )
            flash("Senha alterada. Seu acesso foi configurado.", "success")
            return redirect(url_for("catalog" if is_customer else "home"))
    return render_template("first_access.html", usuario=user)

@app.route("/clientes/novo", methods=["GET", "POST"])
@role_required("operador")
def create_customer():
    # O cadastro de clientes fica dentro da página de gerenciamento do operador.
    """Cadastra um cliente e prepara sua carteira e acesso inicial."""
    if request.method == "GET":
        return redirect("/operador/clientes")
    dados = request.form
    if request.method == "POST":
        first = request.form.get("nome", "").strip()
        surname = request.form.get("sobrenome", "").strip()
        enrollment_input = request.form.get("matricula", "").strip()
        enrollment = "".join(character for character in enrollment_input if character.isdigit())
        email_input = request.form.get("email", "").strip().lower()
        email = email_input or None
        cpf_input = request.form.get("cpf", "").strip()
        cpf_digits = "".join(character for character in cpf_input if character.isdigit()) or None
        phone_input = request.form.get("telefone", "").strip()
        phone_digits = "".join(character for character in phone_input if character.isdigit()) or None
        if phone_digits and phone_digits.startswith("55") and len(phone_digits) in (12, 13):
            phone_digits = phone_digits[2:]
        # O nome de usuário deve ser informado manualmente no formulário.
        requested_username = _normalize_username(request.form.get("username", ""))
        name_pattern = r"[^\W\d_]+(?:[ '-][^\W\d_]+)*"
        email_pattern = r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+"
        errors = []
        if not first or len(first) > 30 or not re.fullmatch(name_pattern, first, flags=re.UNICODE):
            errors.append("Informe um nome válido, com até 30 caracteres.")
        if not surname or len(surname) > 30 or not re.fullmatch(name_pattern, surname, flags=re.UNICODE):
            errors.append("Informe um sobrenome válido, com até 30 caracteres.")
        if not enrollment or len(enrollment) > 14:
            errors.append("Matrícula: informe de 1 a 14 números.")
        if email and (len(email) > 50 or not re.fullmatch(email_pattern, email, flags=re.IGNORECASE)):
            errors.append("Informe um e-mail válido com até 50 caracteres ou deixe o campo vazio.")
        if cpf_input and not re.fullmatch(r"(?:\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})", cpf_input):
            errors.append("Informe um CPF com 11 números ou deixe o campo vazio.")
        if cpf_digits and len(cpf_digits) != 11:
            errors.append("O CPF deve conter 11 números.")
        if phone_input:
            valid_phone = bool(re.fullmatch(r"[\d\s()+.-]+", phone_input) and phone_digits and len(phone_digits) in (10, 11) and phone_digits[:2] in {"11","12","13","14","15","16","17","18","19","21","22","24","27","28","31","32","33","34","35","37","38","41","42","43","44","45","46","47","48","49","51","53","54","55","61","62","63","64","65","66","67","68","69","71","73","74","75","77","79","81","82","83","84","85","86","87","88","89","91","92","93","94","95","96","97","98","99"})
            if valid_phone:
                subscriber = phone_digits[2:]
                valid_phone = (len(subscriber) == 9 and subscriber.startswith("9")) or (len(subscriber) == 8 and subscriber[0] in "2345")
            if not valid_phone:
                errors.append("Informe um telefone brasileiro válido ou deixe o campo vazio.")
        if not 3 <= len(requested_username) <= 30 or not re.fullmatch(r"[a-z0-9]+(?:\.[a-z0-9]+)*", requested_username):
            errors.append("O usuário deve ter de 3 a 30 caracteres, usando letras sem acento, números e pontos entre palavras.")
        elif query("SELECT id FROM usuarios WHERE lower(username) = lower(?)", (requested_username,), one=True):
            errors.append("Esse nome de usuário já está em uso. Escolha outro.")
        if query("SELECT id FROM usuarios WHERE matricula = ?", (enrollment,), one=True):
            errors.append("Já existe uma conta com essa matrícula.")
        if email and query("SELECT id FROM usuarios WHERE lower(email) = lower(?)", (email,), one=True):
            errors.append("Já existe uma conta com esse e-mail.")
        if cpf_digits and query("SELECT id FROM usuarios WHERE cpf = ?", (cpf_digits,), one=True):
            errors.append("Já existe uma conta com esse CPF.")
        if errors:
            for error in errors:
                flash(error, "danger")
            return redirect("/operador/clientes?novo=1")

        alphabet = string.ascii_letters + string.digits
        temporary_password = secrets.choice(string.ascii_letters) + secrets.choice(string.digits) + "".join(secrets.choice(alphabet) for _ in range(8))
        username = requested_username
        connection = db()
        try:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                "INSERT INTO usuarios (nome, sobrenome, matricula, email, cpf, telefone, username, senha_hash, perfil, precisa_definir_acesso) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'cliente', 1)",
                (f"{first} {surname}", surname, enrollment, email, cpf_digits, phone_digits or "", username, generate_password_hash(temporary_password)),
            )
            customer_id = cursor.lastrowid
            connection.execute("INSERT INTO carteiras (usuario_id, saldo) VALUES (?, 0)", (customer_id,))
            created_customer = connection.execute("SELECT id, nome, perfil FROM usuarios WHERE id = ?", (customer_id,)).fetchone()
            registrar_auditoria("Cliente cadastrado", created_customer, f"Matrícula: {enrollment}; cadastro realizado por operador.", connection)
            connection.commit()
        except DatabaseIntegrityError:
            connection.rollback()
            if query("SELECT id FROM usuarios WHERE lower(username) = lower(?)", (username,), one=True):
                flash("Esse nome de usuário acabou de ser usado. Escolha outro.", "danger")
            else:
                flash("Matrícula, e-mail ou CPF já cadastrado. Confira os dados.", "danger")
            return redirect("/operador/clientes?novo=1")
        # Exibe a senha temporária uma única vez na própria página de gerenciamento.
        with TEMP_PASSWORD_NOTICES_LOCK:
            TEMP_PASSWORD_NOTICES[current_user()["id"]] = {"nome": f"{first} {surname}", "username": username, "senha": temporary_password, "perfil": "cliente"}
        flash("Cliente cadastrado. Entregue a senha temporária em particular; ela será exigida apenas no primeiro acesso.", "success")
        return redirect("/operador/clientes")
    return redirect("/operador/clientes?novo=1")

@app.route("/sair", methods=["POST"])
def logout():
    """Encerra a sessão autenticada do usuário."""
    session.clear(); flash("Sessão encerrada.", "info")
    return redirect(url_for("home"))

@app.errorhandler(413)
def uploaded_file_too_large(_error):
    """Apresenta uma resposta amigável quando o upload excede o limite permitido."""
    flash("A foto deve ter até 4 MB.", "danger")
    if request.path.startswith("/produtos"):
        return redirect(url_for("products"))
    return redirect(url_for("profile", editar=1))
