import copy
import unittest
from unittest.mock import patch
from pathlib import Path
from engineering_lab import stage_closure as s

C="a"*40; M="b"*40; T="c"*40; A="d"*40
def fixture():
    paths=sorted(s.REQUIRED)
    refs=lambda start:[dict(id=start+i,attempt=1,path=p) for i,p in enumerate(paths)]
    return dict(schema=1,series="0.7",next_series="0.8",candidate_sha=C,reviewed_main_sha=M,
                candidate_runs=refs(1),main_runs=refs(11),
                adverse_runs=[dict(id=21,attempt=1,path=".github/workflows/qa.yml",sha=A)],
                review={k:"reviewed" for k in s.REVIEW},findings=[dict(id="AUD-STOP",severity="LOW",status="RESOLVED",summary="stop",evidence="test")],
                limitations=["synthetic"],rollback="revert")
def fake(m):
    def fetch(path):
        key=path.rsplit("/",1)[1]
        if key==C: return {"sha":C,"commit":{"tree":{"sha":T}}}
        if key==M: return {"sha":M,"commit":{"tree":{"sha":T}},"parents":[{"sha":A},{"sha":C}]}
        for group in ("candidate_runs","main_runs","adverse_runs"):
            for row in m[group]:
                if str(row["id"])==key:
                    return dict(id=row["id"],run_attempt=row["attempt"],path=row["path"],
                        head_sha=C if group=="candidate_runs" else M if group=="main_runs" else A,
                        repository={"full_name":s.REPO},head_repository={"full_name":s.REPO},
                        event="push" if group=="main_runs" else "pull_request",
                        head_branch="main" if group=="main_runs" else "audit",
                        status="completed",conclusion="failure" if group=="adverse_runs" else "success")
        raise AssertionError(path)
    return fetch
class ClosureTests(unittest.TestCase):
    def test_live_metadata_contract(self):
        m=fixture(); r=s.check(m,fake(m))
        self.assertEqual(r["reported_status"],"PASS"); self.assertEqual(len(r["runs"]),7)
        self.assertEqual(r["promotion"],"NOT_AUTHORIZED")
    def test_open(self):
        m=fixture(); m["findings"][0]["status"]="OPEN"
        self.assertEqual(s.check(m,lambda p:self.fail("no network on open findings"))["reported_status"],"BLOCKED")
    def test_missing_workflow(self):
        m=fixture(); m["main_runs"].pop()
        with self.assertRaises(ValueError): s.validate(m)
    def test_duplicate(self):
        m=fixture(); m["main_runs"][0]["id"]=m["candidate_runs"][0]["id"]
        with self.assertRaises(ValueError): s.validate(m)
    def test_skipped_series(self):
        m=fixture(); m["next_series"]="0.9"
        with self.assertRaises(ValueError): s.validate(m)
    def test_review_missing(self):
        m=fixture(); del m["review"]["rollback"]
        with self.assertRaises(ValueError): s.validate(m)
    def mutate(self,key,change):
        m=fixture(); base=fake(m)
        def fetch(path):
            r=base(path)
            if path.endswith("/"+key): change(r)
            return r
        with self.assertRaises(ValueError): s.check(m,fetch)
    def test_wrong_sha(self): self.mutate("1",lambda r:r.update(head_sha=A))
    def test_wrong_attempt(self): self.mutate("1",lambda r:r.update(run_attempt=2))
    def test_pending(self): self.mutate("11",lambda r:r.update(status="in_progress",conclusion=None))
    def test_wrong_workflow(self): self.mutate("1",lambda r:r.update(path=".github/workflows/other.yml"))
    def test_wrong_tree(self): self.mutate(M,lambda r:r["commit"]["tree"].update(sha=A))
    def test_wrong_parent(self): self.mutate(M,lambda r:r["parents"][1].update(sha=A))
    def test_wrong_repository(self): self.mutate("1",lambda r:r.update(head_repository={"full_name":"other/repo"}))
    def test_negative_not_erased(self): self.mutate("21",lambda r:r.update(conclusion="success"))
    def test_main_not_push(self): self.mutate("11",lambda r:r.update(event="pull_request"))
    def test_series_version(self):
        self.assertEqual(s.series("0.7.10"),"0.7")
        with self.assertRaises(ValueError): s.series("0.07.10")
    @patch("engineering_lab.stage_closure.version_at",return_value="0.7.10")
    @patch("engineering_lab.stage_closure.subprocess.run")
    @patch("engineering_lab.stage_closure.git")
    def test_coverage(self,git,run,version):
        run.return_value.returncode=0; git.return_value="audit/closures/0.7.json\0"
        s.coverage(Path("."),fixture(),M)
        git.return_value="engineering_lab/physics_core.py\0"
        with self.assertRaises(ValueError): s.coverage(Path("."),fixture(),M)
        run.return_value.returncode=1
        with self.assertRaises(ValueError): s.coverage(Path("."),fixture(),M)
    @patch("engineering_lab.stage_closure.version_at",side_effect=["0.7.10","0.7.11"])
    @patch("engineering_lab.stage_closure.git",side_effect=[C,"README.md\0"])
    def test_same_series(self,git,version):
        self.assertEqual(s.transition(Path("."),M)["gate"],"SAME_SERIES_NO_CLOSURE_REQUIRED")
    @patch("engineering_lab.stage_closure.version_at",side_effect=["0.7.10","0.9.0"])
    @patch("engineering_lab.stage_closure.git",side_effect=[C,"README.md\0"])
    def test_transition_skip(self,git,version):
        with self.assertRaises(ValueError): s.transition(Path("."),M)
if __name__=="__main__": unittest.main()
