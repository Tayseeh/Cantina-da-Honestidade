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

# Catálogo oficial de demonstração da Cantina da Honestidade.
# Formato: (nome, descrição, categoria, custo demonstrativo, preço demonstrativo, estoque).
PRODUTOS = [
    ("Wanflo - Batata Chips Lisa Clássica", "Batata chips lisa sabor clássico.", "Salgadinhos", 2.50, 4.00, 18),
    ("Pratic Leve - Batata Ondulada Bacon", "Batata ondulada sabor bacon.", "Salgadinhos", 2.50, 4.00, 18),
    ("Wanflo - Batata Ondulada Cebola e Salsa", "Batata ondulada sabor cebola e salsa.", "Salgadinhos", 2.50, 4.00, 18),
    ("Wanflo - Batata Ondulada Original", "Batata ondulada sabor original.", "Salgadinhos", 2.50, 4.00, 18),
    ("Wanflo - Batata Chips Lisa Picanha na Chapa", "Batata chips lisa sabor picanha na chapa.", "Salgadinhos", 2.50, 4.00, 18),
    ("Santa Fé - Wafer Surf Morango", "Biscoito wafer sabor morango.", "Biscoitos e Bolinhos", 1.50, 2.50, 20),
    ("Santa Fé - Wafer Surf Chocolate", "Biscoito wafer sabor chocolate.", "Biscoitos e Bolinhos", 1.50, 2.50, 20),
    ("Santa Fé - Wafer Surf Limão", "Biscoito wafer sabor limão.", "Biscoitos e Bolinhos", 1.50, 2.50, 20),
    ("Nestlé - Biscoito Recheado Passatempo Chocolate", "Biscoito recheado sabor chocolate.", "Biscoitos e Bolinhos", 2.00, 3.50, 16),
    ("Bimbo - Bolinho Ana Maria Gotas de Chocolate", "Bolinho com gotas de chocolate.", "Biscoitos e Bolinhos", 2.50, 4.00, 16),
    ("Florestal - Flopito Chicle Giga Morango", "Chiclete sabor morango.", "Doces e Balas", 0.50, 1.00, 30),
    ("Florestal - Flopito Chicle Giga Melancia", "Chiclete sabor melancia.", "Doces e Balas", 0.50, 1.00, 30),
    ("Florestal - Flopito Chicle Giga Energético", "Chiclete sabor energético.", "Doces e Balas", 0.50, 1.00, 30),
    ("Florestal - Flopito Chicle Giga Q'Pinta Tutti-Frutti", "Chiclete tutti-frutti que colore a língua de azul.", "Doces e Balas", 0.50, 1.00, 30),
    ("Santa Helena - Paçoquita Rolha", "Doce de amendoim tipo rolha.", "Doces e Balas", 0.80, 1.50, 24),
    ("Fini - Tubes Uva", "Bala de gelatina em tubos sabor uva.", "Doces e Balas", 1.00, 2.00, 20),
    ("Dori - Bala de Gelatina Banana", "Bala de gelatina em formato de banana.", "Doces e Balas", 0.80, 1.50, 20),
    ("Fini - Tubes Framboesa Pinta Língua", "Bala de gelatina em tubos sabor framboesa.", "Doces e Balas", 1.00, 2.00, 20),
    ("Fini - Tubes Twister", "Bala de gelatina em tubos sabor frutas silvestres.", "Doces e Balas", 1.00, 2.00, 20),
    ("Doces Carijós - Pé de Moleque", "Doce de amendoim com açúcar caramelizado.", "Doces e Balas", 0.80, 1.50, 24),
    ("Tirol - Bebida Láctea Kids Shrek Chocolate", "Bebida láctea UHT sabor chocolate.", "Bebidas", 2.00, 3.50, 18),
]

NOMES_PRODUTOS_ATIVOS = {item[0].casefold() for item in PRODUTOS}
PRODUTOS_ANTIGOS_DO_SEED = [
    "Água mineral 500 ml", "Refrigerante lata", "Suco de caixinha", "Café",
    "Pão de queijo", "Salgado assado", "Sanduíche natural", "Biscoito",
    "Chocolate", "Barra de cereal", "Salgadinho ondulado - pacote individual",
    "Batata chips - pacote individual", "Salgadinho - pacote individual",
    "Biscoito wafer - pacote", "Biscoito doce - pacote individual",
    "Biscoito recheado - pacote individual", "Bala sortida - unidade",
    "Bala mastigável - unidade", "Doce sortido - pacote",
    "Snack salgado - pacote individual", "Wanflo - Batata ondulada original",
    "Batata Chips Lisa Clássica", "Batata Ondulada Bacon", "Batata Ondulada Cebola e Salsa",
    "Batata Ondulada Original", "Batata Chips Lisa Picanha na Chapa", "Wafer Surf Morango",
    "Wafer Surf Chocolate", "Wafer Surf Limão", "Biscoito Recheado Passatempo Chocolate",
    "Bolinho Ana Maria Gotas de Chocolate", "Flopito Chicle Giga Morango",
    "Flopito Chicle Giga Melancia", "Flopito Chicle Giga Energético",
    "Flopito Chicle Giga Q'Pinta Tutti-Frutti", "Paçoquita Rolha", "Fini Tubes Uva",
    "Bala de Gelatina Banana", "Fini Tubes Framboesa Pinta Língua", "Fini Tubes Twister",
    "Pé de Moleque", "Bebida Láctea Tirol Kids Shrek Chocolate",
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
    """Sincroniza o catálogo sem excluir produtos vinculados a compras antigas."""
    criados = 0
    atualizados = 0
    # Desativa apenas os itens dos catálogos de demonstração anteriores.
    # Outros produtos cadastrados manualmente e seus históricos são preservados.
    placeholders = ", ".join(["?"] * len(PRODUTOS_ANTIGOS_DO_SEED))
    execute(
        f"UPDATE produtos SET ativo = 0 WHERE LOWER(nome) IN ({placeholders})",
        tuple(nome.lower() for nome in PRODUTOS_ANTIGOS_DO_SEED),
    )

    for nome, descricao, categoria, custo, preco, estoque in PRODUTOS:
        existente = query("SELECT id FROM produtos WHERE LOWER(nome) = LOWER(?) LIMIT 1", (nome,), one=True)
        if existente:
            execute("UPDATE produtos SET descricao=?, categoria=?, ativo=1 WHERE id=?", (descricao, categoria, existente["id"]))
            atualizados += 1
            continue
        execute(
            """INSERT INTO produtos
               (nome, descricao, categoria, preco_compra, preco, estoque, ativo, foto)
               VALUES (?, ?, ?, ?, ?, ?, 1, '')""",
            (nome, descricao, categoria, custo, preco, estoque),
        )
        criados += 1
    return criados, atualizados


def main() -> None:
    """Executa a rotina principal do script a partir das configurações do projeto."""
    with app.app_context():
        initialize_database()
        usuarios_criados, usuarios_existentes, clientes_completados = inserir_usuarios()
        produtos_criados, produtos_atualizados = inserir_produtos()
        print("\nCarga de demonstração concluída.")
        print(f"Usuários criados: {usuarios_criados}; já existentes: {usuarios_existentes}; clientes conferidos/completados: {clientes_completados}.")
        print(f"Produtos criados: {produtos_criados}; produtos atualizados: {produtos_atualizados}; catálogo ativo: {len(PRODUTOS)} itens.")
        print("Dados já preenchidos, senhas e saldos existentes foram preservados. Campos cadastrais vazios dos clientes de demonstração foram completados.")
        print("\nAcesse o sistema usando um dos usernames e senhas documentados no README.")


if __name__ == "__main__":
    main()
