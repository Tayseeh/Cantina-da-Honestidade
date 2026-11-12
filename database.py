"""Camada de acesso ao MySQL 8 para o Confia+."""
from __future__ import annotations

import os
import re
from typing import Any, Iterable
import mysql.connector
from dotenv import load_dotenv
load_dotenv()
from mysql.connector import IntegrityError as DatabaseIntegrityError
from flask import current_app, g


class HybridRow(dict):
    """Linha que permite acesso por nome (row['id']) e por posição (row[0])."""
    def __getitem__(self, key):
        """Permite acessar os campos da linha pelo nome ou pela posição numérica."""
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class CursorAdapter:
    """Adapta o cursor do MySQL para a interface utilizada pelo restante da aplicação."""
    def __init__(self, cursor):
        """Inicializa o adaptador com o cursor ou conexão fornecido."""
        self._cursor = cursor
        self.lastrowid = cursor.lastrowid
        self.rowcount = cursor.rowcount

    def _row(self, row):
        """Converte uma linha retornada pelo cursor para o formato compatível do projeto."""
        return HybridRow(row) if isinstance(row, dict) else row

    def fetchone(self):
        """Obtém a próxima linha do resultado da consulta."""
        return self._row(self._cursor.fetchone())

    def fetchall(self):
        """Obtém todas as linhas restantes do resultado da consulta."""
        return [self._row(row) for row in self._cursor.fetchall()]

    def close(self):
        """Fecha o cursor ou a conexão e libera os recursos associados."""
        self._cursor.close()


class MySQLConnection:
    """Encapsula a conexão MySQL e oferece métodos compatíveis com o projeto."""
    def __init__(self, connection):
        """Inicializa o adaptador com o cursor ou conexão fornecido."""
        self.raw = connection

    def execute(self, sql: str, params: Iterable[Any] = ()):
        """Executa uma instrução de alteração e confirma a transação."""
        statement = sql.strip()
        if statement.upper() in ("BEGIN", "BEGIN IMMEDIATE", "START TRANSACTION"):
            if not self.raw.in_transaction:
                self.raw.start_transaction()
            return CursorAdapter(self.raw.cursor(dictionary=True))
        if statement.upper().startswith("PRAGMA"):
            # Mantido apenas para compatibilidade com verificações legadas.
            if "foreign_keys" in statement.lower():
                return CursorAdapter(self.raw.cursor(dictionary=True))
            raise RuntimeError("PRAGMA é exclusivo do SQLite; adapte a operação para MySQL.")
        statement = re.sub(r"\s+COLLATE\s+NOCASE\b", "", statement, flags=re.I)
        statement = statement.replace("?", "%s")
        cursor = self.raw.cursor(dictionary=True)
        cursor.execute(statement, tuple(params))
        return CursorAdapter(cursor)

    def executescript(self, script: str):
        # MySQL Connector executa uma instrução por cursor.
        """Executa a etapa interna de executescript, apoiando o fluxo da aplicação."""
        results = []
        for statement in script.split(";"):
            if statement.strip():
                results.append(self.execute(statement))
        return results

    def commit(self):
        """Executa a etapa interna de commit, apoiando o fluxo da aplicação."""
        self.raw.commit()

    def rollback(self):
        """Executa a etapa interna de rollback, apoiando o fluxo da aplicação."""
        self.raw.rollback()

    def close(self):
        """Fecha o cursor ou a conexão e libera os recursos associados."""
        self.raw.close()


def _mysql_config():
    """Monta as opções de conexão do MySQL a partir das variáveis de ambiente."""
    return {
        "host": os.getenv("CANTINA_DB_HOST", "localhost"),
        "port": int(os.getenv("CANTINA_DB_PORT", "3306")),
        "user": os.getenv("CANTINA_DB_USER", "root"),
        "password": os.getenv("CANTINA_DB_PASSWORD", ""),
        "database": os.getenv("CANTINA_DB_NAME", "cantina_honestidade"),
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": False,
        "connection_timeout": 10,
    }


def get_db() -> MySQLConnection:
    """Obtém ou cria a conexão MySQL vinculada à requisição Flask atual."""
    connection = g.get("db")
    if connection is None:
        raw = mysql.connector.connect(**_mysql_config())
        # Padroniza os timestamps gravados pelo MySQL em UTC. A interface
        # converte esses valores para America/Sao_Paulo ao exibi-los.
        timezone_cursor = raw.cursor()
        try:
            timezone_cursor.execute("SET time_zone = '+00:00'")
        finally:
            timezone_cursor.close()
        connection = MySQLConnection(raw)
        g.db = connection
        if not current_app.config.get("_DATABASE_LOGGED", False):
            current_app.logger.info(
                "CONFIA+ - conectado ao MySQL %s:%s/%s",
                os.getenv("CANTINA_DB_HOST", "localhost"),
                os.getenv("CANTINA_DB_PORT", "3306"),
                os.getenv("CANTINA_DB_NAME", "cantina_honestidade"),
            )
            current_app.config["_DATABASE_LOGGED"] = True
    return connection


def close_db(_error: BaseException | None = None) -> None:
    """Encerra a conexão vinculada à requisição, desfazendo transações pendentes."""
    connection = g.pop("db", None)
    if connection is not None:
        # Evita confirmar acidentalmente alterações pendentes ao encerrar requisição.
        try:
            connection.rollback()
        finally:
            connection.close()


def query(sql: str, params: Iterable[Any] = (), one: bool = False):
    """Executa uma consulta de leitura e retorna uma ou todas as linhas."""
    cursor = get_db().execute(sql, tuple(params))
    try:
        return cursor.fetchone() if one else cursor.fetchall()
    finally:
        cursor.close()


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    """Executa uma instrução de alteração e confirma a transação."""
    connection = get_db()
    cursor = connection.execute(sql, tuple(params))
    try:
        connection.commit()
        return int(cursor.lastrowid or 0)
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
