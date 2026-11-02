"""Original instructor-authored independent checks (not bundled with learner starter).

These tests verify declared requirements; the student's own tests are not graded.
The learner can view the expected contract, but not this suite in the download.
"""
import unittest
from decimal import Decimal
from quotation import calculate_subtotal, calculate_discount, calculate_final_total

D = Decimal


class QuotationGrading(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(calculate_subtotal(D('10'), D('20')), D('30.00'))

    def test_round_half_up(self):
        self.assertEqual(calculate_subtotal(D('10.005'), D('0')), D('10.01'))

    def test_no_binary_floats(self):
        with self.assertRaises(ValueError):
            calculate_subtotal(10.0, D('4'))

    def test_reject_negative_base(self):
        with self.assertRaises(ValueError):
            calculate_subtotal(D('-1'), D('3'))

    def test_reject_negative_service(self):
        with self.assertRaises(ValueError):
            calculate_subtotal(D('1'), D('-3'))

    def test_reject_invalid_type(self):
        with self.assertRaises(ValueError):
            calculate_discount('100', D('20'))

    def test_discount(self):
        self.assertEqual(calculate_discount(D('600'), D('25')), D('150.00'))

    def test_discount_rounds(self):
        self.assertEqual(calculate_discount(D('100.10'), D('5')), D('5.01'))

    def test_reject_discount_out_of_range(self):
        for n in (D('-1'), D('101')):
            with self.subTest(n=n), self.assertRaises(ValueError):
                calculate_discount(D('100'), n)

    def test_zero_discount(self):
        self.assertEqual(calculate_final_total(D('50'), D('0'), D('0')), D('50.00'))

    def test_full_discount(self):
        self.assertEqual(calculate_final_total(D('50'), D('20'), D('100')), D('0.00'))

    def test_final_total(self):
        self.assertEqual(calculate_final_total(D('5000'), D('1200'), D('10')), D('5580.00'))

    def test_final_rounding(self):
        self.assertEqual(calculate_final_total(D('0.01'), D('0'), D('50')), D('0.00'))
