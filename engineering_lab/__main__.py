import argparse
import json
import sys
import subprocess
from pathlib import Path
from . import registry as reg
from . import provenance as prov
from . import research_cli, code_cli, private_metadata, debug_cli, experimental_cli, stage_closure

def demo(root):
    root.mkdir(mode=0o700)
    (root / "artifacts").mkdir(mode=0o700)
    # Fictitious revisions deliberately marked as synthetic, never production evidence.
    p = dict(schema=1, id="EXP-DEMO-001", peer="foundation", hypothesis="Sum of first ten integers is 55",
             scope="synthetic arithmetic; fictitious SHAs", sources=[], repository="example/synthetic",
             candidate_sha="a"*40, lab_sha="b"*40, baseline_sha=None, kind="unit",
             workload=dict(environment="Python offline", scenario="integers 1..10", seed=None,
                           ticks=None, command_hash=None, authorization="offline_only"),
             criteria={"sum": dict(op="eq", threshold=55, unit="count")})
    frozen = reg.register_plan(root, p)
    measured = sum(range(1, 11))
    data = reg.canonical({"sum": measured, "kind": "synthetic"})
    (root / "artifacts" / "demo.json").write_bytes(data)
    r = dict(schema=1, id=p["id"], plan_sha256=frozen["plan_sha256"], candidate_sha=p["candidate_sha"],
             lab_sha=p["lab_sha"], status="PASS" if measured == 55 else "FAIL", metrics={"sum": measured},
             evidence=[dict(file="demo.json", sha256=reg.checksum(data))],
             limitations="Arithmetic example only; no game, physics, or benchmark evidence.")
    return reg.register_result(root, r)

def main():
    parser = argparse.ArgumentParser(description="Offline APEX Engineering Lab")
    sub = parser.add_subparsers(dest="action", required=True)
    for command in ("plan", "record", "verify", "demo", "declare", "provenance", "github-check", "github-receipt", "receipt"):
        p = sub.add_parser(command)
        p.add_argument("--registry", required=True, type=Path)
        if command in ("plan", "record", "declare"):
            p.add_argument("input", type=Path)
        if command in ("github-check","github-receipt"):
            p.add_argument("--managed",action="store_true")
        if command in ("verify", "provenance", "github-check", "github-receipt", "receipt"):
            p.add_argument("--id", required=True)
    meta=sub.add_parser("metadata-check")
    meta.add_argument("--repository",required=True)
    meta.add_argument("--sha",required=True)
    meta.add_argument("--run",type=int)
    research_cli.add_commands(sub)
    code_cli.add_commands(sub)
    debug_cli.add_commands(sub)
    experimental_cli.add_commands(sub)
    stage_closure.add_commands(sub)
    args = parser.parse_args()
    try:
        if args.action.startswith("closure-"):
            result=stage_closure.cli(args)
        elif args.action.startswith("experiment-"):
            result=experimental_cli.run(args)
        elif args.action.startswith("debug-"):
            result=debug_cli.run(args)
        elif args.action=="metadata-check":
            result=private_metadata.check(args.repository,args.sha,args.run)
        elif args.action.startswith("code-"):
            result = code_cli.run(args)
        elif args.action.startswith("research-"):
            result = research_cli.run(args)
        elif args.action == "demo":
            result = demo(args.registry)
        elif args.action == "verify":
            result = reg.verify(args.registry, args.id)
        elif args.action == "declare":
            result = prov.declare(args.registry, reg.read_json(args.input))
        elif args.action in ("provenance", "github-check", "github-receipt", "receipt"):
            action = {"provenance": prov.inspect, "github-check": prov.github_check,
                      "github-receipt": prov.save_receipt, "receipt": prov.read_receipt}[args.action]
            if getattr(args,"managed",False):
                result = action(args.registry,args.id,fetch=private_metadata.managed_get,metadata_access="managed")
            else:
                result = action(args.registry, args.id)
        else:
            action = reg.register_plan if args.action == "plan" else reg.register_result
            result = action(args.registry, reg.read_json(args.input))
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("reported_status", "PASS") == "PASS" else 1
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, subprocess.SubprocessError) as error:
        print("BLOCKED:", error, file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
