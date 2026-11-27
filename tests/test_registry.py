import copy
import tempfile
import unittest
from pathlib import Path
from engineering_lab import registry as reg
from engineering_lab.__main__ import demo

class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "artifacts").mkdir()
        self.data = b'{"mismatches":0}'
        (self.root / "artifacts" / "e.json").write_bytes(self.data)
        self.p = dict(schema=1, id="EXP-TEST-001", peer="hyper_engine", hypothesis="fixture",
                      scope="synthetic", sources=["IDEA-001"], repository="example/synthetic",
                      candidate_sha="a"*40, lab_sha="b"*40, baseline_sha="c"*40, kind="simulation",
                      workload=dict(environment="offline", scenario="fixture", seed=42, ticks=90,
                                    command_hash="d"*64, authorization="offline_only"),
                      criteria={"mismatches": dict(op="eq", threshold=0, unit="count")})
        self.r = dict(schema=1, id=self.p["id"], plan_sha256=reg.digest(self.p), candidate_sha="a"*40,
                      lab_sha="b"*40, status="PASS", metrics={"mismatches":0},
                      evidence=[dict(file="e.json", sha256=reg.checksum(self.data))], limitations="synthetic")
    def check(self):
        return reg.validate_result(self.p, self.r, self.root)
    def test_all_peers(self):
        for peer in reg.PEERS:
            p = copy.deepcopy(self.p)
            p["peer"] = peer
            self.assertEqual(len(reg.validate_plan(p)),64)
    def test_valid(self):
        out = self.check()
        self.assertEqual(out["artifact_bytes"], "MATCH")
        self.assertEqual(out["authenticity"], "NOT_VERIFIED")
        self.assertEqual(out["promotion"], "NOT_AUTHORIZED")
    def test_plan_changed(self):
        self.p["criteria"]["mismatches"]["threshold"] = 1
        with self.assertRaises(ValueError): self.check()
    def test_sha_changed(self):
        self.r["candidate_sha"] = "f"*40
        with self.assertRaises(ValueError): self.check()
    def test_false_pass(self):
        self.r["metrics"]["mismatches"] = 1
        with self.assertRaises(ValueError): self.check()
        self.r["status"] = "FAIL"
        self.assertEqual(self.check()["reported_status"], "FAIL")
    def test_no_evidence(self):
        self.r["evidence"] = []
        with self.assertRaises(ValueError): self.check()
    def test_invalid_metrics(self):
        for value in (True, float("nan"), float("inf")):
            self.r["metrics"]["mismatches"] = value
            with self.assertRaises(ValueError): self.check()
    def test_no_synthetic_fps(self):
        self.p["criteria"]["fps"] = dict(op="ge", threshold=30, unit="fps")
        with self.assertRaises(ValueError): reg.validate_plan(self.p)
    def test_missing_seed(self):
        self.p["workload"]["seed"] = None
        with self.assertRaises(ValueError): reg.validate_plan(self.p)
    def test_native_authorization(self):
        self.p["kind"] = "native_graphics"
        with self.assertRaises(ValueError): reg.validate_plan(self.p)
    def test_registry_immutable(self):
        with self.assertRaises((OSError, ValueError)): reg.register_result(self.root,self.r)
        reg.register_plan(self.root,self.p)
        with self.assertRaises(FileExistsError): reg.register_plan(self.root,self.p)
        reg.register_result(self.root,self.r)
        with self.assertRaises(FileExistsError): reg.register_result(self.root,self.r)
        self.assertEqual(reg.verify(self.root,self.p["id"])["reported_status"],"PASS")
    def test_tamper(self):
        reg.register_plan(self.root,self.p)
        reg.register_result(self.root,self.r)
        (self.root / "artifacts" / "e.json").write_bytes(b"wrong")
        with self.assertRaises(ValueError): reg.verify(self.root,self.p["id"])
    def test_traversal_and_symlink(self):
        self.r["evidence"][0]["file"] = "../e.json"
        with self.assertRaises(ValueError): self.check()
        link = self.root / "artifacts" / "link.json"
        link.symlink_to(self.root / "artifacts" / "e.json")
        self.r["evidence"][0]["file"] = "link.json"
        with self.assertRaises(ValueError): self.check()
    def test_not_run(self):
        self.r["status"] = "NOT_RUN"
        with self.assertRaises(ValueError): self.check()
        self.r["metrics"] = {}
        self.r["evidence"] = []
        self.assertEqual(self.check()["artifact_bytes"],"NOT_RUN")
    def test_duplicate_json(self):
        path = self.root / "duplicate.json"
        path.write_text('{"id":1,"id":2}')
        with self.assertRaises(ValueError): reg.read_json(path)
    def test_missing_metrics(self):
        self.r["metrics"] = {}
        with self.assertRaises(ValueError): self.check()
    def test_demo(self):
        root = self.root / "new"
        self.assertEqual(demo(root)["reported_status"],"PASS")
        self.assertEqual(reg.verify(root,"EXP-DEMO-001")["artifact_bytes"],"MATCH")
        with self.assertRaises(FileExistsError): demo(root)

if __name__ == "__main__":
    unittest.main()
