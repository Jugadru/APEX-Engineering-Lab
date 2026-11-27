import tempfile
import unittest
from pathlib import Path
from engineering_lab import experimental as e, registry as r
class ExperimentalTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.root=Path(t.name)/"run"
    def test_ordered(self):
        x=e.ordered_commands(e.specs()["ordered_commands"]["config"])
        self.assertEqual(x["metrics"],{"state_mismatches":0,"invalid_commands":0})
        self.assertEqual(x,e.ordered_commands(e.specs()["ordered_commands"]["config"]))
    def test_registry(self):
        x=e.run(self.root,"ordered_commands","EXP-TEST-001","a"*40)
        self.assertEqual(x["reported_status"],"PASS")
        self.assertEqual(x["promotion"],"NOT_AUTHORIZED")
        self.assertEqual(r.verify(self.root,"EXP-TEST-001")["artifact_bytes"],"MATCH")
    def test_config_binding(self):
        e.run(self.root,"ordered_commands","EXP-TEST-001","a"*40)
        p=r.read_json(self.root/"EXP-TEST-001.plan.json")
        self.assertEqual(p["workload"]["command_hash"],r.digest(r.read_json(self.root/"configuration.json")))
    def test_existing_root(self):
        e.run(self.root,"ordered_commands","EXP-TEST-001","a"*40)
        with self.assertRaises(FileExistsError): e.run(self.root,"ordered_commands","EXP-TEST-001","a"*40)
    def test_unknown(self):
        with self.assertRaises(ValueError): e.run(self.root,"shell","EXP-TEST-001","a"*40)
    def test_wrong_sha(self):
        with self.assertRaises(ValueError): e.run(self.root,"ordered_commands","EXP-TEST-001","main")
    def test_bytes_changed(self):
        e.run(self.root,"ordered_commands","EXP-TEST-001","a"*40)
        (self.root/"artifacts/observations.json").write_text("changed")
        with self.assertRaises(ValueError): r.verify(self.root,"EXP-TEST-001")
if __name__=="__main__": unittest.main()
