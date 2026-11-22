"""Caso de uso transacional para finalizar uma compra no Confia+."""
from decimal import Decimal


class UnavailableProductError(Exception):
    """Produto indisponível ou estoque insuficiente."""


class NegativeBalanceAcknowledgementRequired(Exception):
    """A compra deixará a carteira negativa e exige ciência prévia do cliente."""


def complete_purchase(connection, user, cart_items, idempotency_key, acknowledge_negative_balance=False):
    """Confirma compra, estoque, carteira, idempotência e ciência em uma transação."""
    items = []
    total = Decimal("0.00")
    product_ids = sorted(int(product_id) for product_id in cart_items)
    if not product_ids:
        raise UnavailableProductError("Seu carrinho está vazio.")
    if not idempotency_key or len(idempotency_key) > 80:
        raise ValueError("Chave de idempotência inválida.")

    for quantity in cart_items.values():
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise UnavailableProductError("Uma das quantidades do carrinho é inválida. Revise seu carrinho.")

    try:
        connection.execute("START TRANSACTION")
        placeholders = ",".join("?" for _ in product_ids)
        products = connection.execute(
            "SELECT id, nome, preco, preco_compra, estoque, ativo FROM produtos "
            f"WHERE id IN ({placeholders}) ORDER BY id FOR UPDATE",
            product_ids,
        ).fetchall()
        products_by_id = {product["id"]: product for product in products}

        for product_id, quantity in cart_items.items():
            product = products_by_id.get(int(product_id))
            if not product or not product["ativo"]:
                raise UnavailableProductError(
                    "Um dos produtos do carrinho não está mais disponível. Revise seu carrinho."
                )
            if quantity > product["estoque"]:
                raise UnavailableProductError(
                    f"Estoque insuficiente para {product['nome']}. "
                    f"Disponíveis: {product['estoque']} unidade(s); "
                    f"solicitadas: {quantity}. Revise seu carrinho."
                )
            total += Decimal(str(product["preco"])) * quantity
            items.append((product, quantity))

        # A linha da carteira é bloqueada para evitar duas compras concorrentes
        # calcularem o saldo a partir do mesmo valor.
        wallet = connection.execute(
            "SELECT saldo FROM carteiras WHERE usuario_id = ? FOR UPDATE", (user["id"],)
        ).fetchone()
        balance = Decimal(str(wallet["saldo"])) if wallet else Decimal("0.00")
        projected_balance = balance - total
        acknowledged = connection.execute(
            "SELECT id FROM logs_auditoria WHERE alvo_id = ? AND acao = ? LIMIT 1",
            (user["id"], "CIENCIA_SALDO_NEGATIVO"),
        ).fetchone()

        # Exigir ciência na primeira compra que negativará a carteira e em toda
        # compra feita enquanto o saldo atual já estiver negativo.
        requires_negative_acknowledgement = projected_balance < 0 and (
            balance < 0 or not acknowledged
        )
        if requires_negative_acknowledgement and not acknowledge_negative_balance:
            raise NegativeBalanceAcknowledgementRequired()

        # Registrar a ciência apenas uma vez para auditoria, sem duplicar o log
        # nas compras seguintes enquanto a carteira continuar negativa.
        if projected_balance < 0 and not acknowledged and acknowledge_negative_balance:
            connection.execute(
                "INSERT INTO logs_auditoria "
                "(responsavel_id, responsavel_nome, responsavel_perfil, acao, alvo_id, alvo_nome, alvo_perfil, detalhes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user["id"], user["nome"], user["perfil"], "CIENCIA_SALDO_NEGATIVO",
                 user["id"], user["nome"], user["perfil"],
                 "Cliente confirmou ciência de que a compra deixaria a carteira com saldo negativo."),
            )

        cursor = connection.execute(
            "INSERT INTO compras (usuario_id, total, pago, idempotency_key) VALUES (?, ?, ?, ?)",
            (user["id"], float(total), float(total), idempotency_key),
        )
        purchase_id = cursor.lastrowid

        for product, quantity in items:
            updated = connection.execute(
                "UPDATE produtos SET estoque = estoque - ? "
                "WHERE id = ? AND ativo = 1 AND estoque >= ?",
                (quantity, product["id"], quantity),
            )
            if updated.rowcount != 1:
                raise RuntimeError("Estoque alterado durante a compra; transação cancelada.")
            cost = product["preco_compra"] if product["preco_compra"] and product["preco_compra"] > 0 else None
            connection.execute(
                "INSERT INTO itens_compra "
                "(compra_id, produto_id, produto_nome, quantidade, preco_unitario, custo_unitario) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (purchase_id, product["id"], product["nome"], quantity, product["preco"], cost),
            )

        connection.execute(
            "UPDATE carteiras SET saldo = saldo - ? WHERE usuario_id = ?",
            (float(total), user["id"]),
        )
        connection.execute(
            "INSERT INTO movimentacoes "
            "(usuario_id, compra_id, operacao, valor, descricao, idempotency_key, status) "
            "VALUES (?, ?, 'compra', ?, ?, ?, 'confirmada')",
            (user["id"], purchase_id, float(total), f"Compra #{purchase_id}", idempotency_key),
        )
        connection.commit()
        return purchase_id, total, total
    except Exception:
        connection.rollback()
        raise
