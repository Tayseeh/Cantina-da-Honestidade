"""Caso de uso financeiro para registro de recargas de carteira."""
from __future__ import annotations

from decimal import Decimal


class TopupAlreadyProcessedError(Exception):
    """A chave de idempotência da recarga já foi utilizada."""


class WalletNotFoundError(Exception):
    """A carteira associada à operação não foi encontrada."""


def register_topup(connection, customer, operator, value: Decimal, request_key: str, audit):
    """Credita a carteira e grava histórico, notificação e auditoria atomicamente."""
    try:
        connection.execute("START TRANSACTION")
        wallet = connection.execute(
            "UPDATE carteiras SET saldo = ROUND(saldo + ?, 2) WHERE usuario_id = ?",
            (str(value), customer["id"]),
        )
        if wallet.rowcount != 1:
            raise WalletNotFoundError("A carteira do cliente não foi encontrada.")

        connection.execute(
            "INSERT INTO movimentacoes (usuario_id, responsavel_id, operacao, valor, descricao, idempotency_key, status) "
            "VALUES (?, ?, 'recarga', ?, ?, ?, 'confirmada')",
            (customer["id"], operator["id"], str(value), "Recarga em dinheiro", request_key),
        )
        connection.execute(
            "INSERT INTO notificacoes (usuario_id, mensagem) VALUES (?, ?)",
            (customer["id"], f"Recarga de R$ {value:.2f} registrada por {operator['nome']}.")
        )
        audit("Recarga registrada", customer,
              f"Valor: R$ {value:.2f}; matrícula: {customer['matricula'] or '—'}", connection)
        connection.commit()
    except Exception:
        connection.rollback()
        raise

