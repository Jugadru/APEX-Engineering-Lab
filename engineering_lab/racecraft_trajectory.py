"""Bounded offline discrete trajectory optimization; not a real racing line."""
from itertools import product
import random
from . import registry as reg, racecraft_core as core

def validate(stations,preferred,max_step):
    reg.require(isinstance(stations,(list,tuple)) and 2<=len(stations)<=7,"station count")
    reg.require(isinstance(preferred,(list,tuple)) and len(preferred)==len(stations),"preference length")
    core.integer(max_step,0,10000,"step bound")
    for p in preferred: core.integer(p,-15000,15000,"preference")
    for options in stations:
        reg.require(isinstance(options,(list,tuple)) and len(options)<=4,"candidate count")
        for x in options: core.integer(x,-15000,15000,"offset")
        reg.require(len(set(options))==len(options),"duplicate offset")

def score(path,preferred):
    # Integer cost in squared mm; weights are artificial, not travel time.
    return sum((x-p)**2 for x,p in zip(path,preferred))+sum((b-a)**2 for a,b in zip(path,path[1:]))+2*sum((c-2*b+a)**2 for a,b,c in zip(path,path[1:],path[2:]))

def exhaustive(stations,preferred,max_step):
    validate(stations,preferred,max_step)
    best=None; evaluated=0
    for path in product(*stations):
        if any(abs(a-b)>max_step for a,b in zip(path,path[1:])): continue
        evaluated+=1
        item=(score(path,preferred),path)
        if best is None or item<best: best=item
    return {"path_mm":list(best[1]) if best else None,"cost_mm2":best[0] if best else None,"evaluated_paths":evaluated}

def optimize(stations,preferred,max_step):
    validate(stations,preferred,max_step)
    # Keep best prefix per last two offsets; costs depend on no earlier state.
    states={(None,x):((x-preferred[0])**2,(x,)) for x in sorted(stations[0])}
    transitions=0
    for k in range(1,len(stations)):
        next_states={}
        for (a,b),(cost,path) in sorted(states.items(),key=lambda item:item[1]):
            for x in sorted(stations[k]):
                if abs(x-b)>max_step: continue
                transitions+=1
                penalty=(x-preferred[k])**2+(x-b)**2+(2*(x-2*b+a)**2 if a is not None else 0)
                key=(b,x); item=(cost+penalty,path+(x,))
                if key not in next_states or item<next_states[key]: next_states[key]=item
        states=next_states
    best=min(states.values(),default=None)
    return {"path_mm":list(best[1]) if best else None,"cost_mm2":best[0] if best else None,"transitions":transitions}

def evaluate(config):
    rng=random.Random(config["seed"]); offsets=[-2000,0,2000]
    scenarios=[
        ("straight",[offsets]*5,[0]*5,2000),
        ("alternating",[offsets]*5,[-2000,2000,-2000,2000,-2000],2000),
        ("forced",[[-2000],offsets,[2000],offsets,[0]],[0]*5,2000),
        ("disconnected",[[-2000],[2000],[0]],[0]*3,2000),
        ("no_space",[offsets,[],offsets],[0]*3,2000)]
    for i in range(config["random_cases"]):
        stations=[[x for x in offsets if rng.randrange(4)!=0] for _ in range(6)]
        scenarios.append(("seeded-"+str(i),stations,[rng.choice(offsets) for _ in stations],rng.choice([0,2000,4000])))
    mismatch=invalid=permutation=feasible=blocked=0; rows=[]
    for name,stations,prefs,limit in scenarios:
        ref=exhaustive(stations,prefs,limit); got=optimize(stations,prefs,limit)
        keys=("path_mm","cost_mm2")
        mismatch+=any(ref[k]!=got[k] for k in keys)
        reversed_result=optimize([list(reversed(x)) for x in stations],prefs,limit)
        permutation+=any(got[k]!=reversed_result[k] for k in keys)
        path=got["path_mm"]
        if path is None: blocked+=1
        else:
            feasible+=1
            invalid+=not (len(path)==len(stations) and all(x in opts for x,opts in zip(path,stations)) and
                           all(abs(a-b)<=limit for a,b in zip(path,path[1:])) and score(path,prefs)==got["cost_mm2"])
        rows.append({"scenario":name,**got,"oracle_feasible_paths":ref["evaluated_paths"]})
    return {"metrics":{"oracle_mismatches":mismatch,"invalid_paths":invalid,"permutation_mismatches":permutation,
                       "missing_modes":int(not feasible)+int(not blocked)},
            "observations":{"cases":len(rows),"feasible":feasible,"infeasible":blocked,"rows":rows,
                            "limitations":"Sampled station offsets and integer smoothness cost only; no continuous track, lateral dynamics, real lap-time optimization or safety between stations."}}

def spec(c):
    return dict(hypothesis="Dynamic programming returns the same optimal discrete path and tie order as exhaustive search, respecting admissible offsets and step bounds.",
        sources=["REF-109","IDEA-021","IDEA-023","IDEA-024","IDEA-034"],
        config={"seed":42,"random_cases":24},
        criteria={"oracle_mismatches":c("eq",0),"invalid_paths":c("eq",0),"permutation_mismatches":c("eq",0),"missing_modes":c("eq",0)},evaluate=evaluate)
