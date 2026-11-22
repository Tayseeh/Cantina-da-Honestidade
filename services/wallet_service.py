"""Casos de uso relacionados à carteira e ao histórico financeiro."""
from __future__ import annotations

from decimal import Decimal

from database import execute, query


def wallet_balance(user_id: int) -> Decimal:
    # O saldo atual fica em carteiras; o histórico detalhado fica em movimentacoes.
    """Retorna o saldo de uma carteira; usuários sem carteira têm saldo zero."""
    row = query(
        "SELECT saldo FROM carteiras WHERE usuario_id = ?",
        (user_id,),
        one=True,
    )
    return Decimal(str(row["saldo"])) if row else Decimal("0.00")


# Centraliza a gravação do histórico financeiro para manter o padrão entre operações.
def record_movement(
    user_id: int,
    operation: str,
    value: Decimal | float | int,
    responsible_id: int | None = None,
    description: str = "",
    purchase_id: int | None = None,
) -> int:
    """Registra uma movimentação financeira e retorna seu identificador."""
    return execute(
        """INSERT INTO movimentacoes
           (usuario_id, responsavel_id, compra_id, operacao, valor, descricao)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, responsible_id, purchase_id, operation, float(value), description),
    )
