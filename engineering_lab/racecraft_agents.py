"""Conservative batch feasibility reference, not a physically executable motion controller."""
from itertools import combinations
import random
from . import registry as reg, racecraft_core as core, racecraft_collision as collision, racecraft_space as space

def resolve(snapshot,proposals):
    reg.require(isinstance(proposals,dict),"proposals")
    ids=tuple(c.id for c in snapshot.cars if c.active)
    reg.require(all(type(i) is int for i in proposals) and set(proposals)==set(ids),"complete active proposal set")
    hold={i:collision.endpoint(snapshot.car(i).progress_mm,snapshot.car(i).lateral_mm) for i in ids}
    accepted={}
    for i in ids:
        collision.motion(snapshot,i,proposals[i])
        accepted[i]=dict(proposals[i])
    pairs=list(combinations(ids,2))
    initial=[(i,j) for i,j in pairs if collision.contact(snapshot,i,j,hold[i],hold[j])["contact"]]
    initial_set=set(initial)
    edge_margin=space.WIDTH_MM//2+space.BUFFER_MM
    limit=snapshot.half_width_mm-edge_margin
    initial_edge=[i for i in ids if abs(hold[i]["lateral_mm"])>limit]
    veto=set(initial_edge)|{i for i in ids if abs(accepted[i]["lateral_mm"])>limit}|{i for pair in initial for i in pair}
    for i in veto: accepted[i]=hold[i].copy()
    rounds=0
    # Each productive iteration removes at least one nonstationary proposal.
    # Stationary endpoints cannot generate a new contact between initially
    # separated pairs. Therefore a fixed point exists in <= N+1 scans.
    for _ in range(len(ids)+1):
        rounds+=1; new=set()
        for i,j in pairs:
            if (i,j) not in initial_set and collision.contact(snapshot,i,j,accepted[i],accepted[j])["contact"]:
                new.update((i,j))  # Record both conflict participants, including already stationary cars.
        if not new: break
        reg.require(any(accepted[i]!=hold[i] for i in new),"unresolved stationary conflict")
        for i in new: accepted[i]=hold[i].copy()
        veto.update(new)
    remaining=[(i,j) for i,j in pairs if (i,j) not in initial_set and collision.contact(snapshot,i,j,accepted[i],accepted[j])["contact"]]
    reg.require(not remaining,"new contact remains after bounded veto")
    return {"endpoints":[dict(id=i,**accepted[i]) for i in ids],"vetoed_ids":sorted(veto),
            "initial_contacts":[list(pair) for pair in initial],"initial_edge_ids":initial_edge,
            "new_contacts":[list(pair) for pair in remaining],"rounds":rounds,
            "status":"INITIAL_STATE_INVALID" if initial or initial_edge else "GEOMETRICALLY_FEASIBLE",
            "meaning":"STATIONARY_FALLBACK_IS_NOT_PHYSICAL_BRAKING"}

def evaluate(config):
    rng=random.Random(config["seed"]); L=5000000
    cases=[
      ("swap",[core.row(1,100000,-3000),core.row(2,100000,3000)],{1:collision.endpoint(110000,3000),2:collision.endpoint(110000,-3000)}),
      ("chain",[core.row(1,100000),core.row(2,110000),core.row(3,120000)],{1:collision.endpoint(110000,0),2:collision.endpoint(120000,0),3:collision.endpoint(120000,0)}),
      ("parallel",[core.row(1,100000,-3000),core.row(2,100000,3000)],{1:collision.endpoint(120000,-3000),2:collision.endpoint(120000,3000)}),
      ("initial",[core.row(1,100000),core.row(2,100000),core.row(3,90000)],{1:collision.endpoint(110000,0),2:collision.endpoint(110000,0),3:collision.endpoint(105000,0)}),
      ("edge",[core.row(1,100000,4500)],{1:collision.endpoint(120000,3000)})]
    for i in range(config["random_cases"]):
        rows=[core.row(j,(L-20000+j*7000)%L,(-1)**j*2500,40000,j%7!=0) for j in range(24)]
        props={r["id"]:collision.endpoint(r["progress_mm"]+rng.randrange(25001),rng.choice([-3000,0,3000,4500])) for r in rows if r["active"]}
        cases.append(("seeded-"+str(i),rows,props))
    mismatches=invalid=initial_cases=veto_cases=clear_cases=max_rounds=0; details=[]
    for label,rows,props in cases:
        s=core.Snapshot.from_rows(0,L,5000,rows); got=resolve(s,props)
        alt=resolve(core.Snapshot.from_rows(0,L,5000,rows[::-1]),dict(reversed(list(props.items()))))
        mismatches+=got!=alt
        endpoint={r["id"]:collision.endpoint(r["progress_mm"],r["lateral_mm"]) for r in got["endpoints"]}
        ids=sorted(props); initial_pairs={tuple(p) for p in got["initial_contacts"]}
        for i,j in combinations(ids,2):
            observed=collision.oracle(s,i,j,endpoint[i],endpoint[j])
            if (i,j) not in initial_pairs: invalid+=observed["contact"]
            else: invalid+=not observed["initial_contact"]
        for i in ids:
            a=s.car(i); out=endpoint[i]
            invalid+=out not in (props[i],collision.endpoint(a.progress_mm,a.lateral_mm))
            invalid+=abs(out["lateral_mm"])>3800 and i not in got["initial_edge_ids"]
        invalid+=got["rounds"]>len(ids)+1
        initial_cases+=got["status"]=="INITIAL_STATE_INVALID"
        veto_cases+=bool(got["vetoed_ids"]); clear_cases+=not got["vetoed_ids"]
        max_rounds=max(max_rounds,got["rounds"])
        details.append(dict(scenario=label,active=len(ids),vetoes=len(got["vetoed_ids"]),rounds=got["rounds"],status=got["status"]))
    return {"metrics":{"permutation_mismatches":mismatches,"invalid_resolutions":invalid,
                       "missing_modes":int(not initial_cases)+int(not veto_cases)+int(not clear_cases)},
            "observations":{"cases":len(cases),"initial_invalid_cases":initial_cases,"veto_cases":veto_cases,
                            "unvetoed_cases":clear_cases,"max_rounds":max_rounds,"rows":details,
                            "limitations":"Conservative geometric batch veto may stop all agents and cause deadlock; stationary fallback is not acceleration-limited braking. No sporting motion or performance claim."}}

def spec(c):
    return dict(hypothesis="Conservative batch veto is permutation invariant, bounded, and introduces no new swept contact in the linear toy geometry.",
        sources=["REF-105","IDEA-030","IDEA-033","IDEA-034","IDEA-040"],config={"seed":42,"random_cases":16},
        criteria={"permutation_mismatches":c("eq",0),"invalid_resolutions":c("eq",0),"missing_modes":c("eq",0)},evaluate=evaluate)
