import unittest
from test_stage_closure import fixture
from engineering_lab import stage_closure as s
class RacecraftClosureTests(unittest.TestCase):
    def test_racecraft_required_for_future_closure(self):
        m=fixture(); m.update(series="0.8",next_series="0.9")
        with self.assertRaises(ValueError): s.validate(m)
        m["candidate_runs"].append(dict(id=31,attempt=1,path=".github/workflows/racecraft.yml"))
        m["main_runs"].append(dict(id=32,attempt=1,path=".github/workflows/racecraft.yml"))
        self.assertTrue(s.validate(m))
    def test_previous_closure_compatible(self):
        self.assertTrue(s.validate(fixture()))
