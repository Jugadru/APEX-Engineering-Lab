"""Bind a predeclared reproduction to existing scientific registry evidence."""
from . import registry as reg, debugging as dbg

def validate(root,ident,link):
    c=dbg.load_case(root,ident)
    reg.exact(link,"schema id case_sha256 experiment failure_metric failure_value fixture budget_minutes")
    reg.require(link["schema"]==1 and link["id"]==ident and link["case_sha256"]==reg.digest(c),"case binding")
    reg.require(c["kind"] in {"observed_failure","synthetic","user_report"},"static signal is not a reproduced failure")
    exp=reg.experiment_id(link["experiment"])
    p=reg.read_json(root/(exp+".plan.json")); reg.validate_plan(p)
    reg.require(p["id"]==exp and p["repository"]==c["repository"] and p["candidate_sha"]==c["sha"] and p["baseline_sha"]==c["sha"],"baseline revision")
    reg.require(p["kind"] in {"unit","fixture"} and p["workload"]["authorization"] in {"offline_only","hosted_reviewed"},"bounded reproduction only")
    reg.require(type(link["budget_minutes"]) is int and 1<=link["budget_minutes"]<=15 and reg.nonempty(link["fixture"]),"fixture budget")
    m=link["failure_metric"]; v=link["failure_value"]
    reg.require(m in p["criteria"] and reg.numeric(v) and not reg.check(p["criteria"][m],v),"declared failure must violate criterion")
    reg.require(p["workload"]["seed"] is not None and p["workload"]["command_hash"] is not None,"freeze seed and command digest")
    return p
def bind(root,ident,link):
    p=validate(root,ident,link)
    reg.require(not (root/(p["id"]+".result.json")).exists(),"bind before observing result")
    reg.publish_once(root/(ident+".reproduction.json"),link)
    return {"id":ident,"experiment":p["id"],"plan_sha256":reg.digest(p),"status":"PLANNED_NOT_RUN","execution":"EXTERNAL_REVIEWED_FIXTURE_ONLY"}
def load(root,ident):
    dbg.case_id(ident)
    link=reg.read_json(root/(ident+".reproduction.json"))
    p=validate(root,ident,link)
    return link,p
def check(root,ident):
    link,p=load(root,ident)
    result_path=root/(p["id"]+".result.json")
    if not result_path.exists():
        return {"id":ident,"status":"NOT_RUN","plan_sha256":reg.digest(p),"promotion":"NOT_AUTHORIZED"}
    s=reg.verify(root,p["id"]); r=reg.read_json(result_path)
    if r["status"]=="FAIL" and r["metrics"].get(link["failure_metric"])==link["failure_value"]:
        state="MATCHING_FAILURE_OBSERVED"
    elif r["status"]=="PASS": state="NOT_REPRODUCED"
    elif r["status"]=="FAIL": state="DIFFERENT_FAILURE"
    else: state=r["status"]
    return {"id":ident,"status":state,"experiment":p["id"],"plan_sha256":s["plan_sha256"],"result_sha256":s["result_sha256"],
            "artifact_bytes":s["artifact_bytes"],"root_cause":"NOT_ESTABLISHED","authenticity":"NOT_VERIFIED","promotion":"NOT_AUTHORIZED"}

def demo(root):
    """Execute a deliberately defective, bounded arithmetic fixture, not game code."""
    root.mkdir(mode=0o700); (root/"artifacts").mkdir(mode=0o700)
    c=dict(schema=1,id="BUG-REPRO-DEMO",repository="example/synthetic",sha="a"*40,domain="quality",kind="synthetic",
           title="Deliberate arithmetic offset",symptom="Sum reduced by one",expected="55",observed="54",evidence=[],limitations="Synthetic fixture; fictitious revisions.")
    dbg.open_case(root,c)
    p=dict(schema=1,id="EXP-REPRO-DEMO",peer="lab_hub",hypothesis="Deliberate offset violates sum contract",scope="Synthetic arithmetic only",sources=[],
           repository=c["repository"],candidate_sha=c["sha"],baseline_sha=c["sha"],lab_sha="b"*40,kind="fixture",
           workload=dict(environment="Python standard library",scenario="sum 1..10, fixed arithmetic fixture",seed=0,ticks=None,
                         command_hash=reg.checksum(b"sum-fixture-v1"),authorization="offline_only"),criteria={"sum":dict(op="eq",threshold=55,unit="count")})
    reg.register_plan(root,p)
    link=dict(schema=1,id=c["id"],case_sha256=reg.digest(c),experiment=p["id"],failure_metric="sum",failure_value=54,fixture="synthetic sum",budget_minutes=1)
    bind(root,c["id"],link)
    measured=sum(range(1,11))-1
    data=reg.canonical({"observed":measured,"origin":"synthetic"})
    (root/"artifacts/baseline.json").write_bytes(data)
    reg.register_result(root,dict(schema=1,id=p["id"],plan_sha256=reg.digest(p),candidate_sha=p["candidate_sha"],lab_sha=p["lab_sha"],status="FAIL",
                                  metrics={"sum":measured},evidence=[dict(file="baseline.json",sha256=reg.checksum(data))],limitations="Deliberate synthetic failure."))
    return check(root,c["id"])
