import unittest
from datetime import datetime
from services.report_service import build_daily_chart


class ReportChartTests(unittest.TestCase):
    def test_combines_sales_and_topups_by_day(self):
        sales = [{"dia": "2026-11-01", "quantidade": 2, "valor": 20}]
        topups = [
            {"dia": "2026-11-01", "quantidade": 1, "valor": 10},
            {"dia": "2026-11-02", "quantidade": 1, "valor": 5},
        ]
        days, maximum = build_daily_chart(sales, topups, datetime)
        self.assertEqual(len(days), 2)
        self.assertEqual(days[0]["compras"], 20.0)
        self.assertEqual(days[0]["recargas"], 10.0)
        self.assertEqual(days[1]["recargas"], 5.0)
        self.assertEqual(maximum, 20.0)
        self.assertEqual(days[0]["rotulo"], "01/11")


if __name__ == "__main__":
    unittest.main()

class ReportDataTests(unittest.TestCase):
    def test_load_report_data_keeps_summary_movements_and_negative_wallets(self):
        from services.report_service import load_report_data
        calls = []

        def fake_query(sql, params=(), one=False):
            calls.append((sql, params, one))
            if "COUNT(*) AS quantidade" in sql and one:
                return {"quantidade": 3, "valor": 45}
            if "SUM(m.valor)" in sql and one:
                return {"valor": 20}
            if "DATE(c.criado_em)" in sql:
                return [{"dia": "2026-11-01", "quantidade": 2, "valor": 30}]
            if "DATE(m.criado_em)" in sql:
                return [{"dia": "2026-11-01", "quantidade": 1, "valor": 20}]
            if "JOIN usuarios u" in sql and "movimentacoes" in sql:
                return [{"id": 7, "cliente": "Cliente", "valor": 20}]
            if "c.saldo < 0" in sql:
                return [{"nome": "Cliente", "saldo": -12.5}]
            raise AssertionError(f"Consulta inesperada: {sql}")

        data = load_report_data(fake_query, "", [], "", [], "", [], datetime)
        self.assertEqual(data["resumo"], {
            "compras_quantidade": 3, "vendas_valor": 45.0, "recargas_valor": 20.0
        })
        self.assertEqual(data["total_saldo_negativo"], 12.5)
        self.assertEqual(data["movimentacoes"][0]["id"], 7)
        self.assertEqual(len(calls), 6)
