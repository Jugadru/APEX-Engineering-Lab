"""Evidence-bound scientific report views; no re-execution or promotion."""
from pathlib import Path
from . import registry as reg
from .experimental import REPO

def report(root,ident):
    reg.valid_root(root); reg.experiment_id(ident)
    p=reg.read_json(root/(ident+".plan.json")); ph=reg.validate_plan(p)
    reg.require(p["id"]==ident and p["repository"]==REPO and p["candidate_sha"]==p["lab_sha"]==p["baseline_sha"]
                and p["kind"]=="fixture" and p["workload"]["authorization"]=="offline_only","experimental plan binding")
    config=reg.read_json(root/"configuration.json")
    reg.require(isinstance(config,dict) and reg.digest(config)==p["workload"]["command_hash"]
                and config.get("seed")==p["workload"]["seed"],"configuration binding")
    out={"id":ident,"experiment":p["workload"]["scenario"],"revision":p["lab_sha"],"hypothesis":p["hypothesis"],
         "scope":p["scope"],"sources":p["sources"],"configuration":config,"plan_sha256":ph,
         "origin":"SYNTHETIC","authenticity":"NOT_VERIFIED","promotion":"NOT_AUTHORIZED",
         "scientific_validation":"NOT_PERFORMED","gameplay_validation":"NOT_RUN"}
    path=root/(ident+".result.json")
    if not path.exists():
        return {**out,"reported_status":"NOT_RUN","artifact_bytes":"NOT_RUN","metrics":[],
                "observations":{},"limitations":"Frozen plan only; no completed result."}
    summary=reg.verify(root,ident); r=reg.read_json(path)
    status=r["status"]
    rows=[{"metric":k,"unit":rule["unit"],"op":rule["op"],"threshold":rule["threshold"],
           "observed":r["metrics"].get(k),"criterion_met":summary["checks"].get(k)}
          for k,rule in sorted(p["criteria"].items())]
    obs={}
    if status in {"PASS","FAIL"}:
        reg.require(len(r["evidence"])==1 and r["evidence"][0]["file"]=="observations.json","unexpected experimental artifact")
        a=reg.read_json(root/"artifacts"/"observations.json")
        reg.exact(a,"schema experiment revision plan_sha256 configuration metrics observations origin promotion")
        reg.require(a["schema"]==1 and a["experiment"]==out["experiment"] and a["revision"]==out["revision"]
                    and a["plan_sha256"]==ph and a["configuration"]==config and a["metrics"]==r["metrics"]
                    and a["origin"]=="SYNTHETIC" and a["promotion"]=="NOT_AUTHORIZED"
                    and isinstance(a["observations"],dict),"observation binding")
        obs=a["observations"]
    return {**out,"reported_status":status,"artifact_bytes":summary["artifact_bytes"],
            "result_sha256":summary["result_sha256"],"metrics":rows,"observations":obs,"limitations":r["limitations"]}

def suite(entries):
    reg.require(isinstance(entries,list) and 1<=len(entries)<=20,"suite size")
    rows=[report(Path(path),ident) for path,ident in entries]
    reg.require(len({r["revision"] for r in rows})==1,"mixed revisions")
    reg.require(len({r["id"] for r in rows})==len(rows) and len({r["experiment"] for r in rows})==len(rows),"duplicate experiment")
    counts={s:sum(r["reported_status"]==s for r in rows) for s in sorted(reg.STATUSES)}
    status="FAIL" if counts["FAIL"] else "PASS" if counts["PASS"]==len(rows) else "INCONCLUSIVE"
    return {"schema":1,"revision":rows[0]["revision"],"origin":"SYNTHETIC","reported_status":status,
            "counts":counts,"experiments":rows,"scientific_validation":"NOT_PERFORMED",
            "authenticity":"NOT_VERIFIED","promotion":"NOT_AUTHORIZED","gameplay_validation":"NOT_RUN",
            "limitations":"Only supplied entries are summarized; no claim of complete coverage, independent scientific review, CPU speedup or FPS."}

def markdown(s):
    lines=["# APEX Experimental Engineering — scientific evidence report","",
           "Revision: "+s["revision"],"","Status: "+s["reported_status"]+" (supplied synthetic criteria only).",
           "",s["limitations"],"","| Experiment | Status |","|---|---|"]
    for r in s["experiments"]:
        # Code-formatted identifiers only after conservative display escaping.
        name=r["experiment"].replace("|","/").replace("\n"," ").replace("\r"," ")
        lines.append("| "+name+" | "+r["reported_status"]+" |")
    for r in s["experiments"]:
        lines.extend(["","## "+r["id"],"",r["hypothesis"],"",
                      "Plan SHA-256: "+r["plan_sha256"],"","| Metric | Observed | Criterion | Unit | Met |",
                      "|---|---:|---|---|---|"])
        for m in r["metrics"]:
            unit=m["unit"].replace("|","/").replace("\n"," ").replace("\r"," ")
            lines.append("| {metric} | {observed} | {op} {threshold} | {unit} | {criterion_met} |".format(**{**m,"unit":unit}))
        lines.extend(["",r["limitations"]])
    return "\n".join(lines)+"\n"
