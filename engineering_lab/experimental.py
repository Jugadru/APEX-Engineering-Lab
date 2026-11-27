"""Bounded original synthetic experiments, using the existing scientific registry."""
import random
import subprocess
from pathlib import Path
from . import registry as reg, exp_spatial

REPO="Jugadru/APEX-Engineering-Lab"
FOUNDATION="1c226891f24796d0a14535693d32f626a5b476f5"
def criterion(op,threshold,unit="count"):
    return dict(op=op,threshold=threshold,unit=unit)

def ordered_commands(config):
    rng=random.Random(config["seed"])
    commands=[(i, rng.randrange(100), rng.randrange(10)) for i in range(config["agents"])]
    def resolve(rows):
        # Stable ID tie break on a frozen snapshot.
        return sorted(rows,key=lambda r:(-r[1],r[0]))
    expected=resolve(commands); mismatches=0
    for _ in range(config["permutations"]):
        perm=list(commands); rng.shuffle(perm)
        mismatches+=resolve(perm)!=expected
    return {"metrics":{"state_mismatches":mismatches,"invalid_commands":len(expected)-len({r[0] for r in expected})},
            "observations":{"agents":len(commands),"permutations":config["permutations"],"state_sha256":reg.digest(expected)}}

def specs():
    return {"spatial_neighbors":dict(hypothesis="Sorted periodic index returns identical inclusive neighbors and visits no more other rows.",sources=["REF-105","IDEA-033"],config={"seed":42,"cars":24,"length_m":5000,"radii_m":[0,38,100,2500]},criteria={"neighbor_mismatches":criterion("eq",0),"extra_rows":criterion("le",0)},evaluate=exp_spatial.evaluate), "ordered_commands":dict(hypothesis="Stable priority ordering is permutation invariant on frozen synthetic commands.",
        sources=["REF-105","IDEA-033","IDEA-034"],config={"seed":42,"agents":24,"permutations":32},
        criteria={"state_mismatches":criterion("eq",0),"invalid_commands":criterion("eq",0)},evaluate=ordered_commands)}

def revision():
    checkout=Path(__file__).resolve().parent.parent
    sha=subprocess.check_output(["git","-C",str(checkout),"rev-parse","HEAD"],timeout=10,text=True).strip()
    reg.require(reg.sha40(sha),"exact checkout SHA")
    reg.require(not subprocess.check_output(["git","-C",str(checkout),"status","--porcelain","--untracked-files=all"],timeout=10),"reviewed clean checkout required")
    return sha,checkout

def run(root,name,ident,sha):
    # Called only with a fixed in-process experiment, never a user-provided executable.
    reg.experiment_id(ident); reg.require(reg.sha40(sha),"revision")
    catalog=specs(); reg.require(name in catalog,"unknown experiment")
    s=catalog[name]; config=s["config"]
    root.mkdir(mode=0o700); (root/"artifacts").mkdir(mode=0o700)
    p=dict(schema=1,id=ident,peer="foundation",hypothesis=s["hypothesis"],
           scope="Original isolated synthetic fixture; Foundation "+FOUNDATION+"; "+name,
           sources=s["sources"],repository=REPO,candidate_sha=sha,lab_sha=sha,baseline_sha=sha,kind="fixture",
           workload=dict(environment="Python standard library; synthetic",scenario=name,seed=config["seed"],
                         ticks=None,command_hash=reg.digest(config),authorization="offline_only"),criteria=s["criteria"])
    frozen=reg.register_plan(root,p)
    reg.publish_once(root/"configuration.json",config)
    result=s["evaluate"](config)
    metrics=result["metrics"]
    reg.require(set(metrics)==set(p["criteria"]) and all(reg.numeric(v) for v in metrics.values()),"experiment metrics")
    evidence={"schema":1,"experiment":name,"revision":sha,"plan_sha256":frozen["plan_sha256"],
              "configuration":config,"metrics":metrics,"observations":result["observations"],
              "origin":"SYNTHETIC","promotion":"NOT_AUTHORIZED"}
    artifact=root/"artifacts"/"observations.json"
    reg.publish_once(artifact,evidence)
    outcome="PASS" if all(reg.check(p["criteria"][k],v) for k,v in metrics.items()) else "FAIL"
    r=dict(schema=1,id=ident,plan_sha256=frozen["plan_sha256"],candidate_sha=sha,lab_sha=sha,status=outcome,
           metrics=metrics,evidence=[dict(file=artifact.name,sha256=reg.checksum(reg.bounded_bytes(artifact)))],
           limitations="Synthetic in-process reference and candidate at same Lab SHA; no game integration, real FPS or calibrated vehicle evidence.")
    summary=reg.register_result(root,r)
    return {**summary,"experiment":name,"metrics":metrics,"observations":result["observations"],"origin":"SYNTHETIC"}

def run_checkout(root,name,ident):
    sha,checkout=revision()
    reg.require(not root.resolve().is_relative_to(checkout),"registry must be outside checkout")
    return run(root,name,ident,sha)
