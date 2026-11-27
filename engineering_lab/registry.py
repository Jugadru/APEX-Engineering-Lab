"""Local evidence envelopes; no network, dispatch, or promotion."""
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path

LIMIT = 1024 * 1024
PEERS = {"asset_factory", "foundation", "lab_hub", "hyper_engine"}
KINDS = {"documentary", "static", "unit", "fixture", "simulation", "headless_benchmark", "native_graphics", "asset_qa"}
STATUSES = {"PASS", "FAIL", "NOT_RUN", "INCONCLUSIVE", "BLOCKED"}

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def match(s, pattern):
    return isinstance(s, str) and re.fullmatch(pattern, s) is not None

def exact(obj, names):
    require(isinstance(obj, dict) and set(obj) == set(names.split()), "unexpected/missing fields")

def nonempty(s):
    return isinstance(s, str) and bool(s.strip()) and len(s) <= 4000

def numeric(v):
    return type(v) in (int, float) and abs(v) <= 1e100 and math.isfinite(v)

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()

def checksum(data):
    return hashlib.sha256(data).hexdigest()

def digest(obj):
    return checksum(canonical(obj))

def no_duplicates(items):
    result = {}
    for k, v in items:
        require(k not in result, "duplicate JSON key")
        result[k] = v
    return result

def bounded_bytes(path):
    require(path.is_file() and not path.is_symlink(), "regular non-symlink file required")
    with path.open("rb") as f:
        data = f.read(LIMIT + 1)
    require(len(data) <= LIMIT, "file exceeds 1 MiB")
    return data

def read_json(path):
    return json.loads(bounded_bytes(path), object_pairs_hook=no_duplicates)

def publish_once(path, obj):
    data = canonical(obj) + b"\n"
    require(len(data) <= LIMIT, "record too large")
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
        name = Path(temp.name)
        try:
            temp.write(data)
            temp.flush()
            os.fsync(temp.fileno())
            temp.close()
            os.link(name, path)
        finally:
            name.unlink(missing_ok=True)

def experiment_id(value):
    require(match(value, r"EXP-[A-Z0-9-]{1,60}"), "invalid experiment ID")
    return value

def sha40(s):
    return match(s, r"[0-9a-f]{40}")

def sha64(s):
    return match(s, r"[0-9a-f]{64}")

def validate_plan(p):
    exact(p, "schema id peer hypothesis scope sources repository candidate_sha lab_sha baseline_sha kind workload criteria")
    require(type(p["schema"]) is int and p["schema"] == 1, "schema")
    experiment_id(p["id"])
    require(p["peer"] in PEERS and p["kind"] in KINDS, "unknown peer/kind")
    require(nonempty(p["hypothesis"]) and nonempty(p["scope"]), "hypothesis/scope")
    require(match(p["repository"], r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"), "repository")
    require(sha40(p["candidate_sha"]) and sha40(p["lab_sha"]), "exact SHA required")
    require(p["baseline_sha"] is None or sha40(p["baseline_sha"]), "baseline SHA")
    s = p["sources"]
    require(isinstance(s, list) and len(s) <= 500 and all(match(x, r"(REF|IDEA)-[0-9]{3,}") for x in s), "source IDs")
    require(len(s) == len(set(s)), "duplicate sources")
    w = p["workload"]
    exact(w, "environment scenario seed ticks command_hash authorization")
    require(nonempty(w["environment"]) and nonempty(w["scenario"]), "workload")
    require(w["seed"] is None or type(w["seed"]) is int, "seed")
    require(w["ticks"] is None or type(w["ticks"]) is int and w["ticks"] > 0, "ticks")
    require(w["command_hash"] is None or sha64(w["command_hash"]), "command hash")
    require(w["authorization"] in {"offline_only", "hosted_reviewed", "owner_authorized"}, "authorization label")
    if p["kind"] in {"simulation", "headless_benchmark"}:
        require(all(w[k] is not None for k in ("seed", "ticks", "command_hash")), "deterministic workload incomplete")
    if p["kind"] == "headless_benchmark":
        require(p["baseline_sha"] is not None, "benchmark baseline required")
    if p["kind"] == "native_graphics":
        require(w["authorization"] == "owner_authorized", "native authorization label required")
    c = p["criteria"]
    require(isinstance(c, dict) and 0 < len(c) <= 50, "criteria")
    for key, rule in c.items():
        require(match(key, r"[a-z][a-z0-9_]{0,63}"), "metric name")
        exact(rule, "op threshold unit")
        require(rule["op"] in {"eq", "le", "ge"} and numeric(rule["threshold"]) and nonempty(rule["unit"]), "criterion")
        if p["kind"] != "native_graphics":
            require("fps" not in key and rule["unit"].lower() != "fps", "native FPS cannot be inferred")
    return digest(p)

def check(rule, value):
    if rule["op"] == "eq":
        return value == rule["threshold"]
    if rule["op"] == "le":
        return value <= rule["threshold"]
    return value >= rule["threshold"]

def validate_result(p, r, root):
    plan_hash = validate_plan(p)
    exact(r, "schema id plan_sha256 candidate_sha lab_sha status metrics evidence limitations")
    require(type(r["schema"]) is int and r["schema"] == 1, "schema")
    require(r["id"] == p["id"] and r["plan_sha256"] == plan_hash, "plan mismatch")
    require(r["candidate_sha"] == p["candidate_sha"] and r["lab_sha"] == p["lab_sha"], "revision mismatch")
    require(r["status"] in STATUSES and nonempty(r["limitations"]), "status/limitations")
    m = r["metrics"]
    require(isinstance(m, dict) and set(m) <= set(p["criteria"]) and all(numeric(v) for v in m.values()), "metrics")
    ev = r["evidence"]
    require(isinstance(ev, list) and len(ev) <= 50, "evidence")
    if ev:
        folder = root / "artifacts"
        require(folder.is_dir() and not folder.is_symlink(), "artifact directory invalid")
    seen = set()
    for item in ev:
        exact(item, "file sha256")
        filename = item["file"]
        require(match(filename, r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}") and sha64(item["sha256"]), "artifact name/hash")
        require(filename not in seen, "duplicate artifact")
        seen.add(filename)
        require(checksum(bounded_bytes(folder / filename)) == item["sha256"], "artifact bytes mismatch")
    checks = {k: check(p["criteria"][k], v) for k, v in m.items()}
    if r["status"] in {"PASS", "FAIL"}:
        require(bool(ev) and set(m) == set(p["criteria"]), "decisive result needs complete evidence")
        require((r["status"] == "PASS") == all(checks.values()), "status contradicts criteria")
    if r["status"] == "NOT_RUN":
        require(not m and not ev, "NOT_RUN cannot contain observations")
    return {"id": p["id"], "plan_sha256": plan_hash, "result_sha256": digest(r),
            "reported_status": r["status"], "checks": checks,
            "artifact_bytes": "MATCH" if ev else "NOT_RUN",
            "authenticity": "NOT_VERIFIED", "promotion": "NOT_AUTHORIZED"}

def valid_root(root):
    require(root.is_dir() and not root.is_symlink(), "existing non-symlink registry required")

def register_plan(root, p):
    valid_root(root)
    h = validate_plan(p)
    publish_once(root / (p["id"] + ".plan.json"), p)
    return {"id": p["id"], "plan_sha256": h}

def register_result(root, r):
    valid_root(root)
    require(isinstance(r, dict), "result object required")
    ident = experiment_id(r.get("id"))
    p = read_json(root / (ident + ".plan.json"))
    require(p.get("id") == ident, "plan filename mismatch")
    summary = validate_result(p, r, root)
    publish_once(root / (ident + ".result.json"), r)
    return summary

def verify(root, ident):
    valid_root(root)
    experiment_id(ident)
    p = read_json(root / (ident + ".plan.json"))
    r = read_json(root / (ident + ".result.json"))
    require(p.get("id") == ident, "plan filename mismatch")
    return validate_result(p, r, root)
