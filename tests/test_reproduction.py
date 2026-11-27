import tempfile
import unittest
from pathlib import Path
from engineering_lab import reproduction as rp, registry as reg, debugging as dbg
class ReproTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.root=Path(t.name)/"run"
    def test_actual_demo(self):
        r=rp.demo(self.root)
        self.assertEqual(r["status"],"MATCHING_FAILURE_OBSERVED")
        self.assertEqual(r["root_cause"],"NOT_ESTABLISHED")
        self.assertEqual(r["promotion"],"NOT_AUTHORIZED")
        self.assertEqual(rp.check(self.root,"BUG-REPRO-DEMO"),r)
    def setup_plan(self):
        rp.demo(self.root)
        # New synthetic registry cloned before any result; fixture setup only.
        (self.root/"EXP-REPRO-DEMO.result.json").unlink()
        link=reg.read_json(self.root/"BUG-REPRO-DEMO.reproduction.json")
        (self.root/"BUG-REPRO-DEMO.reproduction.json").unlink()
        return link
    def test_unrun(self):
        link=self.setup_plan(); rp.bind(self.root,link["id"],link)
        self.assertEqual(rp.check(self.root,link["id"])["status"],"NOT_RUN")
    def test_budget(self):
        link=self.setup_plan(); link["budget_minutes"]=16
        with self.assertRaises(ValueError): rp.bind(self.root,link["id"],link)
    def test_pass_value_rejected(self):
        link=self.setup_plan(); link["failure_value"]=55
        with self.assertRaises(ValueError): rp.bind(self.root,link["id"],link)
    def test_case_hash(self):
        link=self.setup_plan(); link["case_sha256"]="0"*64
        with self.assertRaises(ValueError): rp.bind(self.root,link["id"],link)
    def test_after_observation_rejected(self):
        rp.demo(self.root); link=reg.read_json(self.root/"BUG-REPRO-DEMO.reproduction.json")
        with self.assertRaises(ValueError): rp.bind(self.root,link["id"],link)
    def test_tamper(self):
        rp.demo(self.root); (self.root/"artifacts/baseline.json").write_text("changed")
        with self.assertRaises(ValueError): rp.check(self.root,"BUG-REPRO-DEMO")
    def test_changed_criteria(self):
        rp.demo(self.root); p=reg.read_json(self.root/"EXP-REPRO-DEMO.plan.json")
        p["criteria"]["sum"]["threshold"]=56
        (self.root/"EXP-REPRO-DEMO.plan.json").write_bytes(reg.canonical(p))
        with self.assertRaises(ValueError): rp.check(self.root,"BUG-REPRO-DEMO")
    def test_wrong_baseline(self):
        link=self.setup_plan(); p=reg.read_json(self.root/"EXP-REPRO-DEMO.plan.json"); p["baseline_sha"]="c"*40
        (self.root/"EXP-REPRO-DEMO.plan.json").write_bytes(reg.canonical(p))
        with self.assertRaises(ValueError): rp.bind(self.root,link["id"],link)
if __name__=="__main__": unittest.main()
