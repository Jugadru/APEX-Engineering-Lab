from pathlib import Path
from . import registry as reg, debugging as d, bug_intelligence as bi
def add_commands(sub):
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
    if args.action=="debug-classify": return bi.record(args.registry,args.id,args.source,args.case)
    if args.action=="debug-history": return bi.history(args.registry,args.fingerprint)
    if args.action=="debug-open": return d.open_case(args.registry,reg.read_json(args.input))
    return d.inspect_case(args.registry,args.id)
