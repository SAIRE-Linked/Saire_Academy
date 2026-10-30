"""Learner-visible tests for the original SAIRE Quotation Engine project."""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quotation import calculate_subtotal, calculate_discount, calculate_final_total

D = Decimal


class QuotationTests(unittest.TestCase):
    def test_subtotal_uses_decimal_precision(self):
        self.assertEqual(calculate_subtotal(D("5000.00"), D("1200.00")), D("6200.00"))

    def test_subtotal_rounds_to_cents(self):
        self.assertEqual(calculate_subtotal(D("10.005"), D("0")), D("10.01"))

    def test_discount_is_calculated_from_subtotal(self):
        self.assertEqual(calculate_discount(D("6200.00"), D("10")), D("620.00"))

    def test_final_total_after_discount(self):
        self.assertEqual(calculate_final_total(D("5000.00"), D("1200.00"), D("10")), D("5580.00"))

    def test_negative_amount_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_subtotal(D("-1"), D("100"))

    def test_discount_over_100_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_discount(D("100"), D("101"))

    def test_float_rejected_to_avoid_rounding_errors(self):
        with self.assertRaises(ValueError):
            calculate_subtotal(10.0, D("2"))


if __name__ == "__main__":
    unittest.main()
