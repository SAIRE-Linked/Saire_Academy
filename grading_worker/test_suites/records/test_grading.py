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

class AdditionalContract(unittest.TestCase):
    def setUp(self):
        self.con=sqlite3.connect(":memory:"); self.addCleanup(self.con.close)
        create_schema(self.con)
    def test_idempotent_schema(self):
        add_loan(self.con, 1, "Stand", "open"); create_schema(self.con)
        self.assertEqual(open_loans(self.con), [(1,"Stand")])
    def test_database_status_constraint(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO loans VALUES (1, 'Stand', 'lost')")
    def test_database_required(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO loans VALUES (1, NULL, 'open')")
    def test_parameterised_value(self):
        label="Reader's stand'); DROP TABLE loans; --"
        self.assertIsNone(add_loan(self.con, 1, label, "open"))
        self.assertEqual(open_loans(self.con), [(1,label)])
    def test_reject_id(self):
        for value in (True, 0, -1, "1"):
            with self.assertRaises(ValueError): add_loan(self.con,value,"Stand","open")
    def test_reject_status(self):
        with self.assertRaises(ValueError): add_loan(self.con,1,"Stand","lost")
    def test_trim(self):
        add_loan(self.con,1,"  Stand  ","open")
        self.assertEqual(open_loans(self.con), [(1,"Stand")])
    def test_caller_owns_transaction(self):
        self.con.commit()
        add_loan(self.con,1,"Stand","open")
        self.con.rollback()
        self.assertEqual(open_loans(self.con), [])
