import copy
import os
import unittest
from unittest.mock import patch
from engineering_lab import private_metadata as pm, code_evidence as ce
from test_code_intelligence import fixture
REPO="Jugadru/APEX-Engineering-Lab"; SHA="a"*40
def summ():
    return dict(game_sha=SHA,analyzer_blob="29a9c39e061b89f9e15126b265d880a40f3155a9",status="PASS",
                scripts=3,expected_scripts=3,rules={"APX003":2},certainty={"confirmed":2},error_count=0)
def profile():
    rows=[dict(weather=w,repeat=r,mean_us=1,p95_us=2,peak_static_bytes=4,end_over_start_ratio=1,simulated_seconds_per_wall_second=3) for w in ("dry","wet") for r in (1,2)]
    return dict(schema=1,game_sha=SHA,report=dict(status="PASS",track="LAB",cases=4,ticks_per_run=90,total_ticks=360,observations=rows,weather_hashes={"dry":"a"*64,"wet":"b"*64}))
class EvidenceTests(unittest.TestCase):
    def test_summary(self):
        x=ce.join(fixture(),summ())
        self.assertEqual(x["analyzer"]["diagnostic_count"],2)
        self.assertEqual(x["analyzer"]["per_file_attribution"],"NOT_AVAILABLE")
        self.assertEqual(x["native_promotion"],"NOT_AUTHORIZED")
    def test_summary_wrong_sha(self):
        s=summ(); s["game_sha"]="b"*40
        with self.assertRaises(ValueError): ce.join(fixture(),s)
    def test_summary_count(self):
        s=summ(); s["certainty"]["confirmed"]=1
        with self.assertRaises(ValueError): ce.join(fixture(),s)
    def test_profile(self):
        x=ce.join(fixture(),profile=profile())
        self.assertEqual(x["profile"]["function_profile"],"NOT_RUN")
        self.assertEqual(x["profile"]["fps"],"NOT_RUN")
    def test_bad_profile(self):
        p=profile(); p["report"]["observations"][0]["mean_us"]=float("nan")
        with self.assertRaises(ValueError): ce.join(fixture(),profile=p)
    def test_correlation(self):
        c=dict(schema=1,head=SHA,base="b"*40,state="FAILURE_EVIDENCE",failures=[dict(case="fixture.gd",status="FAIL",root_cause="NOT_ESTABLISHED",candidates=[])],planned_not_executed=["other.gd"])
        x=ce.join(fixture(),correlation=c)
        self.assertEqual(x["correlation"]["failures"][0]["root_cause"],"NOT_ESTABLISHED")
        self.assertEqual(x["gameplay_validation"],"NOT_RUN")
    def test_invalid_path(self):
        with self.assertRaises(ValueError): pm.managed_get("/repos/"+REPO+"/issues/1")
    def test_no_token(self):
        with patch.dict(os.environ,{"APEX_GITHUB_READ_TOKEN":""}):
            with self.assertRaises(ValueError): pm.managed_get("/repos/"+REPO+"/commits/"+SHA)
    def test_revision(self):
        self.assertEqual(pm.check(REPO,SHA,fetch=lambda p:{"sha":SHA})["status"],"REVISION_METADATA_MATCH")
    def test_other_repo(self):
        with self.assertRaises(ValueError): pm.check("example/repo",SHA,fetch=lambda p:None)
    def test_run_binding(self):
        def fetch(p):
            return {"sha":SHA} if "/commits/" in p else dict(id=3,head_sha=SHA,repository={"full_name":REPO},head_repository={"full_name":REPO},status="completed",conclusion="success",run_attempt=1)
        self.assertEqual(pm.check(REPO,SHA,3,fetch)["run_conclusion"],"success")
    def test_wrong_run(self):
        def fetch(p):
            return {"sha":SHA} if "/commits/" in p else dict(id=3,head_sha="b"*40)
        with self.assertRaises(ValueError): pm.check(REPO,SHA,3,fetch)
if __name__=="__main__": unittest.main()
