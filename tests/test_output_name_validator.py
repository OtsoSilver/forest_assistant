import unittest

from utils.validators import OutputNameValidator


class OutputNameValidatorTests(unittest.TestCase):
    def test_validate_parts_accepts_numeric_quarter_and_compartment(self) -> None:
        result = OutputNameValidator.validate_parts("18", "12")

        self.assertTrue(result.is_valid)
        self.assertEqual(result.normalized, "КВ 18 В 12")

    def test_validate_parts_rejects_non_numeric_values(self) -> None:
        result = OutputNameValidator.validate_parts("abc", "12")

        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.error)
        self.assertIn("квартал", result.error.lower())


if __name__ == "__main__":
    unittest.main()
