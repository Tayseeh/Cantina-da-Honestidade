"""Rotas de admin do Confia+."""

from core import (
    TEMP_PASSWORD_NOTICES,
    TEMP_PASSWORD_NOTICES_LOCK,
    _normalize_username,
    app,
    current_user,
    datetime,
    db,
    execute,
    flash,
    generate_password_hash,
    query,
    re,
    redirect,
    registrar_auditoria,
    render_template,
    request,
    role_required,
    secrets,
    string,
    url_for,
)

@app.route("/admin/usuarios", methods=["GET", "POST"])
@app.route("/operador/clientes", methods=["GET", "POST"])
@role_required("admin", "operador")
def users():
    """Lista e gerencia contas conforme as permissões de administrador ou operador."""
    is_operator = current_user()["perfil"] == "operador"
    redirect_endpoint = "/operador/clientes" if is_operator else "/admin/usuarios"
    if request.method == "POST":
        action = request.form.get("action")
        if is_operator and action not in ("deactivate_user", "activate_user", "edit_user", "reset_password"):
            flash("Você não tem permissão para executar esta ação.", "danger")
            return redirect(redirect_endpoint)
        if action in ("deactivate_user", "activate_user"):
            user_id = int(request.form.get("id", "0"))
            target = query("SELECT id, perfil, ativo FROM usuarios WHERE id = ?", (user_id,), one=True)
            if not target:
                flash("Usuário não encontrado.", "warning")
            elif not is_operator and target["perfil"] == "cliente":
                flash("Administradores gerenciam apenas contas de administradores e operadores.", "danger")
            elif is_operator and target["perfil"] != "cliente":
                flash("Operadores só podem gerenciar contas de clientes.", "danger")
            elif action == "deactivate_user" and user_id == current_user()["id"]:
                flash("Não é possível desativar a própria conta enquanto estiver conectado.", "warning")
            elif action == "deactivate_user" and target["perfil"] == "admin" and target["ativo"] and query("SELECT COUNT(*) AS total FROM usuarios WHERE perfil = 'admin' AND ativo = 1", one=True)["total"] <= 1:
                flash("Mantenha pelo menos uma conta de administrador ativa no sistema.", "warning")
            else:
                new_status = 0 if action == "deactivate_user" else 1
                execute("UPDATE usuarios SET ativo = ? WHERE id = ?", (new_status, user_id))
                target_for_log = query("SELECT id, nome, perfil FROM usuarios WHERE id = ?", (user_id,), one=True)
                registrar_auditoria("Conta desativada" if new_status == 0 else "Conta reativada", target_for_log, f"Status alterado para {'inativa' if new_status == 0 else 'ativa'}")
                flash("Conta desativada. O histórico foi preservado." if new_status == 0 else "Conta ativada.", "success")
            return redirect(redirect_endpoint)

        if action == "reset_password":
            user_id = int(request.form.get("id", "0"))
            target = query("SELECT id, nome, username, perfil FROM usuarios WHERE id = ?", (user_id,), one=True)
            if not target:
                flash("Usuário não encontrado.", "warning")
            elif not is_operator and target["perfil"] == "cliente":
                flash("Administradores gerenciam apenas contas de administradores e operadores.", "danger")
            elif is_operator and target["perfil"] != "cliente":
                flash("Operadores só podem redefinir senhas de clientes.", "danger")
            elif user_id == current_user()["id"]:
                flash("Por segurança, não é possível redefinir a própria senha por esta tela.", "warning")
            else:
                alphabet = string.ascii_letters + string.digits
                temporary_password = secrets.choice(string.ascii_letters) + secrets.choice(string.digits) + "".join(secrets.choice(alphabet) for _ in range(8))
                execute("UPDATE usuarios SET senha_hash = ?, precisa_definir_acesso = 1 WHERE id = ?", (generate_password_hash(temporary_password), user_id))
                registrar_auditoria("Senha temporária redefinida", target, "A senha anterior foi invalidada; nenhuma senha foi armazenada no log.")
                with TEMP_PASSWORD_NOTICES_LOCK:
                    TEMP_PASSWORD_NOTICES[current_user()["id"]] = {"nome": target["nome"], "username": target["username"] or "—", "senha": temporary_password, "perfil": target["perfil"], "tipo": "redefinicao"}
                flash("Nova senha temporária gerada. A senha anterior foi invalidada.", "success")
            return redirect(redirect_endpoint)

        if action == "edit_user":
            user_id = int(request.form.get("id", "0"))
            target = query("SELECT * FROM usuarios WHERE id = ?", (user_id,), one=True)
            if not target:
                flash("Usuário não encontrado.", "warning")
                return redirect(redirect_endpoint)
            if not is_operator and target["perfil"] == "cliente":
                flash("Administradores gerenciam apenas contas de administradores e operadores.", "danger")
                return redirect(redirect_endpoint)
            if is_operator and target["perfil"] != "cliente":
                flash("Operadores só podem editar contas de clientes.", "danger")
                return redirect(redirect_endpoint)
            profile = target["perfil"]
            first = request.form.get("nome", "").strip()
            surname = request.form.get("sobrenome", "").strip()
            email = request.form.get("email", "").strip().lower()
            username = _normalize_username(request.form.get("username", ""))
            requested_profile = request.form.get("perfil", profile)
            cpf_raw = request.form.get("cpf", "").strip()
            phone_raw = request.form.get("telefone", "").strip()
            birth_raw = request.form.get("data_nascimento", "").strip()
            enrollment_raw = request.form.get("matricula", "").strip()
            errors = []
            name_pattern = r"[^\W\d_]+(?:[ '-][^\W\d_]+)*"
            if not first or len(first) > 30 or not re.fullmatch(name_pattern, first, flags=re.UNICODE) or not surname or len(surname) > 30 or not re.fullmatch(name_pattern, surname, flags=re.UNICODE):
                errors.append("Informe nome e sobrenome válidos, com até 30 caracteres cada.")
            email_pattern = r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+"
            if len(email) > 50 or (email and not re.fullmatch(email_pattern, email, flags=re.IGNORECASE)):
                errors.append("Informe um e-mail válido com até 50 caracteres.")
            if not 3 <= len(username) <= 30 or not re.fullmatch(r"[a-z0-9]+(?:\.[a-z0-9]+)*", username):
                errors.append("O nome de usuário deve ter de 3 a 30 caracteres, usando letras sem acento, números e pontos entre palavras.")
            elif query("SELECT id FROM usuarios WHERE lower(username) = lower(?) AND id != ?", (username, user_id), one=True):
                errors.append("Esse nome de usuário já está em uso. Escolha outro.")
            if profile in ("operador", "admin"):
                if requested_profile not in ("operador", "admin"):
                    errors.append("O perfil de operadores e administradores só pode ser Operador ou Administrador.")
                elif requested_profile != profile and user_id == current_user()["id"]:
                    errors.append("Não é permitido alterar o próprio perfil administrativo.")
            else:
                # O perfil de cliente é imutável nesta tela, mesmo que uma requisição manual envie outro perfil.
                requested_profile = profile
            if profile == "cliente":
                digits = "".join(character for character in enrollment_raw if character.isdigit())
                if not digits or len(digits) > 14:
                    errors.append("Matrícula: informe de 1 a 14 números.")
                else:
                    enrollment_raw = digits
            else:
                enrollment_raw = None
            cpf_digits = "".join(character for character in cpf_raw if character.isdigit()) or None
            if cpf_raw and (not re.fullmatch(r"\d{11}", cpf_digits or "") or not re.fullmatch(r"(?:\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})", cpf_raw)):
                errors.append("CPF: informe 11 números no formato 000.000.000-00.")
            ddds = {"11", "12", "13", "14", "15", "16", "17", "18", "19", "21", "22", "24", "27", "28", "31", "32", "33", "34", "35", "37", "38", "41", "42", "43", "44", "45", "46", "47", "48", "49", "51", "53", "54", "55", "61", "62", "63", "64", "65", "66", "67", "68", "69", "71", "73", "74", "75", "77", "79", "81", "82", "83", "84", "85", "86", "87", "88", "89", "91", "92", "93", "94", "95", "96", "97", "98", "99"}
            phone_digits = "".join(character for character in phone_raw if character.isdigit())
            if phone_digits.startswith("55") and len(phone_digits) in (12, 13):
                phone_digits = phone_digits[2:]
            valid_phone = not phone_raw or (re.fullmatch(r"[\d\s()+.-]+", phone_raw) and len(phone_digits) in (10, 11) and phone_digits[:2] in ddds)
            if phone_raw and valid_phone:
                subscriber = phone_digits[2:]
                valid_phone = (len(subscriber) == 9 and subscriber.startswith("9")) or (len(subscriber) == 8 and subscriber[0] in "2345")
            if not valid_phone:
                errors.append("Telefone: informe um número brasileiro válido com DDD.")
            birth_storage = ""
            if birth_raw:
                try:
                    birth_date = datetime.strptime(birth_raw, "%Y-%m-%d").date() if re.fullmatch(r"\d{4}-\d{2}-\d{2}", birth_raw) else datetime.strptime(birth_raw, "%d/%m/%Y").date()
                    today = datetime.today().date()
                    try:
                        earliest = today.replace(year=today.year - 120)
                    except ValueError:
                        earliest = today.replace(year=today.year - 120, day=28)
                    if not earliest <= birth_date <= today:
                        raise ValueError
                    birth_storage = birth_date.isoformat()
                except ValueError:
                    errors.append("Data de nascimento: digite uma data válida.")
            if not errors:
                for column, value, label in (("email", email, "E-mail"), ("cpf", cpf_digits, "CPF"), ("matricula", enrollment_raw, "Matrícula")):
                    lookup = "lower(email) = lower(?)" if column == "email" else f"{column} = ?"
                    if value and query(f"SELECT id FROM usuarios WHERE {lookup} AND id != ?", (value, user_id), one=True):
                        errors.append(f"{label}: já está cadastrado em outra conta.")
            if errors:
                for error in errors:
                    flash(error, "danger")
            else:
                changed_labels = []
                comparisons = (
                    ("nome", target["nome"], f"{first} {surname}".strip(), "nome"),
                    ("email", target["email"], email, "e-mail"),
                    ("username", target["username"], username, "nome de usuário"),
                    ("perfil", target["perfil"], requested_profile, "perfil de acesso"),
                    ("matricula", target["matricula"], enrollment_raw, "matrícula"),
                    ("cpf", target["cpf"], cpf_digits, "CPF"),
                    ("telefone", target["telefone"], phone_digits, "telefone"),
                    ("data_nascimento", target["data_nascimento"], birth_storage, "data de nascimento"),
                )
                changed_labels = [label for _field, old_value, new_value, label in comparisons if (old_value or "") != (new_value or "")]
                execute("UPDATE usuarios SET nome=?, sobrenome=?, email=?, username=?, perfil=?, matricula=?, cpf=?, telefone=?, data_nascimento=?, pin_hash=CASE WHEN ?='cliente' THEN pin_hash ELSE NULL END WHERE id=?", (f"{first} {surname}".strip(), surname, email, username, requested_profile, enrollment_raw, cpf_digits, phone_digits, birth_storage, requested_profile, user_id))
                target_for_log = query("SELECT id, nome, perfil FROM usuarios WHERE id = ?", (user_id,), one=True)
                if changed_labels:
                    detail = "Campos alterados: " + ", ".join(changed_labels)
                    if target["perfil"] != requested_profile:
                        detail += f"; perfil: {target['perfil']} → {requested_profile}"
                    registrar_auditoria("Conta editada", target_for_log, detail)
                flash("Dados do usuário atualizados.", "success")
            return redirect(redirect_endpoint)

        if request.form.get("action") == "create_staff":
            first = request.form.get("nome", "").strip()
            surname = request.form.get("sobrenome", "").strip()
            email = request.form.get("email", "").strip().lower()
            username = _normalize_username(request.form.get("username", ""))
            profile = request.form.get("novo_perfil", "")
            email_pattern = r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+"
            errors = []
            if profile not in ("operador", "admin"):
                errors.append("Escolha o perfil de operador ou administrador.")
            if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ '-]{0,29}", first):
                errors.append("Informe um nome válido com até 30 caracteres.")
            if not re.fullmatch(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ '-]{0,29}", surname):
                errors.append("Informe um sobrenome válido com até 30 caracteres.")
            if not 3 <= len(username) <= 30 or not re.fullmatch(r"[a-z0-9]+(?:\.[a-z0-9]+)*", username):
                errors.append("O usuário deve ter de 3 a 30 caracteres, usando letras sem acento, números e pontos entre palavras.")
            elif query("SELECT id FROM usuarios WHERE lower(username) = lower(?)", (username,), one=True):
                errors.append("Esse nome de usuário já está em uso. Escolha outro.")
            if len(email) > 50 or (email and not re.fullmatch(email_pattern, email, flags=re.IGNORECASE)):
                errors.append("Informe um e-mail válido com até 50 caracteres.")
            if query("SELECT id FROM usuarios WHERE lower(email) = lower(?)", (email,), one=True):
                errors.append("Este e-mail já está cadastrado.")
            if errors:
                for error in errors:
                    flash(error, "danger")
            else:
                alphabet = string.ascii_letters + string.digits
                temporary_password = secrets.choice(string.ascii_letters) + secrets.choice(string.digits) + "".join(secrets.choice(alphabet) for _ in range(8))
                connection = db()
                try:
                    connection.execute("BEGIN IMMEDIATE")
                    cursor = connection.execute(
                        "INSERT INTO usuarios (nome, sobrenome, matricula, email, username, senha_hash, perfil, precisa_definir_acesso) VALUES (?, ?, NULL, ?, ?, ?, ?, 1)",
                        (f"{first} {surname}", surname, email, username, generate_password_hash(temporary_password), profile),
                    )
                    user_id = cursor.lastrowid
                    connection.execute("INSERT INTO carteiras (usuario_id, saldo) VALUES (?, 0)", (user_id,))
                    created_target = connection.execute("SELECT id, nome, perfil FROM usuarios WHERE id = ?", (user_id,)).fetchone()
                    registrar_auditoria("Conta criada", created_target, f"Conta criada com perfil {profile}.", connection)
                    connection.commit()
                except Exception:
                    connection.rollback()
                    app.logger.exception("Falha ao criar usuário administrativo/operador.")
                    flash("Não foi possível criar a conta. Nenhuma alteração foi salva.", "danger")
                    return redirect(url_for("users", novo="1"))
                # Exibe a senha temporária uma única vez após o redirecionamento.
                with TEMP_PASSWORD_NOTICES_LOCK:
                    TEMP_PASSWORD_NOTICES[current_user()["id"]] = {"nome": f"{first} {surname}", "username": username, "senha": temporary_password, "perfil": profile}
                flash("Conta criada. A senha exibida abaixo é temporária e deverá ser alterada no primeiro acesso.", "success")
            return redirect(url_for("users", novo="1" if errors else None))

        flash("Ação não reconhecida. Nenhuma alteração foi realizada.", "warning")
        return redirect(redirect_endpoint)
    today = datetime.today().date()
    try:
        earliest_birth_date = today.replace(year=today.year - 120)
    except ValueError:
        earliest_birth_date = today.replace(year=today.year - 120, day=28)
    with TEMP_PASSWORD_NOTICES_LOCK:
        notice = TEMP_PASSWORD_NOTICES.pop(current_user()["id"], None)
    nova_conta_temporaria = notice if notice and notice.get("tipo") != "redefinicao" else None
    senha_redefinida = notice if notice and notice.get("tipo") == "redefinicao" else None
    if is_operator:
        usuarios = query("SELECT u.*, COALESCE(c.saldo, 0) AS saldo FROM usuarios u LEFT JOIN carteiras c ON c.usuario_id = u.id WHERE u.perfil = 'cliente' ORDER BY u.nome")
        return render_template("customers.html", usuarios=usuarios, hoje=today.isoformat(), nascimento_minimo=earliest_birth_date.isoformat(), nova_conta_temporaria=nova_conta_temporaria, senha_redefinida=senha_redefinida, is_operator=True)
    else:
        # O painel administrativo gerencia somente contas da equipe, nunca clientes.
        usuarios = query("SELECT * FROM usuarios WHERE perfil IN ('admin', 'operador') ORDER BY nome")
    return render_template("users.html", usuarios=usuarios, hoje=today.isoformat(), nascimento_minimo=earliest_birth_date.isoformat(), nova_conta_temporaria=nova_conta_temporaria, senha_redefinida=senha_redefinida, is_operator=is_operator)


@app.route("/admin/logs-auditoria")
@role_required("admin")
def audit_logs():
    """Consulta exclusiva para administradores do histórico de auditoria."""
    start = request.args.get("inicio", "").strip()
    end = request.args.get("fim", "").strip()
    action = request.args.get("acao", "").strip()
    actor = request.args.get("responsavel", "").strip()[:80]
    search_term = request.args.get("busca", "").strip()[:100]
    conditions, params = [], []
    try:
        if start:
            parsed_start = datetime.strptime(start, "%Y-%m-%d").date()
            conditions.append("criado_em >= ?")
            params.append(f"{parsed_start.isoformat()} 00:00:00")
        if end:
            parsed_end = datetime.strptime(end, "%Y-%m-%d").date()
            if start and parsed_end < datetime.strptime(start, "%Y-%m-%d").date():
                raise ValueError
            conditions.append("criado_em < ?")
            params.append(f"{parsed_end.fromordinal(parsed_end.toordinal() + 1).isoformat()} 00:00:00")
    except ValueError:
        flash("Informe um período válido. A data final deve ser igual ou posterior à inicial.", "warning")
        return redirect(url_for("audit_logs"))
    if action:
        conditions.append("acao = ?")
        params.append(action)
    if actor:
        conditions.append("responsavel_nome LIKE ?")
        params.append(f"%{actor}%")
    if search_term:
        conditions.append("(CAST(id AS CHAR) LIKE ? OR alvo_nome LIKE ? OR detalhes LIKE ? OR responsavel_nome LIKE ? OR CAST(alvo_id AS CHAR) LIKE ? OR CAST(responsavel_id AS CHAR) LIKE ?)")
        pattern = f"%{search_term}%"
        params.extend([pattern, pattern, pattern, pattern, pattern, pattern])
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    logs = query(
        "SELECT id, responsavel_id, responsavel_nome, responsavel_perfil, acao, alvo_id, alvo_nome, alvo_perfil, detalhes, criado_em "
        "FROM logs_auditoria" + where + " ORDER BY criado_em DESC, id DESC LIMIT 500",
        tuple(params),
    )
    action_rows = query("SELECT DISTINCT acao FROM logs_auditoria ORDER BY acao")
    actor_rows = query("SELECT DISTINCT responsavel_nome FROM logs_auditoria ORDER BY responsavel_nome")
    return render_template(
        "audit_logs.html", logs=logs, acoes=action_rows, responsaveis=actor_rows,
        filtros={"inicio": start, "fim": end, "acao": action, "responsavel": actor, "busca": search_term},
    )


@app.route("/admin/relatorio", methods=["GET"])
@role_required("admin")
def report():
    """Exibe um resumo simples de vendas, recargas e movimentações por período."""
    start = request.args.get("inicio", "").strip()
    end = request.args.get("fim", "").strip()
    movement_conditions, purchase_conditions, params = [], [], []

    try:
        if start:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            movement_conditions.append("m.criado_em >= ?")
            purchase_conditions.append("c.criado_em >= ?")
            params.append(f"{start_date.isoformat()} 00:00:00")
        if end:
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            end_exclusive = end_date.fromordinal(end_date.toordinal() + 1)
            movement_conditions.append("m.criado_em < ?")
            purchase_conditions.append("c.criado_em < ?")
            params.append(f"{end_exclusive.isoformat()} 00:00:00")
        if start and end and start > end:
            flash("A data inicial não pode ser posterior à data final.", "warning")
            return redirect(url_for("report"))
    except ValueError:
        flash("Informe as datas em um formato válido.", "warning")
        return redirect(url_for("report"))

    movement_where = (" AND " + " AND ".join(movement_conditions)) if movement_conditions else ""
    purchase_where = (" AND " + " AND ".join(purchase_conditions)) if purchase_conditions else ""

    sales = query(
        "SELECT COUNT(*) AS quantidade, COALESCE(SUM(c.total), 0) AS valor "
        f"FROM compras c WHERE 1=1 {purchase_where}", tuple(params), one=True,
    )
    topups = query(
        "SELECT COALESCE(SUM(m.valor), 0) AS valor FROM movimentacoes m "
        f"WHERE m.operacao='recarga' AND m.status='confirmada' {movement_where}",
        tuple(params), one=True,
    )
    movements = query(
        "SELECT m.id, m.criado_em, u.nome AS cliente, m.operacao, m.status, m.valor, "
        "COALESCE(GROUP_CONCAT(DISTINCT ic.produto_nome SEPARATOR ', '), '—') AS produto "
        "FROM movimentacoes m JOIN usuarios u ON u.id=m.usuario_id "
        "LEFT JOIN compras c ON c.id=m.compra_id "
        "LEFT JOIN itens_compra ic ON ic.compra_id=c.id "
        f"WHERE 1=1 {movement_where} "
        "GROUP BY m.id, m.criado_em, u.nome, m.operacao, m.status, m.valor "
        "ORDER BY m.criado_em DESC, m.id DESC LIMIT 500",
        tuple(params),
    )
    # Pendências atuais da carteira não dependem do período selecionado.
    clientes_negativos = query(
        "SELECT u.id, u.nome, c.saldo FROM carteiras c "
        "JOIN usuarios u ON u.id = c.usuario_id "
        "WHERE u.perfil='cliente' AND c.saldo < 0 "
        "ORDER BY c.saldo ASC, u.nome ASC"
    )
    produtos_mais_vendidos = query(
        "SELECT ic.produto_nome AS produto, SUM(ic.quantidade) AS quantidade, "
        "SUM(ic.quantidade * ic.preco_unitario) AS valor_vendido "
        "FROM itens_compra ic JOIN compras c ON c.id=ic.compra_id "
        f"WHERE 1=1 {purchase_where} "
        "GROUP BY ic.produto_nome ORDER BY quantidade DESC, valor_vendido DESC LIMIT 5",
        tuple(params),
    )

    resumo = {
        "compras_quantidade": int(sales["quantidade"] or 0),
        "vendas_valor": float(sales["valor"] or 0),
        "recargas_valor": float(topups["valor"] or 0),
        "clientes_negativos_quantidade": len(clientes_negativos),
        "clientes_negativos_valor": sum(abs(float(c["saldo"] or 0)) for c in clientes_negativos),
    }
    return render_template(
        "report.html", movimentacoes=movements, resumo=resumo,
        clientes_negativos=clientes_negativos,
        produtos_mais_vendidos=produtos_mais_vendidos,
    )
