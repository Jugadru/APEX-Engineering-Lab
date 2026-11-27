"""Bounded, review-only candidate comparison using existing scientific evidence."""
from . import registry as reg, debugging as dbg, reproduction as rp, bug_intelligence as bi

def validate(root,ident,proposal):
    c=dbg.load_case(root,ident)
    baseline=rp.check(root,ident)
    reg.require(baseline["status"]=="MATCHING_FAILURE_OBSERVED","matching baseline failure required")
    link,p=rp.load(root,ident)
    reg.exact(proposal,"schema id case_sha256 baseline_result_sha256 hypotheses")
    reg.require(proposal["schema"]==1 and proposal["id"]==ident and proposal["case_sha256"]==reg.digest(c) and proposal["baseline_result_sha256"]==baseline["result_sha256"],"proposal binding")
    rows=proposal["hypotheses"]
    reg.require(isinstance(rows,list) and 1<=len(rows)<=2,"one or two hypotheses")
    ids=set(); exps=set(); shas=set(); plans=[]
    for r in rows:
        reg.exact(r,"id statement falsifier files experiment plan_sha256 rollback")
        reg.require(reg.match(r["id"],r"H-[1-2]") and r["id"] not in ids,"hypothesis identity")
        ids.add(r["id"])
        reg.require(all(reg.nonempty(r[k]) for k in ("statement","falsifier","rollback")),"hypothesis text")
        reg.require(isinstance(r["files"],list) and 1<=len(r["files"])<=20 and all(bi.project_path(x) for x in r["files"]) and len(set(r["files"]))==len(r["files"]),"candidate files")
        exp=reg.experiment_id(r["experiment"])
        reg.require(exp not in exps and exp!=p["id"],"unique candidate experiment")
        exps.add(exp)
        q=reg.read_json(root/(exp+".plan.json")); reg.validate_plan(q)
        reg.require(q["id"]==exp and r["plan_sha256"]==reg.digest(q),"candidate plan binding")
        reg.require(q["candidate_sha"]!=c["sha"] and q["candidate_sha"] not in shas and q["baseline_sha"]==c["sha"],"distinct candidate revision")
        shas.add(q["candidate_sha"])
        for k in ("repository","lab_sha","kind","workload","criteria","peer"):
            reg.require(q[k]==p[k],"noncomparable candidate: "+k)
        plans.append(q)
    return c,baseline,p,plans

def bind(root,ident,proposal):
    _,_,_,plans=validate(root,ident,proposal)
    reg.require(all(not (root/(p["id"]+".result.json")).exists() for p in plans),"bind before candidate observation")
    reg.publish_once(root/(ident+".solution.json"),proposal)
    return {"id":ident,"proposal_sha256":reg.digest(proposal),"status":"PROPOSED_NOT_RUN","promotion":"NOT_AUTHORIZED"}

def evaluate(root,ident):
    dbg.case_id(ident)
    proposal=reg.read_json(root/(ident+".solution.json"))
    c,baseline,p,plans=validate(root,ident,proposal)
    results=[]
    for h,q in zip(proposal["hypotheses"],plans):
        path=root/(q["id"]+".result.json")
        row={"hypothesis":h["id"],"statement":h["statement"],"falsifier":h["falsifier"],
             "candidate_sha":q["candidate_sha"],"experiment":q["id"],"plan_sha256":reg.digest(q),
             "files":h["files"],"rollback":h["rollback"],"status":"NOT_RUN"}
        if path.exists():
            s=reg.verify(root,q["id"]); raw=reg.read_json(path)
            status=s["reported_status"]
            row.update(result_sha256=s["result_sha256"],metrics=raw["metrics"],
                       status="REVIEW_CANDIDATE" if status=="PASS" else status,artifact_bytes=s["artifact_bytes"])
        results.append(row)
    return {"id":ident,"repository":c["repository"],"baseline_sha":c["sha"],
            "baseline_result_sha256":baseline["result_sha256"],"proposal_sha256":reg.digest(proposal),
            "candidates":results,"root_cause":"NOT_ESTABLISHED",
            "gameplay_validation":"NOT_RUN","authenticity":"NOT_VERIFIED","promotion":"NOT_AUTHORIZED",
            "next_action":"Review diff, original evidence, rollback and target CI; no automatic merge or patch."}

def demo(root):
    rp.demo(root)
    ident="BUG-REPRO-DEMO"; c=dbg.load_case(root,ident)
    _,p=rp.load(root,ident)
    q=dict(p,id="EXP-SOLUTION-DEMO",candidate_sha="c"*40,hypothesis="Remove artificial offset")
    reg.register_plan(root,q)
    proposal=dict(schema=1,id=ident,case_sha256=reg.digest(c),baseline_result_sha256=rp.check(root,ident)["result_sha256"],
                  hypotheses=[dict(id="H-1",statement="Remove artificial offset",falsifier="Sum differs from 55",
                                   files=["synthetic_fixture.py"],experiment=q["id"],plan_sha256=reg.digest(q),rollback="Restore prior synthetic expression")])
    bind(root,ident,proposal)
    measured=sum(range(1,11))
    data=reg.canonical({"observed":measured,"origin":"synthetic"})
    (root/"artifacts/candidate.json").write_bytes(data)
    reg.register_result(root,dict(schema=1,id=q["id"],plan_sha256=reg.digest(q),candidate_sha=q["candidate_sha"],lab_sha=q["lab_sha"],
                                  status="PASS" if measured==55 else "FAIL",metrics={"sum":measured},
                                  evidence=[dict(file="candidate.json",sha256=reg.checksum(data))],limitations="Synthetic expression only; no production patch."))
    return evaluate(root,ident)
