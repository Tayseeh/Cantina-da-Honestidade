"""Criação e atualização da estrutura do banco de dados do Confia+.

Este módulo contém somente a definição das tabelas e índices iniciais.
Não apaga dados existentes.
"""

from database import get_db as db


def initialize_database():
    """Cria o esquema relacional no MySQL 8. Não apaga tabelas existentes."""
    connection = db()
    active_schema = connection.execute("SELECT DATABASE() AS schema_name").fetchone()
    print(f"CONFIA+ - esquema ativo: {active_schema['schema_name']}")
    # Cada bloco define uma tabela e seus índices/relacionamentos. IF NOT EXISTS
    # permite iniciar o sistema sem recriar tabelas que já contenham dados.
    statements = [
        """CREATE TABLE IF NOT EXISTS usuarios (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(150) NOT NULL, matricula VARCHAR(40) NULL UNIQUE,
            email VARCHAR(190) NULL UNIQUE, cpf VARCHAR(20) NULL UNIQUE,
            username VARCHAR(80) NULL UNIQUE, senha_hash VARCHAR(255) NOT NULL,
            sobrenome VARCHAR(100) NOT NULL DEFAULT '', telefone VARCHAR(30) NOT NULL DEFAULT '',
            data_nascimento VARCHAR(20) NOT NULL DEFAULT '', pin_hash VARCHAR(255) NULL,
            foto_perfil VARCHAR(255) NOT NULL DEFAULT '',
            perfil ENUM('cliente','operador','admin') NOT NULL DEFAULT 'cliente',
            ativo TINYINT(1) NOT NULL DEFAULT 1,
            precisa_definir_acesso TINYINT(1) NOT NULL DEFAULT 0,
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_usuarios_perfil_ativo (perfil, ativo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS carteiras (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            usuario_id BIGINT UNSIGNED NOT NULL UNIQUE,
            saldo DECIMAL(12,2) NOT NULL DEFAULT 0,
            CONSTRAINT fk_carteiras_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS produtos (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(180) NOT NULL, descricao TEXT NULL,
            preco DECIMAL(12,2) NOT NULL, estoque INT NOT NULL DEFAULT 0,
            estoque_baixo INT NOT NULL DEFAULT 5,
            ativo TINYINT(1) NOT NULL DEFAULT 1,
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            preco_compra DECIMAL(12,2) NOT NULL DEFAULT 0,
            foto VARCHAR(255) NOT NULL DEFAULT '',
            KEY idx_produtos_ativos_nome (ativo, nome)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS compras (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            usuario_id BIGINT UNSIGNED NOT NULL, total DECIMAL(12,2) NOT NULL,
            pago DECIMAL(12,2) NOT NULL,
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            idempotency_key VARCHAR(100) NULL UNIQUE,
            KEY idx_compras_usuario_data (usuario_id, criado_em, id),
            CONSTRAINT fk_compras_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS itens_compra (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            compra_id BIGINT UNSIGNED NOT NULL, produto_id BIGINT UNSIGNED NOT NULL,
            produto_nome VARCHAR(180) NOT NULL, quantidade INT NOT NULL,
            preco_unitario DECIMAL(12,2) NOT NULL, custo_unitario DECIMAL(12,2) NULL,
            KEY idx_itens_compra_produto (produto_id), KEY idx_itens_compra_compra (compra_id),
            CONSTRAINT fk_itens_compra_compra FOREIGN KEY (compra_id) REFERENCES compras(id),
            CONSTRAINT fk_itens_compra_produto FOREIGN KEY (produto_id) REFERENCES produtos(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS movimentacoes (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            usuario_id BIGINT UNSIGNED NOT NULL, responsavel_id BIGINT UNSIGNED NULL,
            compra_id BIGINT UNSIGNED NULL, operacao VARCHAR(40) NOT NULL,
            valor DECIMAL(12,2) NOT NULL, descricao VARCHAR(255) NULL,
            idempotency_key VARCHAR(100) NULL UNIQUE,
            status VARCHAR(30) NOT NULL DEFAULT 'confirmada',
            movimentacao_origem_id BIGINT UNSIGNED NULL, motivo VARCHAR(500) NOT NULL DEFAULT '',
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_movimentacoes_usuario_data (usuario_id, criado_em, id),
            KEY idx_movimentacoes_data (criado_em, id),
            CONSTRAINT fk_mov_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
            CONSTRAINT fk_mov_responsavel FOREIGN KEY (responsavel_id) REFERENCES usuarios(id),
            CONSTRAINT fk_mov_compra FOREIGN KEY (compra_id) REFERENCES compras(id),
            CONSTRAINT fk_mov_origem FOREIGN KEY (movimentacao_origem_id) REFERENCES movimentacoes(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS notificacoes (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            usuario_id BIGINT UNSIGNED NOT NULL, mensagem TEXT NOT NULL,
            lida TINYINT(1) NOT NULL DEFAULT 0,
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_notificacoes_usuario_lida_data (usuario_id, lida, criado_em, id),
            CONSTRAINT fk_notificacoes_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS login_attempts (
            account_key VARCHAR(80) NOT NULL PRIMARY KEY,
            attempts INT NOT NULL DEFAULT 0,
            window_started_at DATETIME NOT NULL,
            KEY idx_login_attempts_window (window_started_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
        """CREATE TABLE IF NOT EXISTS logs_auditoria (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
            responsavel_id BIGINT UNSIGNED NULL, responsavel_nome VARCHAR(150) NOT NULL,
            responsavel_perfil VARCHAR(30) NOT NULL, acao VARCHAR(120) NOT NULL,
            alvo_id BIGINT UNSIGNED NULL, alvo_nome VARCHAR(150) NOT NULL,
            alvo_perfil VARCHAR(30) NOT NULL DEFAULT '', detalhes TEXT NOT NULL,
            criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            KEY idx_logs_auditoria_data (criado_em, id),
            KEY idx_logs_auditoria_alvo (alvo_id, criado_em)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    ]
    # Executa a criação de todas as tabelas na ordem das dependências.
    for statement in statements:
        cursor = connection.execute(statement)
        cursor.close()


    # Migração compatível com bancos já existentes: adiciona o limite individual
    # de estoque baixo sem alterar os valores atuais de estoque.
    column_check = connection.execute(
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'produtos' "
        "AND COLUMN_NAME = 'estoque_baixo'"
    ).fetchone()
    if not column_check:
        cursor = connection.execute(
            "ALTER TABLE produtos ADD COLUMN estoque_baixo INT NOT NULL DEFAULT 5"
        )
        cursor.close()

    # Índice único opcional: MySQL permite múltiplos NULL, como a regra do SQLite.
    connection.commit()
