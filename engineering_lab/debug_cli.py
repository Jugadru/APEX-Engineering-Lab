from pathlib import Path
from . import registry as reg, debugging as d
def add_commands(sub):
    for name in ("debug-open","debug-inspect"):
        p=sub.add_parser(name)
        p.add_argument("--registry",required=True,type=Path)
        if name=="debug-open": p.add_argument("input",type=Path)
        else: p.add_argument("--id",required=True)
def run(args):
    if args.action=="debug-open": return d.open_case(args.registry,reg.read_json(args.input))
    return d.inspect_case(args.registry,args.id)
