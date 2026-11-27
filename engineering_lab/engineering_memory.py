"""Searchable, immutable lessons tied to prior investigations; not autonomous learning."""
import unicodedata
from . import registry as reg, debugging as dbg, bug_intelligence as bi, reproduction as rp, solution as sol

def memory_id(value):
    reg.require(reg.match(value,r"MEM-[A-Z0-9-]{1,60}"),"memory ID")
    return value

def normalize(s):
    return "".join(c for c in unicodedata.normalize("NFKD",s.casefold()) if not unicodedata.combining(c))

def snapshot(root,ident):
    c=dbg.load_case(root,ident)
    out={"case_sha256":reg.digest(c),"repository":c["repository"],"sha":c["sha"],"domain":c["domain"],
         "kind":c["kind"],"title":c["title"],"classification":None,"reproduction":None,"solution":None}
    if (root/(ident+".classification.json")).exists():
        x=bi.load(root,ident)
        out["classification"]={"sha256":reg.digest(x),"fingerprint":x["fingerprint"],"kind":x["classification"]}
    if (root/(ident+".reproduction.json")).exists():
        x=rp.check(root,ident)
        out["reproduction"]={"status":x["status"],"plan_sha256":x["plan_sha256"],"result_sha256":x.get("result_sha256")}
    if (root/(ident+".solution.json")).exists():
        x=sol.evaluate(root,ident)
        out["solution"]={"proposal_sha256":x["proposal_sha256"],"candidates":[
            {"hypothesis":r["hypothesis"],"candidate_sha":r["candidate_sha"],"status":r["status"],
             "plan_sha256":r["plan_sha256"],"result_sha256":r.get("result_sha256")} for r in x["candidates"]]}
    return out

def validate_input(x):
    reg.exact(x,"schema id case lesson tags limitations")
    reg.require(type(x["schema"]) is int and x["schema"]==1,"memory schema")
    memory_id(x["id"]); dbg.case_id(x["case"])
    reg.require(reg.nonempty(x["lesson"]) and reg.nonempty(x["limitations"]),"lesson/limits")
    tags=x["tags"]
    reg.require(isinstance(tags,list) and 1<=len(tags)<=15 and all(reg.nonempty(t) and len(t)<=64 for t in tags)
                and len(set(map(normalize,tags)))==len(tags),"tags")

def record(root,x):
    reg.valid_root(root); validate_input(x)
    s=snapshot(root,x["case"])
    out={"input":x,"snapshot":s,"snapshot_sha256":reg.digest(s),"promotion":"NOT_AUTHORIZED",
         "scientific_review":"NOT_PERFORMED"}
    reg.publish_once(root/(x["id"]+".memory.json"),out)
    return read(root,x["id"])

def read(root,ident):
    reg.valid_root(root); memory_id(ident)
    r=reg.read_json(root/(ident+".memory.json"))
    reg.exact(r,"input snapshot snapshot_sha256 promotion scientific_review")
    x=r["input"]; validate_input(x)
    reg.require(x["id"]==ident and r["snapshot_sha256"]==reg.digest(r["snapshot"]) and
                r["promotion"]=="NOT_AUTHORIZED" and r["scientific_review"]=="NOT_PERFORMED","memory binding")
    old=r["snapshot"]; current=snapshot(root,x["case"])
    reg.exact(old,"case_sha256 repository sha domain kind title classification reproduction solution")
    for k in ("case_sha256","repository","sha","domain","kind","title"):
        reg.require(old[k]==current[k],"case history changed")
    if old["classification"] is not None:
        reg.require(old["classification"]==current["classification"],"classification history changed")
    if old["reproduction"] is not None:
        a=old["reproduction"]; b=current["reproduction"]
        reg.require(b is not None and a["plan_sha256"]==b["plan_sha256"],"reproduction plan changed")
        if a["result_sha256"] is not None: reg.require(a==b,"reproduction history changed")
        else: reg.require(a["status"]=="NOT_RUN","invalid unrun snapshot")
    if old["solution"] is not None:
        a=old["solution"]; b=current["solution"]
        reg.require(b is not None and a["proposal_sha256"]==b["proposal_sha256"] and len(a["candidates"])==len(b["candidates"]),"proposal history changed")
        for x,y in zip(a["candidates"],b["candidates"]):
            reg.require(all(x[k]==y[k] for k in ("hypothesis","candidate_sha","plan_sha256")),"candidate changed")
            if x["result_sha256"] is not None: reg.require(x==y,"candidate history changed")
            else: reg.require(x["status"]=="NOT_RUN","invalid unrun candidate")
    return {**r,"id":ident,"new_evidence_available":old!=current,"authenticity":"LOCAL_UNAUTHENTICATED"}

def historical(data):
    reg.exact(data,"schema entries")
    reg.require(data["schema"]==1 and isinstance(data["entries"],list) and len(data["entries"])<=100,"historical schema")
    seen=set()
    for x in data["entries"]:
        reg.exact(x,"id domain title lesson tags limitations repository baseline_sha target_sha observations")
        reg.require(reg.match(x["id"],r"HIST-[A-Z0-9-]{1,60}") and x["id"] not in seen,"history ID")
        seen.add(x["id"])
        reg.require(x["repository"]=="Jugadru/apex-godot-simulation-architect" and reg.sha40(x["baseline_sha"]) and reg.sha40(x["target_sha"]),"history revisions")
        reg.require(all(reg.nonempty(x[k]) for k in ("title","lesson","limitations","domain")) and isinstance(x["tags"],list) and all(reg.nonempty(t) for t in x["tags"]),"history text")
        reg.require(isinstance(x["observations"],list) and 1<=len(x["observations"])<=20,"observations")
        for o in x["observations"]:
            reg.exact(o,"run_id producer_sha status scripts expected errors")
            reg.require(type(o["run_id"]) is int and o["run_id"]>0 and reg.sha40(o["producer_sha"]) and o["status"] in reg.STATUSES
                        and all(type(o[k]) is int and o[k]>=0 for k in ("scripts","expected","errors")) and o["scripts"]<=o["expected"],"historical observation")
            if o["status"]=="PASS": reg.require(o["scripts"]==o["expected"] and o["errors"]==0,"historical PASS contradiction")
    return data["entries"]

def search(root,query,history=None,limit=20):
    reg.valid_root(root)
    reg.require(reg.nonempty(query) and len(query)<=200 and type(limit) is int and 1<=limit<=100,"search limits")
    tokens=normalize(query).split()
    rows=[]
    def add(row,text):
        hay=normalize(text)
        if all(t in hay for t in tokens):
            rows.append({**row,"score":sum(hay.count(t) for t in tokens)})
    paths=sorted(root.glob("MEM-*.memory.json")); reg.require(len(paths)<=1000,"memory limit")
    for p in paths:
        x=read(root,p.name.removesuffix(".memory.json")); a=x["input"]; s=x["snapshot"]
        add({"id":x["id"],"origin":"LOCAL_INVESTIGATION","title":s["title"],"lesson":a["lesson"],"domain":s["domain"],
             "new_evidence_available":x["new_evidence_available"],"promotion":"NOT_AUTHORIZED"},
            " ".join([s["title"],a["lesson"],s["domain"],s["repository"],*a["tags"]]))
    if history is not None:
        for x in historical(history):
            add({"id":x["id"],"origin":"HISTORICAL_DOCUMENTARY","title":x["title"],"lesson":x["lesson"],"domain":x["domain"],
                 "promotion":"NOT_AUTHORIZED"}," ".join([x["title"],x["lesson"],x["domain"],*x["tags"]]))
    return {"matches":sorted(rows,key=lambda x:(-x["score"],x["id"]))[:limit],"total":len(rows),
            "interpretation":"Lexical retrieval; evidence and relevance require review; no autonomous model training."}

def demo(root):
    sol.demo(root)
    return record(root,dict(schema=1,id="MEM-DEMO-001",case="BUG-REPRO-DEMO",
                 lesson="A deliberate arithmetic offset was reproduced; the corrected synthetic expression passed the frozen criterion.",
                 tags=["arithmetic","synthetic","regression"],limitations="No game code or real fix."))
