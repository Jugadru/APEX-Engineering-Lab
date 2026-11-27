import tempfile
import unittest
from pathlib import Path
from engineering_lab import debugging as d, registry as reg
def case():
    return dict(schema=1,id="BUG-DEMO-001",repository="example/synthetic",sha="a"*40,
                domain="quality",kind="synthetic",title="Controlled fixture",symptom="Unexpected output",
                expected="55",observed="54",evidence=[],limitations="Synthetic only")
class DebugTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.root=Path(t.name)
    def test_open(self):
        o=d.open_case(self.root,case())
        self.assertEqual(o["state"],"OPEN"); self.assertEqual(o["root_cause"],"NOT_ESTABLISHED")
        self.assertEqual(o["promotion"],"NOT_AUTHORIZED"); self.assertEqual(o["hypothesis_budget"],2)
    def test_no_overwrite(self):
        d.open_case(self.root,case())
        with self.assertRaises(FileExistsError): d.open_case(self.root,case())
    def test_invalid_id(self):
        c=case(); c["id"]="../bad"
        with self.assertRaises(ValueError): d.open_case(self.root,c)
    def test_bad_sha(self):
        c=case(); c["sha"]="main"
        with self.assertRaises(ValueError): d.open_case(self.root,c)
    def test_observed_requires_evidence(self):
        c=case(); c.update(kind="observed_failure",repository="Jugadru/APEX-Simulation")
        with self.assertRaises(ValueError): d.open_case(self.root,c)
    def test_tamper_evidence(self):
        c=case(); c["evidence"]=[dict(file="log.txt",sha256=reg.checksum(b"original"))]
        (self.root/"artifacts").mkdir(); p=self.root/"artifacts/log.txt"; p.write_bytes(b"original")
        d.open_case(self.root,c); p.write_bytes(b"modified")
        with self.assertRaises(ValueError): d.inspect_case(self.root,c["id"])
    def test_unknown_repo(self):
        c=case(); c["repository"]="other/repo"
        with self.assertRaises(ValueError): d.open_case(self.root,c)
    def test_case_not_found(self):
        with self.assertRaises((ValueError,OSError)): d.inspect_case(self.root,"BUG-NONE")
if __name__=="__main__": unittest.main()
