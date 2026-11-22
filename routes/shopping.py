"""Rotas de shopping do Confia+."""

import re

from services.checkout_service import (
    complete_purchase, UnavailableProductError, NegativeBalanceAcknowledgementRequired,
)

from core import (
    DatabaseIntegrityError,
    Decimal,
    _safe_internal_destination,
    abort,
    app,
    check_password_hash,
    current_user,
    db,
    flash,
    jsonify,
    query,
    redirect,
    render_template,
    request,
    role_required,
    session,
    url_for,
    uuid,
    wallet_balance,
)

def cart():
    """Retorna os dados do carrinho mantido na sessão."""
    return session.setdefault("cart", {})

def cart_items():
    """Carrega todos os produtos do carrinho em lote para evitar N+1 consultas."""
    cart_data = cart()
    if not cart_data:
        return [], Decimal("0")

    product_ids = list(cart_data.keys())
    placeholders = ",".join("?" for _ in product_ids)
    products = query(
        f"SELECT * FROM produtos WHERE id IN ({placeholders})",
        [int(product_id) for product_id in product_ids],
    )
    products_by_id = {str(product["id"]): product for product in products}
    items, total = [], Decimal("0")
    for product_id, quantity in cart_data.items():
        product = products_by_id.get(str(product_id))
        if product:
            subtotal = Decimal(str(product["preco"])) * quantity
            total += subtotal
            items.append({"produto": product, "quantidade": quantity, "subtotal": subtotal})
    return items, total

@app.route("/carrinho/adicionar/<int:product_id>", methods=["POST"])
@role_required("cliente")
def add_cart(product_id):
    """Adiciona um produto ao carrinho do cliente."""
    product = query("SELECT * FROM produtos WHERE id = ? AND ativo = 1", (product_id,), one=True)
    if not product:
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(error="Produto indisponível."), 404
        abort(404)
    current = cart()
    key = str(product_id)
    quantity_before = current.get(key, 0)
    if quantity_before >= product["estoque"]:
        message = f"Não foi possível adicionar {product['nome']}. Estoque máximo atingido."
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(error=message), 400
        flash(message, "warning")
        return redirect(_safe_internal_destination(request.form.get("next") or request.args.get("next")) or url_for("show_cart"))
    current[key] = quantity_before + 1
    session.modified = True
    items, total = cart_items()
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            ok=True, nome=product["nome"], quantidade_adicionada=1,
            quantidade_produto=current[key], itens=sum(item["quantidade"] for item in items),
            total=float(total), subtotal=float(Decimal(str(product["preco"])) * current[key]),
            produto_id=product_id,
        )
    flash(f"{product['nome']} adicionado ao carrinho.", "success")
    return redirect(_safe_internal_destination(request.form.get("next") or request.args.get("next")) or url_for("show_cart"))

@app.route("/qr/<int:product_id>", methods=["GET"])
def qr_add(product_id):
    # Abrir/ler um QR Code nunca altera o carrinho por GET. A pessoa confirma
    # explicitamente em um formulário POST protegido por CSRF.
    """Apresenta o fluxo de inclusão de produto por QR Code."""
    product = query("SELECT id, nome, preco, estoque FROM produtos WHERE id = ? AND ativo = 1", (product_id,), one=True)
    if not product:
        abort(404)
    user = current_user()
    if not user:
        return redirect(url_for("login", next=url_for("qr_add", product_id=product_id)))
    if user["perfil"] != "cliente":
        abort(403)
    return render_template("qr_confirm.html", produto=product, next_url=_safe_internal_destination(request.args.get("next")))

@app.route("/qr/<int:product_id>/adicionar", methods=["POST"])
@role_required("cliente")
def qr_add_to_cart(product_id):
    """Adiciona ao carrinho o produto identificado pelo QR Code."""
    return add_cart(product_id)

@app.route("/carrinho", methods=["GET", "POST"])
@role_required("cliente")
def show_cart():
    """Exibe o carrinho e processa a revisão dos itens."""
    current = cart()
    if request.method == "POST":
        for product_id in list(current):
            try:
                amount = int(request.form.get(f"q_{product_id}", 0) or 0)
            except (TypeError, ValueError):
                amount = 0
            product = query("SELECT estoque, ativo FROM produtos WHERE id = ?", (int(product_id),), one=True)
            if amount > 0 and product and product["ativo"] and amount <= product["estoque"]:
                current[product_id] = amount
            else:
                current.pop(product_id, None)
        session.modified = True
        return redirect(_safe_internal_destination(request.form.get("next") or request.args.get("next")) or url_for("show_cart"))
    items, total = cart_items()
    return render_template(
        "cart.html",
        itens=items,
        total=total,
        saldo_atual=wallet_balance(current_user()["id"]),
        saldo_negativo_ciencia_registrada=bool(query(
            "SELECT id FROM logs_auditoria WHERE alvo_id = ? AND acao = ? LIMIT 1",
            (current_user()["id"], "CIENCIA_SALDO_NEGATIVO"), one=True
        )),
        checkout_key=uuid.uuid4().hex,
    )

@app.route("/api/carrinho/<int:product_id>", methods=["POST"])
@role_required("cliente")
def update_cart_item(product_id):
    """Atualiza a quantidade de um item do carrinho."""
    product = query("SELECT * FROM produtos WHERE id = ? AND ativo = 1", (product_id,), one=True)
    if not product:
        return jsonify(error="Produto indisponível."), 404
    data = request.get_json(silent=True) or request.form
    try:
        quantity = int(data.get("quantidade", 0))
    except (TypeError, ValueError):
        return jsonify(error="Quantidade inválida."), 400
    if quantity < 0 or quantity > product["estoque"]:
        return jsonify(error=f"Disponibilidade máxima: {product['estoque']} unidade(s)."), 400
    current = cart()
    key = str(product_id)
    if quantity == 0:
        current.pop(key, None)
    else:
        current[key] = quantity
    session.modified = True
    items, total = cart_items()
    return jsonify(
        total=float(total),
        quantidade=quantity,
        itens=sum(item["quantidade"] for item in items),
        subtotal=float(Decimal(str(product["preco"])) * quantity),
    )

@app.route("/api/carrinho", methods=["DELETE"])
@role_required("cliente")
def clear_cart_api():
    """Remove todos os itens do carrinho pela API."""
    session["cart"] = {}
    session.modified = True
    return jsonify(itens=0, total=0)

@app.route("/carrinho/finalizar", methods=["POST"])
@role_required("cliente")
def checkout():
    """Valida o PIN e apresenta o resultado do caso de uso transacional."""
    user = current_user()
    current = cart()
    if not current:
        flash("Seu carrinho está vazio.", "warning")
        return redirect(url_for("show_cart"))

    submitted_pin = request.form.get("pin", "")
    if not re.fullmatch(r"[0-9]{4}", submitted_pin) or not user["pin_hash"] or not check_password_hash(user["pin_hash"], submitted_pin):
        message = "PIN incorreto. Confira os 4 números e tente novamente."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(error=message), 400
        items, total = cart_items()
        return render_template(
            "cart.html",
            itens=items,
            total=total,
            saldo_atual=wallet_balance(user["id"]),
            saldo_negativo_ciencia_registrada=bool(query(
                "SELECT id FROM logs_auditoria WHERE alvo_id = ? AND acao = ? LIMIT 1",
                (user["id"], "CIENCIA_SALDO_NEGATIVO"), one=True
            )),
            checkout_key=uuid.uuid4().hex,
            pin_error=message,
        ), 400

    checkout_key = request.form.get("idempotency_key", "").strip()
    if not checkout_key or len(checkout_key) > 80:
        flash("Não foi possível validar esta compra. Atualize o carrinho e tente novamente.", "danger")
        return redirect(url_for("show_cart"))

    try:
        purchase_id, paid_total, paid = complete_purchase(
            db(), user, current, checkout_key,
            acknowledge_negative_balance=request.form.get("acknowledge_negative_balance") == "1",
        )
    except NegativeBalanceAcknowledgementRequired:
        flash(
            "Sua compra deixará a carteira com saldo negativo. "
            "Leia o aviso e marque a confirmação de ciência antes de finalizar.",
            "warning",
        )
        return redirect(url_for("catalog"))
    except UnavailableProductError as error:
        flash(str(error), "danger")
        return redirect(url_for("show_cart"))
    except DatabaseIntegrityError:
        flash("Esta compra já foi processada. Confira seu histórico antes de tentar novamente.", "warning")
        return redirect(url_for("history"))

    new_balance = wallet_balance(user["id"])
    session["cart"] = {}
    session.modified = True
    session["purchase_confirmation"] = {
        "purchase_id": purchase_id,
        "paid": float(paid),
        "new_balance": float(new_balance),
    }
    history_url = url_for("history")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(redirect=history_url, purchase_id=purchase_id)
    return redirect(history_url)

@app.route("/historico")
@role_required("cliente")
def history():
    """Exibe ao cliente o histórico das próprias compras."""
    user = current_user()
    purchase_confirmation = session.pop("purchase_confirmation", None)
    purchases = query(
        """SELECT c.*, GROUP_CONCAT(CONCAT(i.produto_nome, ' x', i.quantidade) SEPARATOR ', ') AS itens
           FROM compras c LEFT JOIN itens_compra i ON i.compra_id = c.id
           WHERE c.usuario_id = ? GROUP BY c.id ORDER BY c.criado_em DESC""",
        (user["id"],),
    )
    total_spent = query(
        "SELECT COALESCE(SUM(pago), 0) AS total FROM compras WHERE usuario_id = ?",
        (user["id"],),
        one=True,
    )["total"]
    return render_template(
        "history.html",
        compras=purchases,
        total_gasto=total_spent,
        purchase_confirmation=purchase_confirmation,
    )
