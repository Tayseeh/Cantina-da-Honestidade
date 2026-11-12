import pytest

from services.product_service import parse_product_form


@pytest.fixture
def valid_form():
    return {
        "nome": "Água mineral",
        "descricao": "Garrafa 500 ml",
        "preco_compra": "1,50",
        "preco_venda": "2,50",
        "estoque": "25",
        "estoque_baixo": "5",
    }


def test_parse_product_form_normalizes_values(valid_form):
    result = parse_product_form(valid_form)
    assert result["nome"] == "Água mineral"
    assert str(result["preco_compra"]) == "1.50"
    assert str(result["preco_venda"]) == "2.50"
    assert result["estoque"] == 25
    assert result["estoque_baixo"] == 5


@pytest.mark.parametrize("field,value", [
    ("nome", ""),
    ("nome", "_produto"),
    ("preco_compra", "-1,00"),
    ("preco_venda", "abc"),
    ("estoque", "1.5"),
    ("estoque_baixo", "0"),
    ("estoque_baixo", "-2"),
])
def test_rejects_invalid_product_data(valid_form, field, value):
    valid_form[field] = value
    with pytest.raises(ValueError):
        parse_product_form(valid_form)


def test_default_low_stock_is_five(valid_form):
    valid_form.pop("estoque_baixo")
    assert parse_product_form(valid_form)["estoque_baixo"] == 5
