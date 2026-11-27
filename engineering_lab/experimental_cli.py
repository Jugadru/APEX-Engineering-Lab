from pathlib import Path
from . import experimental as exp, exp_reports, registry as reg

def add_commands(sub):
    sub.add_parser("experiment-list")
    p=sub.add_parser("experiment-report")
    p.add_argument("--registry",required=True,type=Path)
    p.add_argument("--id",required=True)
    p=sub.add_parser("experiment-suite-report")
    p.add_argument("--entry",action="append",nargs=2,required=True,metavar=("PATH","ID"))
    p.add_argument("--output",type=Path)
    p.add_argument("--markdown",type=Path)
    p=sub.add_parser("experiment-run")
    p.add_argument("name",choices=sorted(exp.specs()))
    p.add_argument("--id",required=True)
    p.add_argument("--registry",required=True,type=Path)

def run(args):
    if args.action=="experiment-report":
        return exp_reports.report(args.registry,args.id)
    if args.action=="experiment-suite-report":
        result=exp_reports.suite(args.entry)
        if args.output: reg.publish_once(args.output,result)
        if args.markdown:
            with args.markdown.open("x",encoding="utf-8") as stream:
                stream.write(exp_reports.markdown(result))
        return {"revision":result["revision"],"reported_status":result["reported_status"],"counts":result["counts"],
                "experiments":[{"id":r["id"],"experiment":r["experiment"],"status":r["reported_status"]} for r in result["experiments"]],
                "scientific_validation":"NOT_PERFORMED","promotion":"NOT_AUTHORIZED"}
    if args.action=="experiment-list":
        return {"experiments":{name:{k:v for k,v in spec.items() if k!="evaluate"} for name,spec in exp.specs().items()},
                "execution":"FIXED_BUILTINS_ONLY","promotion":"NOT_AUTHORIZED"}
    return exp.run_checkout(args.registry,args.name,args.id)
