from pathlib import Path
from . import registry as reg, code_intelligence as ci, code_collect, code_evidence
def add_commands(sub):
    p=sub.add_parser("code-collect")
    p.add_argument("--game",type=Path,required=True)
    p.add_argument("--pin",type=Path,default=Path("research/code-pins.json"))
    p.add_argument("--output",type=Path,required=True)
    p=sub.add_parser("code-review")
    p.add_argument("bundle",type=Path)
    p.add_argument("--analyzer",type=Path)
    p.add_argument("--changed",type=Path)
    p.add_argument("--output",type=Path)
    p=sub.add_parser("code-evidence")
    p.add_argument("bundle",type=Path)
    for name in ("summary","profile","correlation"):
        p.add_argument("--"+name,type=Path)
    p=sub.add_parser("code-compare")
    p.add_argument("baseline",type=Path)
    p.add_argument("candidate",type=Path)
def run(args):
    if args.action=="code-collect":
        result=code_collect.collect(args.game,reg.read_json(args.pin))
        reg.publish_once(args.output,result)
        return {"game_sha":result["game_sha"],"scripts":result["architecture"]["scripts"],"bundle_sha256":reg.digest(result)}
    if args.action=="code-evidence":
        read=lambda path: reg.read_json(path) if path else None
        return code_evidence.join(reg.read_json(args.bundle),read(args.summary),read(args.profile),read(args.correlation))
    if args.action=="code-compare":
        return ci.compare(reg.read_json(args.baseline),reg.read_json(args.candidate))
    result=ci.review(reg.read_json(args.bundle),reg.read_json(args.changed) if args.changed else None,
                     reg.read_json(args.analyzer) if args.analyzer else None)
    if args.output: reg.publish_once(args.output,result)
    return result
