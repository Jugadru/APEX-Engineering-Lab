"""Consume the existing correlation report, never infer a root cause."""
from . import registry as reg, debugging as dbg, code_evidence

KINDS={"PARSE","RESOURCE","SCRIPT_RUNTIME","ASSERTION","ENGINE_ERROR","TIMEOUT",
       "EXECUTABLE_UNAVAILABLE","MISSING_MARKER","NONZERO_EXIT","INCOMPLETE_LOG","UNKNOWN"}
def project_path(p):
    return isinstance(p,str) and len(p)<=512 and "\\" not in p and not p.startswith("/") and all(x not in ("",".","..") for x in p.split("/"))

def classify(root,ident,filename,case_name):
    c=dbg.load_case(root,ident)
    reg.require(c["kind"]=="observed_failure","classification requires observed failure")
    refs={e["file"]:e["sha256"] for e in c["evidence"]}
    reg.require(filename in refs,"correlation report must be registered case evidence")
    report=reg.read_json(root/"artifacts"/filename)
    code_evidence.correlation_check(report,c["sha"])
    rows=[x for x in report["failures"] if x["case"]==case_name]
    reg.require(len(rows)==1,"unique matching failed case required")
    r=rows[0]
    reg.require(r["kind"] in KINDS and type(r["log_partial"]) is bool,"classification")
    locations=r["locations"]
    reg.require(isinstance(locations,list) and len(locations)<=8,"locations")
    for loc in locations:
        reg.exact(loc,"file line")
        reg.require(project_path(loc["file"]) and (loc["line"] is None or type(loc["line"]) is int and loc["line"]>0),"location")
    candidates=r["candidates"]
    reg.require(len(candidates)<=20 and type(r["candidate_count"]) is int and r["candidate_count"]>=len(candidates),"candidate count")
    for x in candidates:
        reg.exact(x,"file relation path")
        reg.require(project_path(x["file"]) and x["relation"] in {"direct_path_match","literal_dependency","literal_consumer"} and isinstance(x["path"],list) and 1<=len(x["path"])<=4 and all(project_path(p) for p in x["path"]) and x["path"][-1]==x["file"],"candidate path")
    fingerprint=reg.digest({"repository":c["repository"],"domain":c["domain"],"case":case_name,"kind":r["kind"],"paths":sorted({x["file"] for x in locations})})
    return {"schema":1,"id":ident,"case_sha256":reg.digest(c),"sha":c["sha"],"source_file":filename,
            "source_sha256":refs[filename],"case":case_name,"classification":r["kind"],"observed_status":r["status"],
            "fingerprint":fingerprint,"locations":locations,"candidates":candidates,"partial_log":r["log_partial"],
            "root_cause":"NOT_ESTABLISHED","promotion":"NOT_AUTHORIZED",
            "next_action":"Inspect original log and existing targeted fixture; do not retry blindly."}

def record(root,ident,filename,case_name):
    result=classify(root,ident,filename,case_name)
    reg.publish_once(root/(ident+".classification.json"),result)
    return result

def load(root,ident):
    dbg.case_id(ident)
    stored=reg.read_json(root/(ident+".classification.json"))
    fresh=classify(root,ident,stored["source_file"],stored["case"])
    reg.require(stored==fresh,"classification changed")
    return fresh

def history(root,fingerprint):
    reg.valid_root(root)
    reg.require(reg.sha64(fingerprint),"fingerprint")
    paths=sorted(root.glob("BUG-*.classification.json"))
    reg.require(len(paths)<=1000,"history limit")
    matches=[]
    for p in paths:
        ident=p.name.removesuffix(".classification.json")
        r=load(root,ident)
        if r["fingerprint"]==fingerprint:
            matches.append({"id":ident,"sha":r["sha"],"observed_status":r["observed_status"]})
    return {"matches":matches,"interpretation":"Similar classification and locations, not proof of same root cause."}
