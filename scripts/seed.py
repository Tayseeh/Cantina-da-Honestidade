"""
Carga opcional de dados fictícios para demonstração do Confia+.

Execute na raiz do projeto:
    python scripts/seed.py

O script não exclui nem atualiza registros existentes. Contas são identificadas
por username/e-mail e produtos pelo nome. Campos vazios dos clientes de demonstração
são completados sem sobrescrever dados já preenchidos. Senhas e PINs são armazenados com hash.
"""
from __future__ import annotations

# Permite executar `python scripts/seed.py` a partir da raiz do projeto.
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from werkzeug.security import generate_password_hash

from apli import app, initialize_database
from database import query, execute


# Contas fictícias usadas exclusivamente para demonstração e testes locais.
USUARIOS = [
    {
        "nome": "Administrador Demonstração", "sobrenome": "Demonstração",
        "username": "admin", "email": "admin@cantina.local",
        "senha": "Admin@12345", "perfil": "admin", "saldo": 0,
    },
    {
        "nome": "Mariana Costa", "sobrenome": "Costa",
        "username": "operador1", "email": "operador1@cantina.local",
        "senha": "Operador@12345", "perfil": "operador", "saldo": 0,
    },
    {
        "nome": "Rafael Souza", "sobrenome": "Souza",
        "username": "operador2", "email": "operador2@cantina.local",
        "senha": "Operador@12345", "perfil": "operador", "saldo": 0,
    },
    {
        "nome": "Ana Lima", "sobrenome": "Lima", "matricula": "2026 0145 00342 8",
        "email": "cliente1@cantina.local", "cpf": "390.533.447-05",
        "telefone": "(48) 99123-4501", "data_nascimento": "12/04/2001",
        "username": "cliente1", "senha": "Cliente@12345", "pin": "1234",
        "perfil": "cliente", "saldo": 20,
    },
    {
        "nome": "Marcos Alves", "sobrenome": "Alves", "matricula": "2026 0145 00343 6",
        "email": "cliente2@cantina.local", "cpf": "168.995.350-09",
        "telefone": "(48) 99234-5602", "data_nascimento": "23/09/1999",
        "username": "cliente2", "senha": "Cliente@12345", "pin": "2345",
        "perfil": "cliente", "saldo": 20,
    },
    {
        "nome": "Beatriz Oliveira", "sobrenome": "Oliveira", "matricula": "2026 0145 00344 4",
        "email": "cliente3@cantina.local", "cpf": "529.982.247-25",
        "telefone": "(48) 99345-6703", "data_nascimento": "05/02/2002",
        "username": "cliente3", "senha": "Cliente@12345", "pin": "3456",
        "perfil": "cliente", "saldo": 20,
    },
    {
        "nome": "Lucas Pereira", "sobrenome": "Pereira", "matricula": "2026 0145 00345 2",
        "email": "cliente4@cantina.local", "cpf": "111.444.777-35",
        "telefone": "(48) 99456-7804", "data_nascimento": "17/11/2000",
        "username": "cliente4", "senha": "Cliente@12345", "pin": "4567",
        "perfil": "cliente", "saldo": 20,
    },
    {
        "nome": "Camila Martins", "sobrenome": "Martins", "matricula": "2026 0145 00346 0",
        "email": "cliente5@cantina.local", "cpf": "123.456.789-09",
        "telefone": "(48) 99567-8905", "data_nascimento": "30/06/2001",
        "username": "cliente5", "senha": "Cliente@12345", "pin": "5678",
        "perfil": "cliente", "saldo": 20,
    },
]

# Catálogo inicial de produtos fictícios: nome, descrição, custo, venda e estoque.
PRODUTOS = [
    ("Água mineral 500 ml", "Garrafa de água mineral sem gás.", 1.00, 2.00, 30),
    ("Refrigerante lata", "Refrigerante em lata 350 ml.", 3.50, 5.00, 20),
    ("Suco de caixinha", "Suco de fruta em embalagem individual.", 2.50, 4.00, 20),
    ("Café", "Café em copo individual.", 1.00, 2.50, 30),
    ("Pão de queijo", "Porção individual de pão de queijo.", 1.50, 3.00, 25),
    ("Salgado assado", "Salgado assado de tamanho individual.", 3.00, 5.00, 20),
    ("Sanduíche natural", "Sanduíche natural embalado individualmente.", 5.00, 8.00, 12),
    ("Biscoito", "Pacote individual de biscoitos.", 2.00, 3.50, 20),
    ("Chocolate", "Barra pequena de chocolate.", 2.50, 4.50, 15),
    ("Barra de cereal", "Barra de cereal individual.", 1.80, 3.50, 15),
]


def inserir_usuarios() -> tuple[int, int, int]:
    """Cria as contas e completa somente campos vazios dos clientes de demonstração."""
    criados = 0
    ignorados = 0
    completados = 0
    for usuario in USUARIOS:
        existente = query(
            "SELECT id, perfil FROM usuarios WHERE username = ? OR email = ? LIMIT 1",
            (usuario["username"], usuario["email"]),
            one=True,
        )
        if existente:
            ignorados += 1
            usuario_id = existente["id"]
            # Não sobrescreve dados já preenchidos nem altera saldo/senha do usuário.
            if usuario["perfil"] == "cliente" and existente["perfil"] == "cliente":
                execute(
                    """UPDATE usuarios SET
                           nome = CASE WHEN TRIM(nome) = ? THEN ? ELSE nome END,
                           matricula = COALESCE(NULLIF(TRIM(matricula), ''), ?),
                           cpf = COALESCE(NULLIF(TRIM(cpf), ''), ?),
                           telefone = COALESCE(NULLIF(TRIM(telefone), ''), ?),
                           data_nascimento = COALESCE(NULLIF(TRIM(data_nascimento), ''), ?),
                           pin_hash = COALESCE(NULLIF(pin_hash, ''), ?)
                       WHERE id = ?""",
                    (
                        usuario["nome"].split()[0], usuario["nome"],
                        usuario["matricula"], usuario["cpf"], usuario["telefone"],
                        usuario["data_nascimento"], generate_password_hash(usuario["pin"]),
                        usuario_id,
                    ),
                )
                completados += 1
            carteira = query(
                "SELECT id FROM carteiras WHERE usuario_id = ? LIMIT 1",
                (usuario_id,), one=True,
            )
            if not carteira:
                execute(
                    "INSERT INTO carteiras (usuario_id, saldo) VALUES (?, ?)",
                    (usuario_id, usuario["saldo"]),
                )
            continue

        if usuario["perfil"] == "cliente":
            usuario_id = execute(
                """INSERT INTO usuarios
                   (nome, sobrenome, matricula, email, cpf, telefone, data_nascimento,
                    username, senha_hash, pin_hash, perfil, ativo, precisa_definir_acesso)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0)""",
                (
                    usuario["nome"], usuario["sobrenome"], usuario["matricula"],
                    usuario["email"], usuario["cpf"], usuario["telefone"],
                    usuario["data_nascimento"], usuario["username"],
                    generate_password_hash(usuario["senha"]),
                    generate_password_hash(usuario["pin"]), usuario["perfil"],
                ),
            )
        else:
            usuario_id = execute(
                """INSERT INTO usuarios
                   (nome, sobrenome, username, email, senha_hash, perfil, ativo,
                    precisa_definir_acesso)
                   VALUES (?, ?, ?, ?, ?, ?, 1, 0)""",
                (
                    usuario["nome"], usuario["sobrenome"], usuario["username"],
                    usuario["email"], generate_password_hash(usuario["senha"]),
                    usuario["perfil"],
                ),
            )
        execute(
            "INSERT INTO carteiras (usuario_id, saldo) VALUES (?, ?)",
            (usuario_id, usuario["saldo"]),
        )
        criados += 1
    return criados, ignorados, completados


def inserir_produtos() -> tuple[int, int]:
    """Insere os produtos fictícios que ainda não existem no banco."""
    criados = 0
    ignorados = 0
    for nome, descricao, custo, preco, estoque in PRODUTOS:
        existente = query(
            "SELECT id FROM produtos WHERE LOWER(nome) = LOWER(?) LIMIT 1",
            (nome,),
            one=True,
        )
        if existente:
            ignorados += 1
            continue
        execute(
            """INSERT INTO produtos
               (nome, descricao, preco_compra, preco, estoque, ativo, foto)
               VALUES (?, ?, ?, ?, ?, 1, '')""",
            (nome, descricao, custo, preco, estoque),
        )
        criados += 1
    return criados, ignorados


def main() -> None:
    """Executa a rotina principal do script a partir das configurações do projeto."""
    with app.app_context():
        initialize_database()
        usuarios_criados, usuarios_existentes, clientes_completados = inserir_usuarios()
        produtos_criados, produtos_existentes = inserir_produtos()
        print("\nCarga de demonstração concluída.")
        print(f"Usuários criados: {usuarios_criados}; já existentes: {usuarios_existentes}; clientes conferidos/completados: {clientes_completados}.")
        print(f"Produtos criados: {produtos_criados}; já existentes ignorados: {produtos_existentes}.")
        print("Dados já preenchidos, senhas e saldos existentes foram preservados. Campos cadastrais vazios dos clientes de demonstração foram completados.")
        print("\nAcesse o sistema usando um dos usernames e senhas documentados no README.")


if __name__ == "__main__":
    main()
