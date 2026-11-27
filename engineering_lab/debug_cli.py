from pathlib import Path
from . import registry as reg, debugging as d, bug_intelligence as bi, reproduction as rp, solution as sol
def add_commands(sub):
    for name in ("debug-solution-bind","debug-solution-review","debug-solution-demo"):
        p=sub.add_parser(name)
        p.add_argument("--registry",required=True,type=Path)
        if name!="debug-solution-demo": p.add_argument("--id",required=True)
        if name=="debug-solution-bind": p.add_argument("input",type=Path)
    for name in ("debug-repro-bind","debug-repro-check","debug-repro-demo"):
        p=sub.add_parser(name)
        p.add_argument("--registry",required=True,type=Path)
        if name!="debug-repro-demo": p.add_argument("--id",required=True)
        if name=="debug-repro-bind": p.add_argument("input",type=Path)
    p=sub.add_parser("debug-classify")
    p.add_argument("--registry",required=True,type=Path)
    for name in ("id","source","case"): p.add_argument("--"+name,required=True)
    p=sub.add_parser("debug-history")
    p.add_argument("--registry",required=True,type=Path)
    p.add_argument("--fingerprint",required=True)
    for name in ("debug-open","debug-inspect"):
        p=sub.add_parser(name)
        p.add_argument("--registry",required=True,type=Path)
        if name=="debug-open": p.add_argument("input",type=Path)
        else: p.add_argument("--id",required=True)
def run(args):
    if args.action=="debug-solution-demo": return sol.demo(args.registry)
    if args.action=="debug-solution-bind": return sol.bind(args.registry,args.id,reg.read_json(args.input))
    if args.action=="debug-solution-review": return sol.evaluate(args.registry,args.id)
    if args.action=="debug-repro-demo": return rp.demo(args.registry)
    if args.action=="debug-repro-bind": return rp.bind(args.registry,args.id,reg.read_json(args.input))
    if args.action=="debug-repro-check": return rp.check(args.registry,args.id)
    if args.action=="debug-classify": return bi.record(args.registry,args.id,args.source,args.case)
    if args.action=="debug-history": return bi.history(args.registry,args.fingerprint)
    if args.action=="debug-open": return d.open_case(args.registry,reg.read_json(args.input))
    return d.inspect_case(args.registry,args.id)
