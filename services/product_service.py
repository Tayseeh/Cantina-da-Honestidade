"""Regras de validação e preparação dos dados de produtos."""

import re

from domain_utils import money


def parse_product_form(form):
    """Valida e converte os campos do formulário de produto.

    Retorna os valores já normalizados para cadastro ou edição.
    """
    name = form.get("nome", "").strip()
    description = form.get("descricao", "").strip()
    raw_purchase = form.get("preco_compra", "").strip()
    raw_sale = form.get("preco_venda", "").strip()
    raw_stock = form.get("estoque", "").strip()
    raw_low_stock = form.get("estoque_baixo", "5").strip()

    valid_name = re.fullmatch(r"[^\W_](?:[^\W_]|[\s.,'’()/&+-]){0,79}", name, re.UNICODE)
    valid_description = re.fullmatch(r"(?:[^\W_]|[\s.,;:!?()'’\"/_&+%#@-]){0,250}", description, re.UNICODE)
    valid_purchase = re.fullmatch(r"\d{1,9}(?:[,.]\d{1,2})?", raw_purchase)
    valid_sale = re.fullmatch(r"\d{1,9}(?:[,.]\d{1,2})?", raw_sale)
    valid_stock = re.fullmatch(r"\d{1,6}", raw_stock)
    valid_low_stock = re.fullmatch(r"\d{1,6}", raw_low_stock)

    if not all((valid_name, valid_description, valid_purchase, valid_sale, valid_stock, valid_low_stock)):
        raise ValueError("Confira os dados do produto e tente novamente.")
    if int(raw_low_stock) < 1:
        raise ValueError("O limite de estoque baixo deve ser maior que zero.")

    return {
        "nome": name,
        "descricao": description,
        "preco_compra": money(raw_purchase),
        "preco_venda": money(raw_sale),
        "estoque": int(raw_stock),
        "estoque_baixo": int(raw_low_stock),
    }
