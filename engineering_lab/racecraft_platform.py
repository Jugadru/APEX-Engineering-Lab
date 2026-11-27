"""Exact legacy replay and numeric portable evidence for steering paths."""
import argparse
import json
import math
from pathlib import Path
from . import racecraft_unified as u, physics_vehicle as v, registry as reg
from . import racecraft_yaw as y, racecraft_oriented as o, racecraft_control_refine as refinement

ABS_TOL=1e-9
REL_TOL=1e-12

def record():
    fixture=u.evaluate(u.spec(lambda *args: None)["config"])
    if any(fixture["metrics"].values()):
        raise RuntimeError("unified fixture failed")
    edge=u.resolve({1:u.initial(100,lateral=3.73,lateral_speed=1)},{1:v.control()})
    if edge["status"]!="FEASIBLE_COUPLED_STEP" or edge["search_stage"]!="REFINED":
        raise RuntimeError("refined fixture failed")
    legacy={"schema":1,"episodes":fixture["observations"]["episodes"],
            "metrics":fixture["metrics"],"edge_digest":reg.digest(edge),
            "infeasible":fixture["observations"]["infeasible"],
            "budget":fixture["observations"]["budget"]}
    return {"schema":2,"legacy":legacy,"steering":steering_records()}

def steering_records():
    rows=[]
    for grip in (.4,1.0):
        s={1:dict(y.initial(),y_m=-2.5),2:dict(y.initial(),y_m=2.5)}
        frames=[]
        for tick in range(4):
            cmd={i:v.control(grip_factor=grip,throttle=.5 if tick==0 else 0,
                              cut_s=.06 if tick==0 else 0,brake=.2 if tick==1 else 0) for i in s}
            targets={1:-.02 if tick<2 else .02,2:.02 if tick<2 else -.02}
            r=o.resolve(s,cmd,targets)
            if r["status"]!="FEASIBLE_ORIENTED_STEP":
                raise RuntimeError("oriented replay fixture failed")
            frames.append({"status":r["status"],"nodes":r["nodes"],"selected":[r["selected"][i] for i in sorted(s)]})
            s=r["states"]
        rows.append({"grip":grip,"frames":frames})
    edge=refinement.refine({1:dict(y.initial(),y_m=4.8)},{1:v.control()},{1:.25})
    if edge["status"]!="FEASIBLE_ORIENTED_STEP" or edge["final_loss"]>=edge["initial_loss"]:
        raise RuntimeError("refinement replay fixture failed")
    return {"oriented":rows,"refined_edge":edge}

def numerical_equal(a,b,path="steering"):
    if type(a) is not type(b):
        raise ValueError("cross-platform type mismatch at "+path)
    if isinstance(a,float):
        if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a,b,rel_tol=REL_TOL,abs_tol=ABS_TOL):
            raise ValueError("cross-platform numeric mismatch at "+path)
    elif isinstance(a,dict):
        if a.keys()!=b.keys():
            raise ValueError("cross-platform fields mismatch at "+path)
        for k in a:
            numerical_equal(a[k],b[k],path+"."+str(k))
    elif isinstance(a,(list,tuple)):
        if len(a)!=len(b):
            raise ValueError("cross-platform length mismatch at "+path)
        for i,(x,z) in enumerate(zip(a,b)):
            numerical_equal(x,z,path+"."+str(i))
    elif a!=b:
        raise ValueError("cross-platform discrete mismatch at "+path)

def compare(records):
    if len(records)<2:
        raise ValueError("need at least two records")
    if any(x.get("schema")==2 for x in records):
        if not all(x.get("schema")==2 and set(x)=={"schema","legacy","steering"} for x in records):
            raise ValueError("mixed replay schemas")
        legacy=compare([x["legacy"] for x in records])
        for x in records:
            numerical_equal(records[0]["steering"],x["steering"])
        return legacy  # exact legacy digest only; steering uses declared tolerances
    if any(x!=records[0] for x in records[1:]):
        raise ValueError("cross-platform replay mismatch; preserve all artifacts")
    return reg.digest(records[0])

def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="action",required=True)
    p=sub.add_parser("record");p.add_argument("--output",required=True)
    p=sub.add_parser("compare");p.add_argument("files",nargs="+")
    args=parser.parse_args()
    if args.action=="record":
        data=record()
        Path(args.output).write_text(json.dumps(data,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print(reg.digest(data))
    else:
        records=[json.loads(Path(p).read_text(encoding="utf-8")) for p in args.files]
        digest=compare(records)
        print(json.dumps({"exact_legacy_digest":digest,"steering_numeric_comparison":"PASS","abs_tol":ABS_TOL,"rel_tol":REL_TOL}) if records[0].get("schema")==2 else digest)

if __name__=="__main__":
    main()
