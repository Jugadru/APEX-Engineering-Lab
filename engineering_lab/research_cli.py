from pathlib import Path
from . import registry as reg, research as res

def add_commands(sub):
    for name in ("research-validate","research-search","research-rank","research-propose","research-discover"):
        p=sub.add_parser(name)
        if name=="research-discover":
            p.add_argument("provider",choices=("github","crossref"))
            p.add_argument("query")
            continue
        p.add_argument("--portfolio",type=Path,default=Path("research/portfolio.json"))
        if name!="research-rank":
            p.add_argument("--foundation-dir",type=Path,required=True)
            p.add_argument("--pin",type=Path,default=Path("research/foundation-pin.json"))
        if name=="research-search":
            p.add_argument("query")
        if name=="research-propose":
            for field in ("card","id","repository","candidate","lab","baseline"):
                p.add_argument("--"+field,required=True)
            p.add_argument("--registry",type=Path,required=True)

def run(args):
    if args.action=="research-discover":
        return res.public_discover(args.provider,args.query)
    p=reg.read_json(args.portfolio)
    if args.action=="research-rank":
        return {"ranking":res.rank(p),"score":"2*benefit-cost-risk; ordinal estimates only"}
    pin=reg.read_json(args.pin)
    catalog=res.load_foundation(args.foundation_dir,pin)
    if args.action=="research-search":
        return {"matches":res.search_catalog(catalog,args.query),"status":"CATALOG_ONLY"}
    if args.action=="research-validate":
        return res.validate_portfolio(p,catalog,pin)
    plan=res.propose(p,args.card,args.id,args.repository,args.candidate,args.lab,args.baseline,catalog,pin)
    return {**reg.register_plan(args.registry,plan),"status":"PROPOSED_NOT_RUN","promotion":"NOT_AUTHORIZED"}
