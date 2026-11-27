import tempfile
import unittest
from pathlib import Path
from engineering_lab import registry as reg, solution as sol
class SolutionTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.root=Path(t.name)/"run"
        self.ident="BUG-REPRO-DEMO"
    def fresh(self):
        sol.demo(self.root)
        p=self.root/(self.ident+".solution.json"); x=reg.read_json(p)
        p.unlink(); (self.root/"EXP-SOLUTION-DEMO.result.json").unlink()
        return x
    def test_demo(self):
        x=sol.demo(self.root)
        self.assertEqual(x["candidates"][0]["status"],"REVIEW_CANDIDATE")
        self.assertEqual(x["candidates"][0]["metrics"]["sum"],55)
        self.assertEqual(x["gameplay_validation"],"NOT_RUN")
        self.assertEqual(x["promotion"],"NOT_AUTHORIZED")
    def test_unrun(self):
        x=self.fresh(); sol.bind(self.root,self.ident,x)
        self.assertEqual(sol.evaluate(self.root,self.ident)["candidates"][0]["status"],"NOT_RUN")
    def test_budget(self):
        x=self.fresh(); x["hypotheses"]*=3
        with self.assertRaises(ValueError): sol.bind(self.root,self.ident,x)
    def test_noncomparable(self):
        x=self.fresh(); p=self.root/"EXP-SOLUTION-DEMO.plan.json"; q=reg.read_json(p)
        q["workload"]["seed"]=9; p.write_bytes(reg.canonical(q)); x["hypotheses"][0]["plan_sha256"]=reg.digest(q)
        with self.assertRaises(ValueError): sol.bind(self.root,self.ident,x)
    def test_stale_baseline(self):
        x=self.fresh(); x["baseline_result_sha256"]="0"*64
        with self.assertRaises(ValueError): sol.bind(self.root,self.ident,x)
    def test_path_escape(self):
        x=self.fresh(); x["hypotheses"][0]["files"]=["../bad"]
        with self.assertRaises(ValueError): sol.bind(self.root,self.ident,x)
    def test_after_observation(self):
        sol.demo(self.root); x=reg.read_json(self.root/(self.ident+".solution.json"))
        with self.assertRaises(ValueError): sol.bind(self.root,self.ident,x)
    def test_criterion_change(self):
        sol.demo(self.root); p=self.root/"EXP-SOLUTION-DEMO.plan.json"; q=reg.read_json(p)
        q["criteria"]["sum"]["threshold"]=54; p.write_bytes(reg.canonical(q))
        with self.assertRaises(ValueError): sol.evaluate(self.root,self.ident)
    def test_artifact_tamper(self):
        sol.demo(self.root); (self.root/"artifacts/candidate.json").write_text("changed")
        with self.assertRaises(ValueError): sol.evaluate(self.root,self.ident)
if __name__=="__main__": unittest.main()
