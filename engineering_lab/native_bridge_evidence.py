"""Read-only native comparison; matching scenario inputs is not model parity."""
import argparse
import json
from pathlib import Path
import re

CORE_SHA="2171247db6824331b714dc2588cda15b4b60a496"
HYPER_SHA="4e4e75f96f94ce4487e7a3c37862aabcbba649ef"
CASES=[("ITA","Seco"),("GBR","Chuva intensa")]

def load(path):
    lines=Path(path).read_text(encoding="utf-8").splitlines()
    if any(re.search(r"SCRIPT ERROR:|Parse Error:|^ERROR:",x) for x in lines):
        raise ValueError("native errors in "+str(path))
    rows=[json.loads(x.split("APEX_BRIDGE_RESULT ",1)[1]) for x in lines if x.startswith("APEX_BRIDGE_RESULT ")]
    if len(rows)!=1:
        raise ValueError("expected one native result")
    return rows[0]

def compare(core,hyper):
    if core["engine"]!="Core2" or hyper["engine"]!="Hyper301":
        raise ValueError("engine identity")
    for report in (core,hyper):
        if [(r["track"],r["weather"]) for r in report["rows"]]!=CASES:
            raise ValueError("scenario roster")
    out=[]
    for a,b in zip(core["rows"],hyper["rows"]):
        for x in (a,b):
            if (x["seed"],x["ticks"],x["elapsed_sim_ms"],x["commands"])!=(2026,100,20000,[]):
                raise ValueError("scenario contract")
            ids=[c["id"] for c in x["initial"]]
            if len(ids)!=24 or ids!=sorted(set(ids)) or ids!=[c["id"] for c in x["final"]]:
                raise ValueError("car identities")
            if not re.fullmatch("[0-9a-f]{64}",x["hash"]) or x["elapsed_cpu_usec"]<=0:
                raise ValueError("invalid native evidence")
            if any(type(c["progress_units"]) is not int for c in x["final"]):
                raise ValueError("progress must be integer")
        if a["initial"]!=b["initial"] or a["length_mm"]!=b["length_mm"]:
            raise ValueError("initial scenario differs: do not compare")
        deltas=[y["progress_units"]-x["progress_units"] for x,y in zip(a["final"],b["final"])]
        out.append(dict(track=a["track"],weather=a["weather"],seed=2026,ticks=100,
                        initial_roster_match=True,clock_match=True,
                        max_abs_progress_delta_units=max(map(abs,deltas)),
                        core_hash=a["hash"],hyper_hash=b["hash"],
                        core_cpu_usec=a["elapsed_cpu_usec"],hyper_cpu_usec=b["elapsed_cpu_usec"],
                        model_equivalence="NOT_ESTABLISHED",lab_launch="BLOCKED_NO_LAUNCH_MODEL"))
    return dict(status="PASS",kind="NATIVE_INPUT_AND_DIFFERENCE_AUDIT",core_sha=CORE_SHA,
                hyper_sha=HYPER_SHA,rows=out,model_equivalence="NOT_ESTABLISHED",promotion="NOT_AUTHORIZED",
                limitations="Shared public scenario and initial roster only; internal physics, autonomous commands, clocks beyond sample and results are not equivalent. CPU times are descriptive, not a speed ranking.")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("core");p.add_argument("hyper");p.add_argument("output")
    a=p.parse_args()
    result=compare(load(a.core),load(a.hyper))
    Path(a.output).write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
