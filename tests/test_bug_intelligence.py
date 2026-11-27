import tempfile
import unittest
from pathlib import Path
from engineering_lab import debugging as d, bug_intelligence as bi, registry as reg
from test_debugging import case
def observed():
    c=case(); c.update(kind="observed_failure",repository="Jugadru/APEX-Simulation")
    return c
def report(sha):
    return dict(schema=1,head=sha,base="b"*40,state="FAILURE_EVIDENCE",planned_not_executed=[],
                failures=[dict(case="fixture.gd",status="FAIL",root_cause="NOT_ESTABLISHED",kind="ASSERTION",
                    locations=[dict(file="scripts/a.gd",line=3)],log_partial=False,candidates=[dict(file="scripts/a.gd",relation="direct_path_match",path=["scripts/a.gd"])],candidate_count=1)])
class BugTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.root=Path(t.name); (self.root/"artifacts").mkdir()
    def create(self,c=None,r=None):
        c=c or observed(); r=r or report(c["sha"]); data=reg.canonical(r); name=c["id"]+".json"
        (self.root/"artifacts"/name).write_bytes(data); c["evidence"]=[dict(file=name,sha256=reg.checksum(data))]
        d.open_case(self.root,c); return c,name
    def test_classify(self):
        c,n=self.create(); r=bi.record(self.root,c["id"],n,"fixture.gd")
        self.assertEqual(r["classification"],"ASSERTION"); self.assertEqual(r["root_cause"],"NOT_ESTABLISHED")
        self.assertEqual(bi.load(self.root,c["id"]),r)
    def test_stale(self):
        c,n=self.create(r=report("c"*40))
        with self.assertRaises(ValueError): bi.record(self.root,c["id"],n,"fixture.gd")
    def test_unknown_case(self):
        c,n=self.create()
        with self.assertRaises(ValueError): bi.record(self.root,c["id"],n,"other.gd")
    def test_unregistered(self):
        c,n=self.create()
        with self.assertRaises(ValueError): bi.record(self.root,c["id"],"other.json","fixture.gd")
    def test_no_overwrite(self):
        c,n=self.create(); bi.record(self.root,c["id"],n,"fixture.gd")
        with self.assertRaises(FileExistsError): bi.record(self.root,c["id"],n,"fixture.gd")
    def test_path_escape(self):
        r=report("a"*40); r["failures"][0]["locations"][0]["file"]="../bad.gd"
        c,n=self.create(r=r)
        with self.assertRaises(ValueError): bi.record(self.root,c["id"],n,"fixture.gd")
    def test_recurrence(self):
        a,n=self.create(); x=bi.record(self.root,a["id"],n,"fixture.gd")
        b=observed(); b.update(id="BUG-DEMO-002",sha="c"*40); b,n=self.create(b); y=bi.record(self.root,b["id"],n,"fixture.gd")
        self.assertEqual(x["fingerprint"],y["fingerprint"])
        self.assertEqual(len(bi.history(self.root,x["fingerprint"])["matches"]),2)
    def test_tampered_classification(self):
        c,n=self.create(); x=bi.record(self.root,c["id"],n,"fixture.gd"); x["classification"]="PARSE"
        (self.root/(c["id"]+".classification.json")).write_bytes(reg.canonical(x))
        with self.assertRaises(ValueError): bi.load(self.root,c["id"])
if __name__=="__main__": unittest.main()
