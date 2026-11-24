import unittest
from decimal import Decimal
from services.checkout_service import (complete_purchase, UnavailableProductError, NegativeBalanceAcknowledgementRequired)


class Result:
    def __init__(self, rows=None, lastrowid=None, rowcount=1):
        self.rows = rows or []
        self.lastrowid = lastrowid
        self.rowcount = rowcount

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


class FakeConnection:
    def __init__(self, products, wallet_balance=Decimal('100.00'), acknowledged=False):
        self.products = products
        self.wallet_balance = wallet_balance
        self.acknowledged = acknowledged
        self.statements = []
        self.committed = False
        self.rolled_back = False

    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        normalized = " ".join(sql.split()).upper()
        if normalized.startswith("SELECT ID, NOME, PRECO"):
            return Result(self.products)
        if normalized.startswith("SELECT SALDO FROM CARTEIRAS"):
            return Result([{"saldo": self.wallet_balance}])
        if normalized.startswith("SELECT ID FROM LOGS_AUDITORIA"):
            return Result([{"id": 1}] if self.acknowledged else [])
        if normalized.startswith("INSERT INTO COMPRAS"):
            return Result(lastrowid=42)
        return Result(rowcount=1)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class CheckoutServiceTests(unittest.TestCase):
    def setUp(self):
        self.products = [{
            "id": 7, "nome": "Suco", "preco": Decimal("5.50"),
            "preco_compra": Decimal("3.00"), "estoque": 4, "ativo": 1,
        }]

    def test_purchase_commits_all_financial_and_stock_changes(self):
        connection = FakeConnection(self.products)
        purchase_id, total, paid = complete_purchase(connection, {"id": 10, "nome": "Cliente", "perfil": "cliente"}, {"7": 2}, "key-123")
        self.assertEqual(purchase_id, 42)
        self.assertEqual(total, Decimal("11.00"))
        self.assertEqual(paid, Decimal("11.00"))
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        sql = " ".join(statement for statement, _ in connection.statements).upper()
        self.assertIn("UPDATE CARTEIRAS SET SALDO = SALDO -", sql)
        self.assertIn("INSERT INTO MOVIMENTACOES", sql)
        self.assertIn("FOR UPDATE", sql)

    def test_negative_wallet_balance_remains_allowed(self):
        connection = FakeConnection(self.products, wallet_balance=Decimal('0.00'))
        complete_purchase(connection, {"id": 10, "nome": "Cliente", "perfil": "cliente"}, {"7": 4}, "key-456", acknowledge_negative_balance=True)
        wallet_statement = next(sql for sql, _ in connection.statements if "UPDATE carteiras" in sql)
        self.assertNotIn("saldo >=", wallet_statement.lower())


    def test_crossing_from_zero_to_negative_requires_acknowledgement(self):
        connection = FakeConnection(self.products, wallet_balance=Decimal('0.00'))
        with self.assertRaises(NegativeBalanceAcknowledgementRequired):
            complete_purchase(
                connection, {"id": 10, "nome": "Cliente", "perfil": "cliente"},
                {"7": 4}, "key-no-ack",
            )
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)


    def test_acknowledged_negative_wallet_does_not_require_acknowledgement_again(self):
        connection = FakeConnection(
            self.products, wallet_balance=Decimal("-2.00"), acknowledged=True
        )
        complete_purchase(
            connection,
            {"id": 10, "nome": "Cliente", "perfil": "cliente"},
            {"7": 1},
            "key-negative-repeat",
        )
        audit_inserts = [
            sql for sql, _ in connection.statements
            if "insert into logs_auditoria" in sql.lower()
        ]
        self.assertEqual(audit_inserts, [])
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)


    def test_new_negative_crossing_after_recharge_requires_new_acknowledgement(self):
        # Mesmo havendo ciência registrada em uma negativação anterior, uma
        # carteira recarregada para saldo positivo exige nova ciência ao negativar.
        connection = FakeConnection(
            self.products, wallet_balance=Decimal("10.00"), acknowledged=True
        )
        with self.assertRaises(NegativeBalanceAcknowledgementRequired):
            complete_purchase(
                connection,
                {"id": 10, "nome": "Cliente", "perfil": "cliente"},
                {"7": 2},
                "key-new-negative-crossing",
            )
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)

    def test_new_negative_crossing_after_recharge_is_logged_again(self):
        connection = FakeConnection(
            self.products, wallet_balance=Decimal("10.00"), acknowledged=True
        )
        complete_purchase(
            connection,
            {"id": 10, "nome": "Cliente", "perfil": "cliente"},
            {"7": 2},
            "key-new-negative-crossing-ack",
            acknowledge_negative_balance=True,
        )
        audit_inserts = [
            sql for sql, _ in connection.statements
            if "insert into logs_auditoria" in sql.lower()
        ]
        self.assertEqual(len(audit_inserts), 1)
        self.assertTrue(connection.committed)

    def test_already_negative_wallet_does_not_require_repeated_acknowledgement(self):
        connection = FakeConnection(self.products, wallet_balance=Decimal("-2.00"))
        complete_purchase(
            connection,
            {"id": 10, "nome": "Cliente", "perfil": "cliente"},
            {"7": 1},
            "key-already-negative",
        )
        audit_inserts = [
            sql for sql, _ in connection.statements
            if "insert into logs_auditoria" in sql.lower()
        ]
        self.assertEqual(audit_inserts, [])
        self.assertTrue(connection.committed)

    def test_insufficient_stock_rolls_back(self):
        connection = FakeConnection(self.products)
        with self.assertRaises(UnavailableProductError):
            complete_purchase(connection, {"id": 10, "nome": "Cliente", "perfil": "cliente"}, {"7": 5}, "key-789")
        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)

    def test_missing_product_rolls_back(self):
        connection = FakeConnection([])
        with self.assertRaises(UnavailableProductError):
            complete_purchase(connection, {"id": 10, "nome": "Cliente", "perfil": "cliente"}, {"999": 1}, "key-999")
        self.assertTrue(connection.rolled_back)

    def test_invalid_quantity_is_rejected_before_transaction(self):
        connection = FakeConnection(self.products)
        with self.assertRaises(UnavailableProductError):
            complete_purchase(connection, {"id": 10, "nome": "Cliente", "perfil": "cliente"}, {"7": 0}, "key-invalid")
        self.assertFalse(connection.committed)
        self.assertFalse(connection.rolled_back)
        self.assertEqual(connection.statements, [])


if __name__ == "__main__":
    unittest.main()
