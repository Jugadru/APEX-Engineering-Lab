import tempfile
import unittest
from pathlib import Path
from engineering_lab import engineering_memory as m, registry as reg, solution as sol
from engineering_lab import debugging as dbg
from test_debugging import case
class MemoryTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.root=Path(t.name)/"run"
    def test_demo(self):
        r=m.demo(self.root)
        self.assertEqual(r["snapshot"]["solution"]["candidates"][0]["status"],"REVIEW_CANDIDATE")
        self.assertEqual(r["promotion"],"NOT_AUTHORIZED")
        self.assertFalse(r["new_evidence_available"])
    def test_search(self):
        m.demo(self.root); r=m.search(self.root,"arithmetic synthetic")
        self.assertEqual(r["total"],1)
        self.assertEqual(r["matches"][0]["id"],"MEM-DEMO-001")
    def test_historical(self):
        self.root.mkdir(); h=reg.read_json(Path("research/debug-history.json"))
        r=m.search(self.root,"regressao multiline",h)
        self.assertEqual(r["total"],1)
        self.assertEqual(r["matches"][0]["origin"],"HISTORICAL_DOCUMENTARY")
    def test_history_contradiction(self):
        h=reg.read_json(Path("research/debug-history.json")); h["entries"][0]["observations"][0]["status"]="PASS"
        with self.assertRaises(ValueError): m.historical(h)
    def test_immutable(self):
        r=m.demo(self.root)
        with self.assertRaises(FileExistsError): m.record(self.root,r["input"])
    def test_case_tamper(self):
        m.demo(self.root); p=self.root/"BUG-REPRO-DEMO.case.json"; c=reg.read_json(p)
        c["title"]="other"; p.write_bytes(reg.canonical(c))
        with self.assertRaises(ValueError): m.read(self.root,"MEM-DEMO-001")
    def test_evidence_tamper(self):
        m.demo(self.root); (self.root/"artifacts/candidate.json").write_text("changed")
        with self.assertRaises(ValueError): m.read(self.root,"MEM-DEMO-001")
    def test_open_case_memory(self):
        self.root.mkdir(); c=case(); dbg.open_case(self.root,c)
        r=m.record(self.root,dict(schema=1,id="MEM-OPEN-001",case=c["id"],lesson="Still unresolved",tags=["pending"],limitations="No result"))
        self.assertIsNone(r["snapshot"]["reproduction"])
    def test_new_evidence(self):
        sol.demo(self.root)
        result=self.root/"EXP-SOLUTION-DEMO.result.json"; raw=result.read_bytes(); result.unlink()
        r=m.record(self.root,dict(schema=1,id="MEM-PENDING-001",case="BUG-REPRO-DEMO",lesson="Pending review",tags=["pending"],limitations="Synthetic"))
        self.assertEqual(r["snapshot"]["solution"]["candidates"][0]["status"],"NOT_RUN")
        result.write_bytes(raw)
        self.assertTrue(m.read(self.root,"MEM-PENDING-001")["new_evidence_available"])
    def test_bad_query(self):
        self.root.mkdir()
        with self.assertRaises(ValueError): m.search(self.root,"")
if __name__=="__main__": unittest.main()
