import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from engineering_lab import registry as reg, provenance as prov

class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "artifacts").mkdir()
        # Opaque archive bytes for digest matching only; no extraction or parsing.
        data = b"synthetic archive fixture"
        (self.root / "artifacts" / "fixture.zip").write_bytes(data)
        self.p = dict(schema=1, id="EXP-PROV-001", peer="lab_hub", hypothesis="fixture",
                      scope="synthetic tests of metadata adapter", sources=[], repository=prov.LAB,
                      candidate_sha="a"*40, lab_sha="b"*40, baseline_sha="c"*40, kind="unit",
                      workload=dict(environment="offline", scenario="fixture", seed=None, ticks=None,
                                    command_hash=None, authorization="offline_only"),
                      criteria={"count":dict(op="eq",threshold=1,unit="count")})
        self.r = dict(schema=1,id=self.p["id"],plan_sha256=reg.digest(self.p),candidate_sha=self.p["candidate_sha"],
                      lab_sha=self.p["lab_sha"],status="PASS",metrics={"count":1},
                      evidence=[dict(file="fixture.zip",sha256=reg.checksum(data))],limitations="fixture only")
        reg.register_plan(self.root,self.p)
        reg.register_result(self.root,self.r)
        self.d = dict(schema=1,id=self.p["id"],result_sha256=reg.digest(self.r),origin="github_actions",
                      run=dict(repository=prov.LAB,id=17,attempt=2),
                      archives=[dict(artifact_id=21,file="fixture.zip")],limitations="test fixture")
        self.live = dict(id=17,run_attempt=2,head_sha=self.p["candidate_sha"],status="completed",
                         conclusion="success",repository=dict(full_name=prov.LAB),head_repository=dict(full_name=prov.LAB))
        self.artifact = dict(id=21,expired=False,workflow_run=dict(id=17,head_sha=self.p["candidate_sha"]),
                             digest="sha256:"+reg.checksum(data))
        self.calls = []
    def fetch(self,path):
        self.calls.append(path)
        if "/commits/" in path:
            return {"sha":path.rsplit("/",1)[-1]}
        if path.endswith("/runs/17"):
            return copy.deepcopy(self.live)
        if path.endswith("/artifacts/21"):
            return copy.deepcopy(self.artifact)
        raise AssertionError(path)
    def declare(self):
        return prov.declare(self.root,self.d)
    def check(self):
        self.declare()
        return prov.github_check(self.root,self.p["id"],self.fetch)
    def test_declared_only(self):
        out=self.declare()
        self.assertEqual(out["provenance"],"DECLARED_ONLY")
        self.assertEqual(out["maturity"],"EXPERIMENTAL")
        self.assertEqual(out["promotion"],"NOT_AUTHORIZED")
        self.assertEqual(self.calls,[])
    def test_live_match(self):
        out=self.check()
        self.assertEqual(out["archive_digest_coverage"],"ALL")
        self.assertEqual(out["review_readiness"],"EVIDENCE_FOR_REVIEW")
        self.assertEqual(out["scientific_review"],"NOT_PERFORMED")
        self.assertEqual(out["maturity"],"EXPERIMENTAL")
        self.assertEqual(len(self.calls),5)
    def test_wrong_attempt(self):
        self.live["run_attempt"]=1
        with self.assertRaises(ValueError): self.check()
    def test_wrong_head(self):
        self.live["head_sha"]="f"*40
        with self.assertRaises(ValueError): self.check()
    def test_fork(self):
        self.live["head_repository"]["full_name"]="example/fork"
        with self.assertRaises(ValueError): self.check()
    def test_incomplete(self):
        self.live["status"]="in_progress"
        with self.assertRaises(ValueError): self.check()
    def test_wrong_digest(self):
        self.artifact["digest"]="sha256:"+"0"*64
        with self.assertRaises(ValueError): self.check()
    def test_wrong_artifact_run(self):
        self.artifact["workflow_run"]["id"]=99
        with self.assertRaises(ValueError): self.check()
    def test_expired_artifact(self):
        self.artifact["expired"]=True
        with self.assertRaises(ValueError): self.check()
    def test_missing_digest(self):
        self.artifact.pop("digest")
        with self.assertRaises(ValueError): self.check()
    def test_metadata_without_archives(self):
        self.d["archives"]=[]
        out=self.check()
        self.assertEqual(out["archive_digest_coverage"],"NONE")
        self.assertEqual(out["review_readiness"],"INSUFFICIENT")
    def test_workflow_failure_separate(self):
        self.live["conclusion"]="failure"
        out=self.check()
        self.assertEqual(out["reported_status"],"PASS")
        self.assertEqual(out["review_readiness"],"INSUFFICIENT")
    def test_synthetic(self):
        self.d.update(origin="synthetic",run=None,archives=[])
        self.declare()
        with self.assertRaises(ValueError): prov.github_check(self.root,self.p["id"],self.fetch)
        self.assertEqual(self.calls,[])
    def test_wrong_result(self):
        self.d["result_sha256"]="0"*64
        with self.assertRaises(ValueError): self.declare()
    def test_no_overwrite(self):
        self.declare()
        with self.assertRaises(FileExistsError): self.declare()
    def test_reject_non_allowlisted_repo(self):
        self.d["run"]["repository"]="example/other"
        with self.assertRaises(ValueError): self.declare()
    def test_tampered_bytes(self):
        self.declare()
        (self.root/"artifacts"/"fixture.zip").write_bytes(b"wrong")
        with self.assertRaises(ValueError): prov.github_check(self.root,self.p["id"],self.fetch)
    def test_receipt_untrusted(self):
        self.declare()
        with patch.object(prov,"github_check",side_effect=lambda root, ident: self.original_check(root,ident,self.fetch)):
            prov.save_receipt(self.root,self.p["id"])
            with self.assertRaises(FileExistsError): prov.save_receipt(self.root,self.p["id"])
        out=prov.read_receipt(self.root,self.p["id"])
        self.assertEqual(out["receipt_status"],"LOCAL_SNAPSHOT_UNAUTHENTICATED")
        self.assertEqual(out["provenance"],"DECLARED_ONLY")
        self.assertEqual(out["live_recheck"],"REQUIRED")
    original_check=staticmethod(prov.github_check)
    def test_wrong_revision(self):
        self.declare()
        def fetch(path):
            if "/commits/" in path: return {"sha":"0"*40}
            return self.fetch(path)
        with self.assertRaises(ValueError): prov.github_check(self.root,self.p["id"],fetch)
    def test_duplicate_archive(self):
        self.d["archives"].append(copy.deepcopy(self.d["archives"][0]))
        with self.assertRaises(ValueError): self.declare()

if __name__=="__main__":
    unittest.main()
