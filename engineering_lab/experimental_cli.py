from pathlib import Path
from . import experimental as exp

def add_commands(sub):
    sub.add_parser("experiment-list")
    p=sub.add_parser("experiment-run")
    p.add_argument("name",choices=sorted(exp.specs()))
    p.add_argument("--id",required=True)
    p.add_argument("--registry",required=True,type=Path)

def run(args):
    if args.action=="experiment-list":
        return {"experiments":{name:{k:v for k,v in spec.items() if k!="evaluate"} for name,spec in exp.specs().items()},
                "execution":"FIXED_BUILTINS_ONLY","promotion":"NOT_AUTHORIZED"}
    return exp.run_checkout(args.registry,args.name,args.id)
