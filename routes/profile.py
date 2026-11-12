"""Rotas de profile do Confia+."""

from core import (
    BASE_DIR,
    DatabaseIntegrityError,
    abort,
    app,
    current_user,
    datetime,
    execute,
    flash,
    generate_password_hash,
    login_required,
    role_required,
    os,
    process_profile_photo,
    profile_form_values,
    format_datetime_br,
    jsonify,
    query,
    re,
    redirect,
    render_template,
    request,
    url_for,
    uuid,
)

@app.route("/perfil", methods=["GET", "POST"])
@login_required
def profile():
    """Exibe e atualiza os dados pessoais, foto e credenciais do usuário."""
    user = current_user()
    editando = request.args.get("editar") == "1"
    tela_seguranca = request.args.get("seguranca", "")
    if tela_seguranca not in ("senha", "pin") or (tela_seguranca == "pin" and user["perfil"] != "cliente"):
        tela_seguranca = ""
    dados = profile_form_values(user)
    credential_saved = False
    if request.method == "POST":
        action = request.form.get("acao")
        if action == "perfil" and user["perfil"] not in ("cliente", "operador", "admin"):
            abort(403)
        if action == "perfil" and user["perfil"] in ("cliente", "operador", "admin"):
            editando = True
            dados = {key: request.form.get(key, "").strip() for key in ("nome", "sobrenome", "email", "cpf", "telefone", "data_nascimento")}
            if user["perfil"] == "operador":
                dados["email"] = (user.get("email") or "").strip()
            dados["matricula"] = user["matricula"]
            errors = []
            for label, key in (("Nome", "nome"), ("Sobrenome", "sobrenome")):
                value = dados[key]
                if not value or len(value) > 30 or not re.fullmatch(r"[^\W\d_]+(?:[ '-][^\W\d_]+)*", value, flags=re.UNICODE):
                    errors.append(f"{label}: use apenas letras, espaços, hífen ou apóstrofo (até 30 caracteres).")

            dados["email"] = dados["email"].lower()
            email_pattern = r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+"
            if user["perfil"] == "operador" and not dados["email"]:
                errors.append("E-mail: o preenchimento é obrigatório para operadores.")
            elif dados["email"] and (len(dados["email"]) > 50 or not re.fullmatch(email_pattern, dados["email"], flags=re.IGNORECASE)):
                errors.append("E-mail: informe um endereço válido com até 50 caracteres.")
            email_storage = dados["email"] or None

            cpf_digits = "".join(character for character in dados["cpf"] if character.isdigit()) or None
            if dados["cpf"] and (not cpf_digits or not re.fullmatch(r"\d{11}", cpf_digits) or not re.fullmatch(r"(?:\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2})", dados["cpf"])):
                errors.append("CPF: informe 11 números no formato 000.000.000-00.")

            ddds = {"11", "12", "13", "14", "15", "16", "17", "18", "19", "21", "22", "24", "27", "28", "31", "32", "33", "34", "35", "37", "38", "41", "42", "43", "44", "45", "46", "47", "48", "49", "51", "53", "54", "55", "61", "62", "63", "64", "65", "66", "67", "68", "69", "71", "73", "74", "75", "77", "79", "81", "82", "83", "84", "85", "86", "87", "88", "89", "91", "92", "93", "94", "95", "96", "97", "98", "99"}
            phone_digits = "".join(character for character in dados["telefone"] if character.isdigit())
            if phone_digits.startswith("55") and len(phone_digits) in (12, 13):
                phone_digits = phone_digits[2:]
            valid_phone = not dados["telefone"] or (re.fullmatch(r"[\d\s()+.-]+", dados["telefone"]) and len(phone_digits) in (10, 11) and phone_digits[:2] in ddds)
            if dados["telefone"] and valid_phone:
                subscriber = phone_digits[2:]
                valid_phone = (len(subscriber) == 9 and subscriber.startswith("9")) or (len(subscriber) == 8 and subscriber[0] in "2345")
            if not valid_phone:
                errors.append("Telefone: informe um número brasileiro válido com DDD.")

            if dados["data_nascimento"]:
                try:
                    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", dados["data_nascimento"]):
                        raise ValueError
                    birth_date = datetime.strptime(dados["data_nascimento"], "%d/%m/%Y").date()
                    today = datetime.today().date()
                    try:
                        earliest_birth_date = today.replace(year=today.year - 120)
                    except ValueError:
                        earliest_birth_date = today.replace(year=today.year - 120, day=28)
                    if not earliest_birth_date <= birth_date <= today:
                        raise ValueError
                    birth_date_storage = birth_date.isoformat()
                except ValueError:
                    birth_date_storage = ""
                    errors.append("Data de nascimento: digite uma data válida.")
            else:
                birth_date_storage = ""

            photo_bytes = None
            try:
                photo_bytes = process_profile_photo(request.files.get("foto"))
            except ValueError as error:
                errors.append(str(error))

            if not errors:
                for column, value, label in (("email", email_storage, "E-mail"), ("cpf", cpf_digits, "CPF")):
                    lookup = "lower(email) = lower(?)" if column == "email" else f"{column} = ?"
                    if value and query(f"SELECT id FROM usuarios WHERE {lookup} AND id != ?", (value, user["id"]), one=True):
                        errors.append(f"{label}: já existe uma conta cadastrada com esse dado.")

            if not errors:
                old_photo_path = user["foto_perfil"] or ""
                remove_photo = request.form.get("remover_foto") == "1" and photo_bytes is None
                new_photo_path = "" if remove_photo else old_photo_path
                new_photo_disk_path = None
                if photo_bytes is not None:
                    photo_folder = os.path.join(BASE_DIR, "static", "uploads", "perfis")
                    os.makedirs(photo_folder, exist_ok=True)
                    photo_filename = f"{uuid.uuid4().hex}.jpg"
                    new_photo_path = f"uploads/perfis/{photo_filename}"
                    new_photo_disk_path = os.path.join(photo_folder, photo_filename)
                    with open(new_photo_disk_path, "wb") as photo_file:
                        photo_file.write(photo_bytes)
                try:
                    execute(
                        "UPDATE usuarios SET nome = ?, sobrenome = ?, email = ?, cpf = ?, telefone = ?, data_nascimento = ?, foto_perfil = ? WHERE id = ?",
                        (f'{dados["nome"]} {dados["sobrenome"]}', dados["sobrenome"], email_storage, cpf_digits, phone_digits, birth_date_storage, new_photo_path, user["id"]),
                    )
                    if new_photo_path != old_photo_path and old_photo_path.startswith("uploads/perfis/"):
                        old_photo_disk_path = os.path.join(BASE_DIR, "static", "uploads", "perfis", os.path.basename(old_photo_path))
                        if os.path.isfile(old_photo_disk_path):
                            try:
                                os.remove(old_photo_disk_path)
                            except OSError:
                                pass
                    flash("Perfil atualizado com sucesso.", "success")
                    return redirect(url_for("profile"))
                except DatabaseIntegrityError:
                    if new_photo_disk_path and os.path.isfile(new_photo_disk_path):
                        os.remove(new_photo_disk_path)
                    errors.append("E-mail ou CPF já cadastrado em outra conta.")

            for error in errors:
                flash(error, "danger")
        elif action == "senha":
            new_password = request.form.get("senha", "")
            password_confirmation = request.form.get("confirmar_senha", "")
            if new_password != password_confirmation:
                flash("A confirmação da senha não corresponde.", "danger")
            elif len(new_password) < 8 or len(new_password) > 20 or not re.search(r"[^\W\d_]", new_password, flags=re.UNICODE) or not re.search(r"\d", new_password):
                flash("Use de 8 a 20 caracteres, incluindo uma letra e um número.", "danger")
            else:
                execute("UPDATE usuarios SET senha_hash = ? WHERE id = ?", (generate_password_hash(new_password), user["id"]))
                credential_saved = True
                flash("Senha atualizada.", "success")
        elif action == "pin" and user["perfil"] == "cliente":
            pin = request.form.get("pin", "")
            pin_confirmation = request.form.get("confirmar_pin", "")
            if pin != pin_confirmation:
                flash("A confirmação do PIN não corresponde.", "danger")
            elif not re.fullmatch(r"[0-9]{4}", pin):
                flash("O PIN deve conter exatamente 4 números.", "danger")
            else:
                execute("UPDATE usuarios SET pin_hash = ? WHERE id = ?", (generate_password_hash(pin), user["id"]))
                credential_saved = True
                flash("PIN de pagamento atualizado.", "success")
        if action != "perfil" or not errors:
            if action == "senha":
                return redirect(url_for("profile") if credential_saved else url_for("profile", seguranca="senha"))
            if action == "pin":
                return redirect(url_for("profile") if credential_saved else url_for("profile", seguranca="pin"))
            return redirect(url_for("profile"))
    today = datetime.today().date()
    try:
        earliest_birth_date = today.replace(year=today.year - 120)
    except ValueError:
        earliest_birth_date = today.replace(year=today.year - 120, day=28)
    return render_template(
        "profile.html",
        usuario=current_user(),
        dados=dados,
        editando=editando,
        tela_seguranca=tela_seguranca,
        foto_removida=request.method == "POST" and request.form.get("remover_foto") == "1",
        hoje=today.isoformat(),
        nascimento_minimo=earliest_birth_date.isoformat(),
    )



# Notificações e ajuda do cliente.
@app.route("/notificacoes")
@role_required("cliente")
def notifications():
    """Exibe as notificações disponíveis para o cliente autenticado."""
    user = current_user(); notes = query("SELECT * FROM notificacoes WHERE usuario_id = ? ORDER BY criado_em DESC", (user["id"],))
    execute("UPDATE notificacoes SET lida = 1 WHERE usuario_id = ?", (user["id"],))
    return render_template("notifications.html", notificacoes=notes)

@app.post("/api/notificacoes/<int:notification_id>/ler")
@role_required("cliente")
def mark_notification_read(notification_id):
    """Marca como lida apenas uma notificação pertencente ao cliente autenticado."""
    user = current_user()
    execute(
        "UPDATE notificacoes SET lida = 1 WHERE id = ? AND usuario_id = ?",
        (notification_id, user["id"]),
    )
    return jsonify(success=True)


@app.route("/api/notificacoes/resumo")
@role_required("cliente")
def notifications_summary():
    """Retorna um resumo das notificações do cliente em formato de API."""
    user = current_user()
    notes = query(
        "SELECT id, mensagem, criado_em FROM notificacoes WHERE usuario_id = ? AND lida = 0 ORDER BY criado_em DESC LIMIT 5",
        (user["id"],),
    )
    count = query(
        "SELECT COUNT(*) AS total FROM notificacoes WHERE usuario_id = ? AND lida = 0",
        (user["id"],), one=True,
    )["total"]
    return jsonify(
        count=count,
        notifications=[{"id": note["id"], "message": note["mensagem"], "created_at": format_datetime_br(note["criado_em"])} for note in notes],
    )

@app.route("/ajuda/atalhos")
@role_required("cliente")
def customer_shortcuts_help():
    """Apresenta orientações e atalhos úteis para o cliente."""
    return render_template("help_shortcuts.html")
