"""Stage exit checks, reusing managed GitHub metadata; no promotion or runner dispatch."""
import re
import subprocess
from pathlib import Path
from . import registry as reg, private_metadata as metadata

REPO="Jugadru/APEX-Engineering-Lab"
# Cumulative light regression floor. Add department-specific workflows in reviewed
# changes before closing a stage; extra declared checks are also mandatory.
REQUIRED={".github/workflows/qa.yml",".github/workflows/physics.yml",".github/workflows/experiments.yml"}
# Historical manifests remain readable. A new closure of a reopened 0.8
# revision must cover the modern regression workflows at that exact tree.
REOPENED_REQUIRED=REQUIRED | {
    ".github/workflows/racecraft.yml",
    ".github/workflows/racecraft-platform.yml",
    ".github/workflows/racecraft-track-evidence.yml",
    ".github/workflows/racecraft-outline-evidence.yml",
    ".github/workflows/stage-closure.yml"}
REOPENED_ADDITIONAL={
    ".github/workflows/racecraft-historical-pace.yml",
    ".github/workflows/native-engine-comparison.yml"}
REVIEW={"scope","boundary_cases","regression","evidence","documentation","rollback"}
ORDER=[f"0.{i}" for i in range(7,13)]+["1.0"]

def series(version):
    reg.require(reg.match(version,r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"),"version format")
    return ".".join(version.split(".")[:2])

def successor(stage):
    reg.require(stage in ORDER[:-1],"stage outside reviewed roadmap")
    return ORDER[ORDER.index(stage)+1]

def run_ref(r):
    reg.exact(r,"id attempt path")
    reg.require(type(r["id"]) is int and 0<r["id"]<10**20 and type(r["attempt"]) is int and 1<=r["attempt"]<=100,"run identity")
    reg.require(reg.match(r["path"],r"\.github/workflows/[a-zA-Z0-9_.-]+\.ya?ml"),"workflow path")

def validate(m):
    reg.exact(m,"schema series next_series candidate_sha reviewed_main_sha candidate_runs main_runs adverse_runs review findings limitations rollback")
    reg.require(type(m["schema"]) is int and m["schema"]==1 and m["next_series"]==successor(m["series"]),"closure schema/sequence")
    reg.require(reg.sha40(m["candidate_sha"]) and reg.sha40(m["reviewed_main_sha"]) and m["candidate_sha"]!=m["reviewed_main_sha"],"distinct exact revisions")
    required=REQUIRED | ({".github/workflows/racecraft.yml"} if ORDER.index(m["series"])>=ORDER.index("0.8") else set())
    used=set()
    for key in ("candidate_runs","main_runs"):
        rows=m[key]
        reg.require(isinstance(rows,list) and len(required)<=len(rows)<=12,"required workflow set")
        paths=set()
        for r in rows:
            run_ref(r)
            reg.require(r["path"] not in paths and r["id"] not in used,"duplicate workflow/run")
            paths.add(r["path"]); used.add(r["id"])
        reg.require(required<=paths,"missing mandatory regression workflow")
        if key=="candidate_runs": candidate_paths=paths
        else: reg.require(paths==candidate_paths,"candidate/main workflow coverage differs")
    reg.require(isinstance(m["adverse_runs"],list) and len(m["adverse_runs"])<=12,"adverse runs")
    for r in m["adverse_runs"]:
        reg.exact(r,"id attempt path sha")
        run_ref({k:r[k] for k in ("id","attempt","path")})
        reg.require(reg.sha40(r["sha"]) and r["sha"] not in (m["candidate_sha"],m["reviewed_main_sha"]) and r["id"] not in used,"adverse revision/run")
        used.add(r["id"])
    reg.require(isinstance(m["review"],dict) and set(m["review"])==REVIEW and all(reg.nonempty(v) for v in m["review"].values()),"review checklist incomplete")
    reg.require(isinstance(m["findings"],list) and len(m["findings"])<=100,"findings")
    seen=set()
    for row in m["findings"]:
        reg.exact(row,"id severity status summary evidence")
        reg.require(reg.match(row["id"],r"AUD-[A-Z0-9-]{1,60}") and row["id"] not in seen,"finding ID")
        seen.add(row["id"])
        reg.require(row["severity"] in {"LOW","MEDIUM","HIGH","CRITICAL"} and row["status"] in {"RESOLVED","LIMITATION","OPEN"} and reg.nonempty(row["summary"]) and reg.nonempty(row["evidence"]),"finding fields")
    reg.require(isinstance(m["limitations"],list) and 1<=len(m["limitations"])<=30 and all(reg.nonempty(x) for x in m["limitations"]) and reg.nonempty(m["rollback"]),"limitations/rollback")
    return reg.digest(m)

def check(m,fetch=metadata.managed_get):
    digest=validate(m)
    open_ids=[x["id"] for x in m["findings"] if x["status"]=="OPEN"]
    if open_ids:
        return {"reported_status":"BLOCKED","reason":"open findings","open_findings":open_ids,"manifest_sha256":digest,"promotion":"NOT_AUTHORIZED"}
    prefix="/repos/"+REPO
    c=fetch(prefix+"/commits/"+m["candidate_sha"]); main=fetch(prefix+"/commits/"+m["reviewed_main_sha"])
    reg.require(c.get("sha")==m["candidate_sha"] and main.get("sha")==m["reviewed_main_sha"],"commit binding")
    tree=(c.get("commit") or {}).get("tree",{}).get("sha")
    reg.require(reg.sha40(tree) and tree==(main.get("commit") or {}).get("tree",{}).get("sha"),"candidate/main tree mismatch")
    parents=main.get("parents",[])
    reg.require(len(parents)==2 and parents[1].get("sha")==m["candidate_sha"],"reviewed main must be merge of exact candidate")
    checked=[]
    for group in ("candidate_runs","main_runs","adverse_runs"):
        for row in m[group]:
            sha=m["candidate_sha"] if group=="candidate_runs" else m["reviewed_main_sha"] if group=="main_runs" else row["sha"]
            want="failure" if group=="adverse_runs" else "success"
            r=fetch(prefix+"/actions/runs/"+str(row["id"]))
            reg.require(r.get("id")==row["id"] and r.get("run_attempt")==row["attempt"] and r.get("head_sha")==sha
                        and r.get("path")==row["path"] and (r.get("repository") or {}).get("full_name")==REPO
                        and (r.get("head_repository") or {}).get("full_name")==REPO,"workflow identity mismatch")
            if group=="main_runs":
                reg.require(r.get("event")=="push" and r.get("head_branch")=="main","main run is not a main push")
            elif group=="candidate_runs":
                reg.require(r.get("event")=="pull_request","candidate run is not a PR")
            reg.require(r.get("status")=="completed" and r.get("conclusion")==want,"required run not completed with expected conclusion")
            checked.append({"group":group,"id":row["id"],"sha":sha,"path":row["path"],"conclusion":want,"attempt":row["attempt"]})
    return {"reported_status":"PASS","stage":m["series"],"next_stage":m["next_series"],"reviewed_main_sha":m["reviewed_main_sha"],
            "candidate_sha":m["candidate_sha"],"tree":tree,"manifest_sha256":digest,"runs":checked,
            "review":"DECLARED_TECHNICAL_REVIEW","evidence":"LIVE_GITHUB_METADATA_MATCH",
            "promotion":"NOT_AUTHORIZED","scientific_validation":"NOT_PERFORMED",
            "limitations":"Metadata and checklist gate only; no log/artifact byte authentication, independent review, branch protection or game authorization."}

def git(root,*args):
    return subprocess.check_output(["git","-C",str(root),*args],timeout=10,text=True)

def version_at(root,sha):
    reg.require(reg.sha40(sha),"revision")
    data=git(root,"show",sha+":engineering_lab/__init__.py")
    hits=re.findall(r'^__version__\s*=\s*["\x27]([0-9.]+)["\x27]\s*$',data,re.M)
    reg.require(len(hits)==1,"version declaration")
    return hits[0]

def reopened_coverage(m,tree_paths):
    if m["series"]!="0.8" or "audit/REOPEN_0.8.md" not in tree_paths:
        return
    reg.require(REOPENED_REQUIRED<=tree_paths,"reopened stage missing required workflow files")
    required=REOPENED_REQUIRED | (REOPENED_ADDITIONAL & tree_paths)
    for key in ("candidate_runs","main_runs"):
        reg.require(required<={r["path"] for r in m[key]},"reopened stage missing workflow evidence")

def coverage(root,m,base):
    # A closure record may be committed after the reviewed main. Only its own
    # manifest may differ; any code, tests, workflows or other docs invalidate it.
    reviewed=m["reviewed_main_sha"]
    reg.require(subprocess.run(["git","-C",str(root),"merge-base","--is-ancestor",reviewed,base],timeout=10,check=False).returncode==0,"reviewed main is not an ancestor of base")
    delta=set(git(root,"diff","--name-only","-z",reviewed,base).split("\0"))-{""}
    reg.require(delta<={"audit/closures/"+m["series"]+".json"},"base changed beyond closure manifest; refresh audit")
    reg.require(series(version_at(root,reviewed))==m["series"],"reviewed revision is wrong series")
    if m["series"]=="0.8":
        paths=set(git(root,"ls-tree","-r","--name-only","-z",reviewed).split("\0"))-{""}
        reopened_coverage(m,paths)

def transition(root,base,fetch=metadata.managed_get):
    reg.require(reg.sha40(base),"base SHA")
    head=git(root,"rev-parse","HEAD").strip()
    before,after=series(version_at(root,base)),series(version_at(root,head))
    changed=set(git(root,"diff","--name-only","-z",base,head).split("\0"))-{""}
    manifests={p for p in changed if p.startswith("audit/closures/")}
    if before==after and not manifests:
        return {"reported_status":"PASS","gate":"SAME_SERIES_NO_CLOSURE_REQUIRED","series":before,"promotion":"NOT_AUTHORIZED"}
    if before!=after:
        reg.require(after==successor(before),"series skip or downgrade")
    path="audit/closures/"+before+".json"
    reg.require(manifests<={path},"unexpected closure manifest changes")
    m=reg.read_json(root/path)
    reg.require(m["series"]==before,"wrong closure series")
    validate(m); coverage(root,m,base)
    result=check(m,fetch)
    return {**result,"gate":"STAGE_TRANSITION" if before!=after else "STAGE_CLOSURE_RECORD"}

def add_commands(sub):
    p=sub.add_parser("closure-check")
    p.add_argument("manifest",type=Path)
    p.add_argument("--managed",action="store_true")
    p=sub.add_parser("closure-transition")
    p.add_argument("--base-sha",required=True)

def cli(args):
    if args.action=="closure-check":
        m=reg.read_json(args.manifest); digest=validate(m)
        if not args.managed:
            return {"reported_status":"BLOCKED","reason":"live managed verification required","manifest_sha256":digest,"promotion":"NOT_AUTHORIZED"}
        return check(m)
    return transition(Path(__file__).resolve().parent.parent,args.base_sha)
