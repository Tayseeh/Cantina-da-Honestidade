import unittest
from services.login_attempt_service import account_attempt_key


class LoginAttemptKeyTests(unittest.TestCase):
    def test_same_account_uses_same_key_for_different_case(self):
        self.assertEqual(
            account_attempt_key("TAYSE@EXAMPLE.COM"),
            account_attempt_key("tayse@example.com"),
        )

    def test_known_account_key_is_based_on_account_id(self):
        self.assertEqual(account_attempt_key("user@example.com", 123), "account:123")

    def test_unknown_identifier_is_not_stored_in_key(self):
        key = account_attempt_key("private@example.com")
        self.assertTrue(key.startswith("unknown:"))
        self.assertNotIn("private@example.com", key)


if __name__ == "__main__":
    unittest.main()
