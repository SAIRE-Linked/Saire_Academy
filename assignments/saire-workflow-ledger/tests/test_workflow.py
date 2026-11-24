import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
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
