import unittest
from workflow import transition, summary

class WorkflowContract(unittest.TestCase):
    def test_allowed(self):
        self.assertEqual(transition("new", "assigned"), "assigned")
    def test_rejected(self):
        with self.assertRaises(ValueError): transition("new", "closed")
    def test_count(self):
        self.assertEqual(summary([{"status":"new"},{"status":"new"}]), {"new":2,"assigned":0,"closed":0})
    def test_empty(self):
        self.assertEqual(summary([]), {"new":0,"assigned":0,"closed":0})

class AdditionalContract(unittest.TestCase):
    def test_other_routes(self):
        self.assertEqual(transition("assigned", "closed"), "closed")
        self.assertEqual(transition("closed", "new"), "new")
    def test_same_state(self):
        with self.assertRaises(ValueError): transition("new", "new")
    def test_nontext_state(self):
        with self.assertRaises(ValueError): transition([], "new")
    def test_unknown_state(self):
        with self.assertRaises(ValueError): transition("lost", "new")
    def test_unknown_record(self):
        with self.assertRaises(ValueError): summary([{"status":"lost"}])
    def test_missing_record(self):
        with self.assertRaises(ValueError): summary([{}])
    def test_invalid_record_type(self):
        with self.assertRaises(ValueError): summary([None])
    def test_invalid_collection(self):
        with self.assertRaises(ValueError): summary("new")
    def test_unhashable_status(self):
        with self.assertRaises(ValueError): summary([{"status":[]}])
    def test_preserve(self):
        import copy
        rows=[{"status":"closed","extra":[1]}, {"status":"assigned"}, {"status":"new"}]
        before=copy.deepcopy(rows)
        self.assertEqual(summary(rows), {"new":1,"assigned":1,"closed":1})
        self.assertEqual(rows,before)
