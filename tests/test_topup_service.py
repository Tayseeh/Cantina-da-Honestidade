from decimal import Decimal

import pytest

from services.topup_service import (
    WalletNotFoundError,
    register_topup,
)


class Cursor:
    def __init__(self, rowcount=1, lastrowid=77, row=None):
        self.rowcount = rowcount
        self.lastrowid = lastrowid
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, results=None):
        self.results = list(results or [])
        self.calls = []
        self.committed = False
        self.rolled_back = False

    def execute(self, sql, params=()):
        normalized = " ".join(sql.split())
        self.calls.append((normalized, params))
        if normalized.upper() in ("START TRANSACTION", "BEGIN", "BEGIN IMMEDIATE"):
            return Cursor()
        return self.results.pop(0) if self.results else Cursor()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def audit(*args):
    return None


def test_register_topup_commits_wallet_history_and_notification():
    connection = FakeConnection([Cursor(rowcount=1), Cursor(), Cursor()])
    customer = {"id": 10, "matricula": "A10"}
    operator = {"id": 2, "nome": "Operador"}

    register_topup(connection, customer, operator, Decimal("25.50"), "key-1", audit)

    assert connection.committed is True
    assert connection.rolled_back is False
    sql = [call[0] for call in connection.calls]
    assert any("UPDATE carteiras" in statement for statement in sql)
    assert any("INSERT INTO movimentacoes" in statement for statement in sql)
    assert any("INSERT INTO notificacoes" in statement for statement in sql)


def test_register_topup_rolls_back_when_wallet_is_missing():
    connection = FakeConnection([Cursor(rowcount=0)])

    with pytest.raises(WalletNotFoundError):
        register_topup(connection, {"id": 10, "matricula": "A10"}, {"id": 2, "nome": "Op"}, Decimal("10"), "key", audit)

    assert connection.rolled_back is True
    assert connection.committed is False

