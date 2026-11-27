import argparse
import json
import sys
from pathlib import Path
from . import registry as reg

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
    for command in ("plan", "record", "verify", "demo"):
        p = sub.add_parser(command)
        p.add_argument("--registry", required=True, type=Path)
        if command in ("plan", "record"):
            p.add_argument("input", type=Path)
        if command == "verify":
            p.add_argument("--id", required=True)
    args = parser.parse_args()
    try:
        if args.action == "demo":
            result = demo(args.registry)
        elif args.action == "verify":
            result = reg.verify(args.registry, args.id)
        else:
            action = reg.register_plan if args.action == "plan" else reg.register_result
            result = action(args.registry, reg.read_json(args.input))
        print(json.dumps(result, sort_keys=True))
        return 0 if result.get("reported_status", "PASS") == "PASS" else 1
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
        print("BLOCKED:", error, file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
