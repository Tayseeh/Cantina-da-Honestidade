"""Funções puras de domínio e apresentação, sem dependência do Flask ou SQLite."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo
from typing import Any, Mapping

BRASILIA_TZ = ZoneInfo("America/Sao_Paulo")


def money(value: Any) -> Decimal:
    """Converte um valor monetário em Decimal com duas casas decimais."""
    try:
        amount = Decimal(str(value).replace(",", "."))
        if not amount.is_finite() or amount < 0:
            raise ValueError
        return amount.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError("Informe um valor monetário válido.") from error


def profile_form_values(user: Mapping[str, Any]) -> dict[str, str]:
    """Prepara os dados de perfil para exibição em um formulário."""
    full_name = (user["nome"] or "").strip()
    surname = (user["sobrenome"] or "").strip()
    if surname and full_name.endswith(f" {surname}"):
        first_name = full_name[: -(len(surname) + 1)]
    elif not surname and " " in full_name:
        first_name, surname = full_name.rsplit(" ", 1)
    else:
        first_name = full_name

    phone_digits = re.sub(r"\D", "", user["telefone"] or "")
    phone = user["telefone"] or ""
    if len(phone_digits) in (10, 11):
        phone = f"({phone_digits[:2]}) {phone_digits[2:-4]}-{phone_digits[-4:]}"

    cpf_digits = re.sub(r"\D", "", user["cpf"] or "")
    cpf = user["cpf"] or ""
    if len(cpf_digits) == 11:
        cpf = f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}"

    birth_date = user["data_nascimento"] or ""
    try:
        if birth_date:
            birth_date = datetime.strptime(birth_date, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        pass

    enrollment = re.sub(r"\D", "", user["matricula"] or "")[:14]

    return {
        "nome": first_name,
        "sobrenome": surname,
        "matricula": enrollment,
        "email": user["email"] or "",
        "cpf": cpf,
        "telefone": phone,
        "data_nascimento": birth_date,
    }


def format_br_phone(value: str | None) -> str:
    """Formata telefones brasileiros de 10 ou 11 dígitos."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return value or ""


def format_datetime_br(value: Any, include_time: bool = True) -> str:
    """Formata timestamps UTC do SQLite para horário de Brasília."""
    if value is None or value == "":
        return ""
    raw = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        try:
            return datetime.strptime(raw, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return raw
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        local = parsed.astimezone(BRASILIA_TZ)
        pattern = "%d/%m/%Y %H:%M" if include_time else "%d/%m/%Y"
        return local.strftime(pattern)
    except (ValueError, OverflowError):
        return raw


def username_base(first_name: str, surname: str) -> str:
    """Gera uma base de usuário legível no formato nome.sobrenome."""
    raw = f"{first_name}.{surname}".strip().lower()
    normalized = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-z0-9]+", ".", normalized).strip(".")
    return normalized or "estudante"


def normalize_username(value: str | None) -> str:
    """Normaliza um nome de usuário para ASCII minúsculo com pontos."""
    raw = (value or "").strip().lower()
    normalized = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", ".", normalized).strip(".")
