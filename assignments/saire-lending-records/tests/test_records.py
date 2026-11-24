import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
import sqlite3
import unittest
from records import create_schema, add_loan, open_loans

class RecordsContract(unittest.TestCase):
    def setUp(self):
        self.con=sqlite3.connect(":memory:"); self.addCleanup(self.con.close)
        create_schema(self.con)
    def test_empty(self):
        self.assertEqual(open_loans(self.con), [])
    def test_sorted_and_filtered(self):
        add_loan(self.con, 9, "Tripod", "open")
        add_loan(self.con, 2, "Recorder", "open")
        add_loan(self.con, 4, "Cable", "returned")
        self.assertEqual(open_loans(self.con), [(2,"Recorder"),(9,"Tripod")])
    def test_duplicate_id(self):
        add_loan(self.con, 1, "Stand", "open")
        with self.assertRaises(sqlite3.IntegrityError): add_loan(self.con, 1, "Cable", "open")
    def test_invalid_item(self):
        with self.assertRaises(ValueError): add_loan(self.con, 1, "   ", "open")
