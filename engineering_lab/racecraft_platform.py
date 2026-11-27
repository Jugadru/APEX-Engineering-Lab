"""Portable exact replay evidence for the isolated Racecraft reference."""
import argparse
import json
from pathlib import Path
from . import racecraft_unified as u, physics_vehicle as v, registry as reg

def record():
    fixture=u.evaluate(u.spec(lambda *args: None)["config"])
    if any(fixture["metrics"].values()):
        raise RuntimeError("unified fixture failed")
    edge=u.resolve({1:u.initial(100,lateral=3.73,lateral_speed=1)},{1:v.control()})
    if edge["status"]!="FEASIBLE_COUPLED_STEP" or edge["search_stage"]!="REFINED":
        raise RuntimeError("refined fixture failed")
    return {"schema":1,"episodes":fixture["observations"]["episodes"],
            "metrics":fixture["metrics"],"edge_digest":reg.digest(edge),
            "infeasible":fixture["observations"]["infeasible"],
            "budget":fixture["observations"]["budget"]}

def compare(records):
    if len(records)<2:
        raise ValueError("need at least two records")
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
        print(compare([json.loads(Path(p).read_text(encoding="utf-8")) for p in args.files]))

if __name__=="__main__":
    main()
