"""Evidence provenance v1: public GitHub metadata, never scientific approval."""
import datetime
import json
import urllib.request
from . import registry as reg

LAB = "Jugadru/APEX-Engineering-Lab"
PUBLIC_REPOS = {LAB, "Jugadru/APEX-Simulation", "Jugadru/APEX-Hyper-Engine"}
API = "https://api.github.com"
MAX_API = 1024 * 1024

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def public_get(path):
    # Paths are constructed only from allowlisted repositories, numeric IDs and exact SHAs.
    request = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "APEX-Engineering-Lab/0.2",
        "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=10) as response:
        data = response.read(MAX_API + 1)
    reg.require(len(data) <= MAX_API, "API response too large")
    return json.loads(data, object_pairs_hook=reg.no_duplicates)

def positive_id(value):
    return type(value) is int and 0 < value < 10**20

def load_records(root, ident):
    summary = reg.verify(root, ident)
    return (reg.read_json(root / (ident + ".plan.json")),
            reg.read_json(root / (ident + ".result.json")), summary)

def validate_declaration(p, r, summary, d):
    reg.exact(d, "schema id result_sha256 origin run archives limitations")
    reg.require(type(d["schema"]) is int and d["schema"] == 1, "provenance schema")
    reg.require(d["id"] == p["id"] and d["result_sha256"] == summary["result_sha256"], "result binding")
    reg.require(d["origin"] in {"synthetic", "local", "github_actions"}, "origin")
    reg.require(reg.nonempty(d["limitations"]), "limitations")
    archives = d["archives"]
    reg.require(isinstance(archives, list) and len(archives) <= 20, "archive mappings")
    if d["origin"] != "github_actions":
        reg.require(d["run"] is None and not archives, "non-GitHub origin cannot declare a run")
        return
    run = d["run"]
    reg.exact(run, "repository id attempt")
    reg.require(p["repository"] in PUBLIC_REPOS and run["repository"] == p["repository"], "public repository allowlist")
    reg.require(positive_id(run["id"]) and positive_id(run["attempt"]), "run ID/attempt")
    reg.require(r["status"] != "NOT_RUN", "NOT_RUN cannot claim execution")
    evidence = {x["file"] for x in r["evidence"]}
    seen_ids, seen_files = set(), set()
    for item in archives:
        reg.exact(item, "artifact_id file")
        aid, filename = item["artifact_id"], item["file"]
        reg.require(positive_id(aid) and isinstance(filename, str) and filename in evidence
                    and filename.lower().endswith(".zip"), "archive must be a registered zip evidence file")
        reg.require(aid not in seen_ids and filename not in seen_files, "duplicate archive mapping")
        seen_ids.add(aid)
        seen_files.add(filename)

def declare(root, d):
    reg.valid_root(root)
    reg.require(isinstance(d, dict), "declaration object required")
    ident = reg.experiment_id(d.get("id"))
    p, r, summary = load_records(root, ident)
    validate_declaration(p, r, summary, d)
    reg.publish_once(root / (ident + ".provenance.json"), d)
    return inspect(root, ident)

def inspect(root, ident):
    p, r, s = load_records(root, ident)
    d = reg.read_json(root / (ident + ".provenance.json"))
    validate_declaration(p, r, s, d)
    return {"id": ident, "origin": d["origin"], "declaration_sha256": reg.digest(d),
            "result_sha256": s["result_sha256"], "reported_status": r["status"],
            "artifact_bytes": s["artifact_bytes"], "provenance": "DECLARED_ONLY",
            "maturity": "PROPOSTO" if r["status"] == "NOT_RUN" else "EXPERIMENTAL",
            "scientific_review": "NOT_PERFORMED", "promotion": "NOT_AUTHORIZED"}

def github_check(root, ident, fetch=public_get, metadata_access="public"):
    reg.require(metadata_access in {"public","managed"},"metadata access mode")
    """Read public metadata via HTTPS. Dependency injection is for offline tests only."""
    p, r, s = load_records(root, ident)
    d = reg.read_json(root / (ident + ".provenance.json"))
    validate_declaration(p, r, s, d)
    reg.require(d["origin"] == "github_actions", "GitHub origin required")
    repo = p["repository"]
    run = d["run"]
    prefix = "/repos/" + repo
    candidate = fetch(prefix + "/commits/" + p["candidate_sha"])
    lab = fetch("/repos/" + LAB + "/commits/" + p["lab_sha"])
    reg.require(candidate.get("sha") == p["candidate_sha"] and lab.get("sha") == p["lab_sha"], "revision metadata mismatch")
    if p["baseline_sha"] is not None:
        baseline = fetch(prefix + "/commits/" + p["baseline_sha"])
        reg.require(baseline.get("sha") == p["baseline_sha"], "baseline revision mismatch")
    live = fetch(prefix + "/actions/runs/" + str(run["id"]))
    reg.require(live.get("id") == run["id"] and live.get("run_attempt") == run["attempt"], "run or attempt mismatch")
    reg.require(live.get("head_sha") == p["candidate_sha"], "run head mismatch")
    reg.require((live.get("repository") or {}).get("full_name") == repo
                and (live.get("head_repository") or {}).get("full_name") == repo, "run repository mismatch or fork")
    reg.require(live.get("status") == "completed" and live.get("conclusion") in {"success", "failure", "cancelled", "timed_out", "skipped", "neutral", "action_required", "stale", "startup_failure"}, "run not completed")
    # Workflow outcome is deliberately separate from the scientific result.
    evidence = {x["file"]: x["sha256"] for x in r["evidence"]}
    matched = []
    for item in d["archives"]:
        aid, filename = item["artifact_id"], item["file"]
        artifact = fetch(prefix + "/actions/artifacts/" + str(aid))
        wr = artifact.get("workflow_run") or {}
        reg.require(artifact.get("id") == aid and artifact.get("expired") is False
                    and wr.get("id") == run["id"] and wr.get("head_sha") == p["candidate_sha"], "artifact run binding")
        reg.require(artifact.get("digest") == "sha256:" + evidence[filename], "archive digest absent or mismatch")
        matched.append({"id": aid, "file": filename, "sha256": evidence[filename]})
    # Artifacts API does not independently identify the run attempt; avoid claiming that.
    coverage = bool(evidence) and len(matched) == len(evidence)
    result = inspect(root, ident)
    result.update({"provenance": "MANAGED_GITHUB_METADATA_MATCH" if metadata_access=="managed" else "PUBLIC_GITHUB_METADATA_MATCH", "workflow_id": run["id"],
                   "workflow_attempt": run["attempt"], "workflow_conclusion": live["conclusion"],
                   "archive_digest_coverage": "ALL" if coverage else ("PARTIAL" if matched else "NONE"),
                   "matched_archives": matched, "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   "review_readiness": "EVIDENCE_FOR_REVIEW" if coverage and live["conclusion"] == "success"
                      and r["status"] in {"PASS", "FAIL"} else "INSUFFICIENT",
                   "limitations": "HTTPS metadata at check time; no signature, trusted timestamp, artifact attempt attribution, metric authenticity, or scientific validation."})
    return result

def save_receipt(root, ident, fetch=None, metadata_access="public"):
    report = github_check(root, ident) if fetch is None else github_check(root, ident, fetch=fetch, metadata_access=metadata_access)
    reg.publish_once(root / (ident + ".github-receipt.json"), report)
    return report

def read_receipt(root, ident):
    current = inspect(root, ident)
    receipt = reg.read_json(root / (ident + ".github-receipt.json"))
    reg.require(isinstance(receipt, dict) and receipt.get("id") == ident
                and receipt.get("declaration_sha256") == current["declaration_sha256"]
                and receipt.get("result_sha256") == current["result_sha256"], "receipt binding mismatch")
    # A local receipt is not signed. Do not echo its assertions as trusted evidence.
    return {**current, "receipt_sha256": reg.digest(receipt),
            "receipt_status": "LOCAL_SNAPSHOT_UNAUTHENTICATED",
            "live_recheck": "REQUIRED"}
