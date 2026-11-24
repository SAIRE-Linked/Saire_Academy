import unittest
from intake import make_ticket

class IntakeContract(unittest.TestCase):
    def test_cleaned_record(self):
        self.assertEqual(make_ticket("  Reading lamp  ", 2), {"name": "Reading lamp", "priority": 2})
    def test_empty_label(self):
        with self.assertRaises(ValueError): make_ticket("   ", 1)
    def test_priority_boundary(self):
        self.assertEqual(make_ticket("Fan", 3)["priority"], 3)
    def test_bool_priority(self):
        with self.assertRaises(ValueError): make_ticket("Fan", True)

class AdditionalContract(unittest.TestCase):
    def test_long_label(self):
        with self.assertRaises(ValueError): make_ticket("x" * 81, 1)
    def test_exact_label_boundary(self):
        self.assertEqual(len(make_ticket("x" * 80, 1)["name"]), 80)
    def test_non_text(self):
        with self.assertRaises(ValueError): make_ticket(9, 2)
    def test_low_priority(self):
        with self.assertRaises(ValueError): make_ticket("Fan", 0)
    def test_high_priority(self):
        with self.assertRaises(ValueError): make_ticket("Fan", 4)
    def test_no_coercion(self):
        with self.assertRaises(ValueError): make_ticket("Fan", "2")
    def test_fresh_record(self):
        first=make_ticket("Fan", 1); first["name"]="Changed"
        self.assertEqual(make_ticket("Fan", 1)["name"], "Fan")
