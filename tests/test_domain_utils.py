import unittest

from domain_utils import (
    money,
    profile_form_values,
    format_br_phone,
    format_datetime_br,
    username_base,
    normalize_username,
)


class DomainUtilsTests(unittest.TestCase):
    def test_money_uses_two_decimal_places(self):
        self.assertEqual(str(money("12,5")), "12.50")

    def test_money_rejects_negative_and_invalid_values(self):
        for value in ("-1,00", "abc", "NaN"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    money(value)

    def test_format_br_phone(self):
        self.assertEqual(format_br_phone("48999991234"), "(48) 99999-1234")
        self.assertEqual(format_br_phone("(48) 3333-1234"), "(48) 3333-1234")
        self.assertEqual(format_br_phone("123"), "123")

    def test_format_datetime_br(self):
        self.assertEqual(format_datetime_br("2026-11-11"), "11/11/2026")
        self.assertEqual(
            format_datetime_br("2026-11-11T12:00:00Z"),
            "11/11/2026 09:00",
        )
        self.assertEqual(format_datetime_br(None), "")

    def test_username_helpers_normalize_accents_and_spaces(self):
        self.assertEqual(username_base("João", " da Silva"), "joao.da.silva")
        self.assertEqual(normalize_username("  ANA Paula  "), "ana.paula")
        self.assertEqual(normalize_username(None), "")

    def test_profile_form_values_formats_registration_data(self):
        user = {
            "nome": "Ana Paula Silva",
            "sobrenome": "Silva",
            "telefone": "48999991234",
            "cpf": "12345678900",
            "data_nascimento": "2000-02-03",
            "matricula": "12345678123456",
            "email": "ana@example.com",
        }
        result = profile_form_values(user)
        self.assertEqual(result["nome"], "Ana Paula")
        self.assertEqual(result["sobrenome"], "Silva")
        self.assertEqual(result["telefone"], "(48) 99999-1234")
        self.assertEqual(result["cpf"], "123.456.789-00")
        self.assertEqual(result["data_nascimento"], "03/02/2000")
        self.assertEqual(result["matricula"], "12345678123456")
        self.assertEqual(result["email"], "ana@example.com")


if __name__ == "__main__":
    unittest.main()
