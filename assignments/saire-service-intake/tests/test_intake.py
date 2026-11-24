import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
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
