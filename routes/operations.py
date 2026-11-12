"""Rotas de operations do Confia+."""

from core import (
    BASE_DIR,
    DatabaseIntegrityError,
    Decimal,
    app,
    current_user,
    db,
    execute,
    flash,
    money,
    os,
    process_profile_photo,
    query,
    re,
    redirect,
    registrar_auditoria,
    render_template,
    request,
    role_required,
    store_product_photo,
    url_for,
    uuid,
)

@app.route("/produtos", methods=["GET", "POST"])
@role_required("operador")
def products():
    """Lista produtos e processa o cadastro de novos produtos."""
    if request.method == "POST":
        image_disk_path = None
        try:
            name = request.form.get("nome", "").strip()
            description = request.form.get("descricao", "").strip()
            raw_purchase = request.form.get("preco_compra", "").strip()
            raw_sale = request.form.get("preco_venda", "").strip()
            raw_stock = request.form.get("estoque", "").strip()
            raw_low_stock = request.form.get("estoque_baixo", "5").strip()
            if (not re.fullmatch(r"[^\W_](?:[^\W_]|[\s.,'’()/&+-]){0,79}", name, re.UNICODE)
                    or not re.fullmatch(r"(?:[^\W_]|[\s.,;:!?()'’\"/_&+%#@-]){0,250}", description, re.UNICODE)
                    or not re.fullmatch(r"\d{1,9}(?:[,.]\d{1,2})?", raw_purchase)
                    or not re.fullmatch(r"\d{1,9}(?:[,.]\d{1,2})?", raw_sale)
                    or not re.fullmatch(r"\d{1,6}", raw_stock)
                    or not re.fullmatch(r"\d{1,6}", raw_low_stock)
                    or int(raw_low_stock) < 1):
                raise ValueError
            purchase_price = money(raw_purchase)
            sale_price = money(raw_sale)
            stock = int(raw_stock)
            low_stock = int(raw_low_stock)
            photo_bytes = process_profile_photo(request.files.get("foto"))
            photo_path, image_disk_path = store_product_photo(photo_bytes)
            product_id = execute("INSERT INTO produtos (nome, descricao, preco_compra, preco, estoque, estoque_baixo, foto) VALUES (?, ?, ?, ?, ?, ?, ?)", (name, description, float(purchase_price), float(sale_price), stock, low_stock, photo_path))
            registrar_auditoria("Produto cadastrado", {"id": product_id, "nome": name, "perfil": "produto"}, f"Custo: R$ {purchase_price:.2f}; venda: R$ {sale_price:.2f}; estoque inicial: {stock}")
            flash("Produto cadastrado.", "success")
        except (ValueError, KeyError, OSError) as error:
            if image_disk_path and os.path.isfile(image_disk_path):
                os.remove(image_disk_path)
            flash(str(error) if isinstance(error, ValueError) and str(error) else "Confira os dados do produto e tente novamente.", "danger")
        return redirect(url_for("products"))
    return render_template("products.html", produtos=query("SELECT * FROM produtos ORDER BY ativo DESC, nome"))

@app.route("/produtos/<int:product_id>", methods=["POST"])
@role_required("operador")
def edit_product(product_id):
    """Atualiza os dados ou o estado de um produto existente."""
    image_disk_path = None
    product = query("SELECT * FROM produtos WHERE id = ?", (product_id,), one=True)
    if not product:
        flash("Produto não encontrado.", "warning")
        return redirect(url_for("products"))
    action = request.form.get("action")
    if action in ("deactivate_product", "activate_product"):
        new_status = 0 if action == "deactivate_product" else 1
        execute("UPDATE produtos SET ativo = ? WHERE id = ?", (new_status, product_id))
        registrar_auditoria("Produto desativado" if new_status == 0 else "Produto ativado", {"id": product_id, "nome": product["nome"], "perfil": "produto"}, f"Status alterado para {'inativo' if new_status == 0 else 'ativo'}.")
        flash("Produto desativado." if new_status == 0 else "Produto ativado.", "success")
        return redirect(url_for("products"))
    try:
        name = request.form.get("nome", "").strip()
        description = request.form.get("descricao", "").strip()
        raw_purchase = request.form.get("preco_compra", "").strip()
        raw_sale = request.form.get("preco_venda", "").strip()
        raw_stock = request.form.get("estoque", "").strip()
        raw_low_stock = request.form.get("estoque_baixo", "5").strip()
        if (not re.fullmatch(r"[^\W_](?:[^\W_]|[\s.,'’()/&+-]){0,79}", name, re.UNICODE)
                or not re.fullmatch(r"(?:[^\W_]|[\s.,;:!?()'’\"/_&+%#@-]){0,250}", description, re.UNICODE)
                or not re.fullmatch(r"\d{1,9}(?:[,.]\d{1,2})?", raw_purchase)
                or not re.fullmatch(r"\d{1,9}(?:[,.]\d{1,2})?", raw_sale)
                or not re.fullmatch(r"\d{1,6}", raw_stock)
                or not re.fullmatch(r"\d{1,6}", raw_low_stock)
                or int(raw_low_stock) < 1):
            raise ValueError
        purchase_price = money(raw_purchase)
        sale_price = money(raw_sale)
        stock = int(raw_stock)
        low_stock = int(raw_low_stock)
        photo_bytes = process_profile_photo(request.files.get("foto"))
        photo_path = product["foto"] or ""
        if photo_bytes is not None:
            photo_path, image_disk_path = store_product_photo(photo_bytes)
        elif request.form.get("remover_foto"):
            photo_path = ""
        execute("UPDATE produtos SET nome=?, descricao=?, preco_compra=?, preco=?, estoque=?, estoque_baixo=?, foto=? WHERE id=?", (name, description, float(purchase_price), float(sale_price), stock, low_stock, photo_path, product_id))
        registrar_auditoria("Produto editado", {"id": product_id, "nome": name, "perfil": "produto"}, f"Preço de compra: R$ {float(product['preco_compra'] or 0):.2f} → R$ {purchase_price:.2f}; preço de venda: R$ {float(product['preco'] or 0):.2f} → R$ {sale_price:.2f}; estoque: {product['estoque']} → {stock}; limite de estoque baixo: {product.get('estoque_baixo', 5)} → {low_stock}")
        if product["foto"] and photo_path != product["foto"] and product["foto"].startswith("uploads/produtos/"):
            old_image_path = os.path.join(BASE_DIR, "static", "uploads", "produtos", os.path.basename(product["foto"]))
            if os.path.isfile(old_image_path):
                try:
                    os.remove(old_image_path)
                except OSError:
                    pass
        flash("Produto atualizado.", "success")
    except (ValueError, KeyError, OSError) as error:
        if image_disk_path and os.path.isfile(image_disk_path):
            os.remove(image_disk_path)
        flash(str(error) if isinstance(error, ValueError) and str(error) else "Confira os dados do produto e tente novamente.", "danger")
    return redirect(url_for("products"))

@app.route("/recargas", methods=["GET", "POST"])
@role_required("operador")
def topups():
    """Registra recargas de carteira após o recebimento do valor."""
    if request.method == "POST":
        request_key = request.form.get("idempotency_key", "").strip()
        customer = query("SELECT * FROM usuarios WHERE matricula = ? AND ativo = 1", (request.form.get("matricula", "").strip(),), one=True)
        try:
            value = money(request.form.get("valor", ""))
        except ValueError:
            value = Decimal("0.00")
        if not request_key or len(request_key) > 80:
            flash("Não foi possível validar esta recarga. Atualize a página e tente novamente.", "danger")
        elif not customer or customer["perfil"] != "cliente" or value <= 0:
            flash("Informe uma matrícula de cliente e um valor válido.", "danger")
        elif request.form.get("confirmacao_recebimento") != "sim":
            flash("Confirme que o dinheiro foi recebido fisicamente antes de liberar o crédito.", "warning")
        else:
            operator = current_user()
            connection = db()
            try:
                # Um único commit persiste saldo, histórico e notificação juntos.
                # BEGIN IMMEDIATE serializa recargas concorrentes no SQLite.
                connection.execute("BEGIN IMMEDIATE")
                cursor = connection.execute(
                    "UPDATE carteiras SET saldo = ROUND(saldo + ?, 2) WHERE usuario_id = ?",
                    (str(value), customer["id"]),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError("A carteira do cliente não foi encontrada.")
                connection.execute(
                    "INSERT INTO movimentacoes (usuario_id, responsavel_id, operacao, valor, descricao, idempotency_key, status) VALUES (?, ?, 'recarga', ?, ?, ?, 'confirmada')",
                    (customer["id"], operator["id"], str(value), "Recarga em dinheiro", request_key),
                )
                connection.execute(
                    "INSERT INTO notificacoes (usuario_id, mensagem) VALUES (?, ?)",
                    (customer["id"], f"Recarga de R$ {value:.2f} registrada por {operator['nome']}.")
                )
                registrar_auditoria("Recarga registrada", customer, f"Valor: R$ {value:.2f}; matrícula: {customer['matricula'] or '—'}", connection)
                connection.commit()
                flash("Recarga registrada e cliente notificado.", "success")
            except DatabaseIntegrityError:
                connection.rollback()
                # Reenvio do mesmo formulário: não credita novamente.
                flash("Esta recarga já foi processada. Confira o saldo antes de tentar novamente.", "warning")
            except Exception:
                connection.rollback()
                app.logger.exception("Falha ao registrar recarga; transação revertida.")
                flash("Não foi possível registrar a recarga. Nenhuma alteração foi salva; tente novamente.", "danger")
        return redirect(url_for("topups"))
    customers = query("SELECT nome, email, matricula FROM usuarios WHERE perfil = 'cliente' AND ativo = 1 ORDER BY nome")
    recent_topups = query(
        "SELECT m.id, m.usuario_id, m.valor, m.descricao, m.criado_em, u.nome AS cliente, u.matricula "
        "FROM movimentacoes m JOIN usuarios u ON u.id=m.usuario_id "
        "WHERE m.operacao='recarga' ORDER BY m.criado_em DESC, m.id DESC LIMIT 30"
    )
    return render_template("topups.html", clientes=customers, recarga_idempotency_key=uuid.uuid4().hex, recargas=recent_topups)
