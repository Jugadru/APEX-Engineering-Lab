"""Four-lap rolling snapshot pit-window reference, not a sporting engine.

Open-loop plans use observed weather prefixes and an exogenous rival prior.
A no-service plan is legal only if no service is required in this horizon.
All timings, tyre profiles and traffic are synthetic; no physical track rank.
"""
from dataclasses import dataclass
from itertools import product
import random
from . import registry as reg, strategy_tyre as tyre, strategy_weather as weather, strategy_duel as duel, strategy_research as base

H=duel.HORIZON
COMPOUNDS=(*duel.SLICKS,"wet")
RATES=(100,600)
TOLERANCE=1000
NONE=(None,None)

@dataclass(frozen=True)
class State:
    duel_state:duel.Snapshot
    compound:str
    prefix:tuple
    required:bool
    earliest:int=0
    latest:int=H-1
    manual:int|None=None

def plans(s):
    reg.require(isinstance(s,State),"window state")
    duel.validate(s.duel_state)
    reg.require(isinstance(s.compound,str) and s.compound in COMPOUNDS,"compound")
    reg.require(type(s.prefix) is tuple and 1<=len(s.prefix)<=8,"prefix budget")
    weather.counts(s.prefix)
    reg.require(type(s.required) is bool and type(s.earliest) is int and type(s.latest) is int
                and 0<=s.earliest<=s.latest<H,"window bounds")
    reg.require(s.manual is None or (type(s.manual) is int and s.earliest<=s.manual<=s.latest),"manual lock")
    stops=(s.manual,) if s.manual is not None else range(s.earliest,s.latest+1)
    return (() if s.required or s.manual is not None else (NONE,))+tuple(product(stops,COMPOUNDS))

def forecasts(s):
    plans(s)
    c,k=weather.counts(s.prefix)
    # Unnormalized exact posterior × conditional path likelihood; common denominator.
    rows=[]
    for tail in product((False,True),repeat=H-1):
        path=(s.prefix[-1],)+tail
        flips=sum(a!=b for a,b in zip(path,path[1:]))
        weight=sum(r**(c+flips)*(1000-r)**(k+H-1-flips) for r in RATES)
        for rival in duel.FORECAST:
            rows.append((path,rival,weight))
    return tuple(rows)

def outcome(s,plan,path,rival):
    legal=plans(s)
    reg.require(type(plan) is tuple and len(plan)==2 and
                (plan==NONE or (type(plan[0]) is int and isinstance(plan[1],str))) and
                plan in legal,"legal plan")
    reg.require(type(path) is tuple and len(path)==H and all(type(x) is bool for x in path)
                and path[0]==s.prefix[-1],"realized weather")
    reg.require(type(rival) is tuple and rival in duel.FORECAST and all(type(x) is int for x in rival),"rival")
    d=s.duel_state;stop,new=plan;rstop,rpace=rival
    own=d.gap_ms;other=0;delay=0
    compound=s.compound;age=d.own_age;rcompound="medium";rage=d.rival_age
    for lap,wet in enumerate(path):
        if lap==rstop:
            other+=base.PIT_MS;rcompound="soft";rage=0
        if lap==stop:
            own+=base.PIT_MS;compound=new;age=0
            delay=duel.traffic_delay(own,[other]+[x+90000*lap for x in d.traffic_offsets])
        own+=tyre.lap_cost(compound,age,wet)
        other+=tyre.lap_cost(rcompound,rage,wet)+rpace
        age+=1;rage+=1
    return own+delay,other,delay

def table(s):
    candidates=plans(s);scenarios=forecasts(s);den=sum(w for _,_,w in scenarios)
    values={p:[outcome(s,p,path,rival) for path,rival,_ in scenarios] for p in candidates}
    def score(p):
        return sum(w*(v[0]-v[1]) for v,(_,_,w) in zip(values[p],scenarios))
    return candidates,scenarios,den,values,{p:score(p) for p in candidates}

def recommend(s):
    candidates,scenarios,den,values,scores=table(s)
    best=min(candidates,key=scores.get)
    # Explicit discrete set: a good early and late stop do not imply good middle stops.
    eligible=sorted({p[0] for p in candidates if p[0] is not None
                     and scores[p]-scores[best]<=TOLERANCE*den})
    per_lap=[]
    for lap in sorted({p[0] for p in candidates if p[0] is not None}):
        p=min((p for p in candidates if p[0]==lap),key=scores.get)
        per_lap.append(dict(lap=lap,compound=p[1],regret_ms=(scores[p]-scores[best])/den))
    wins=sum(w for i,(_,_,w) in enumerate(scenarios) if values[best][i][0]-values[best][i][1]
             <=min(values[p][i][0]-values[p][i][1] for p in candidates)+TOLERANCE)
    return dict(plan=best,first=eligible[0] if eligible else None,
                ideal=best[0],last=eligible[-1] if eligible else None,eligible=eligible,
                expected_gap_ms=scores[best]/den,per_lap=per_lap,
                no_stop_regret_ms=(scores[NONE]-scores[best])/den if NONE in scores else None,
                near_optimal_probability=wins/den,
                action="pit_now" if best[0]==0 else "wait")

def baseline(s):
    candidates=plans(s)
    if s.manual is not None:
        lap=s.manual
    else:
        lap=(s.earliest+s.latest)//2
    p=(lap,"wet" if s.prefix[-1] else "medium")
    return p if p in candidates else NONE

def reference(s,p,path,rival):
    """Segment sums, independent of the sequential outcome loop."""
    d=s.duel_state;k,new=p;rstop,pace=rival
    def elapsed(initial,age,start,k,new,end,rate):
        old=end if k is None else min(end,k)
        total=initial+sum(tyre.lap_cost(start,age+i,path[i]) for i in range(old))+end*rate
        if k is not None and k<end:
            total+=base.PIT_MS+sum(tyre.lap_cost(new,i-k,path[i]) for i in range(k,end))
        return total
    delay=0
    if k is not None:
        exit_ms=elapsed(d.gap_ms,d.own_age,s.compound,k,new,k,0)+base.PIT_MS
        rtime=elapsed(0,d.rival_age,"medium",rstop,"soft",k,pace)+base.PIT_MS*int(k==rstop)
        field=[rtime]+[x+90000*k for x in d.traffic_offsets]
        delay=duel.TRAFFIC_LOSS_MS if any(exit_ms-duel.TRAFFIC_WINDOW_MS<=x<=exit_ms for x in field) else 0
    return (elapsed(d.gap_ms,d.own_age,s.compound,k,new,H,0)+delay,
            elapsed(0,d.rival_age,"medium",rstop,"soft",H,pace),delay)

def evaluate(config):
    seed=config["seed"];n=config["cases"]
    reg.require(type(seed) is int and 0<=seed<=2**32 and type(n) is int and 1<=n<=96,"budget")
    metrics=dict(weight_mismatches=0,accounting_mismatches=0,invalid_actions=0,
                 optimum_violations=0,window_violations=0,replay_mismatches=0,negative_regret=0)
    grid=[State(duel.Snapshot(g,a,8,t),"medium",(wet,),req)
          for g,a,t,wet,req in product((-2000,2000),(4,18),((),(24000,27000)),(False,True),(False,True))]
    for s in grid:
        cs,sc,den,_,scores=table(s);r=recommend(s)
        c,k=weather.counts(s.prefix)
        expected=4*1000**(H-1)*sum(x**c*(1000-x)**k for x in RATES)
        metrics["weight_mismatches"]+=int(den!=expected)
        ref_scores={p:0 for p in cs}
        for p in cs:
            for path,rival,w in sc:
                v=reference(s,p,path,rival)
                metrics["accounting_mismatches"]+=int(outcome(s,p,path,rival)!=v)
                ref_scores[p]+=w*(v[0]-v[1])
        best=min(cs,key=ref_scores.get)
        metrics["optimum_violations"]+=int(r["plan"]!=best or scores!=ref_scores)
        eligible=sorted({p[0] for p in cs if p[0] is not None and ref_scores[p]-ref_scores[best]<=TOLERANCE*den})
        metrics["window_violations"]+=int(r["eligible"]!=eligible or r["first"]!=(eligible[0] if eligible else None)
            or r["last"]!=(eligible[-1] if eligible else None) or r["ideal"]!=best[0])
    rng=random.Random(seed);rows=[]
    totals={p:0 for p in ("fixed","window")}
    regrets={p:0 for p in totals}
    for i in range(n):
        prefix=tuple(bool(rng.randrange(2)) for _ in range(3))
        s=State(duel.Snapshot(rng.randrange(-5000,5001),rng.randrange(4,21),rng.randrange(4,21),
               tuple(sorted(rng.randrange(18000,33001) for _ in range(2)))),
               "wet" if prefix[-1] else "medium",prefix,bool(i%2),manual=2 if i%7==0 else None)
        r=recommend(s);selected={"fixed":baseline(s),"window":r["plan"]}
        metrics["replay_mismatches"]+=int(r!=recommend(s))
        # Realized path and opponent drawn only after choice; alternate rate outside prior.
        rate=(100,600,900)[i%3];path=[prefix[-1]]
        for _ in range(H-1):
            path.append(path[-1] ^ (rng.randrange(1000)<rate))
        path=tuple(path);rival=rng.choice(duel.FORECAST)
        oracle=min(reference(s,p,path,rival)[0] for p in plans(s))
        row=dict(case=i,rate=rate,required=s.required,manual=s.manual,weather=path)
        for policy,p in selected.items():
            metrics["invalid_actions"]+=int(p not in plans(s))
            v=outcome(s,p,path,rival);regret=v[0]-oracle
            metrics["accounting_mismatches"]+=int(v!=reference(s,p,path,rival))
            metrics["negative_regret"]+=int(regret<0)
            totals[policy]+=v[0];regrets[policy]+=regret
            row[policy]=dict(plan=p,elapsed_ms=v[0],regret_ms=regret)
        rows.append(row)
    return dict(metrics=metrics,observations=dict(grid_states=len(grid),forecast_scenarios=32,sampled_cases=n,
        mean_elapsed_ms={p:totals[p]/n for p in totals},mean_regret_ms={p:regrets[p]/n for p in regrets},rows=rows,
        limitations="Four-lap open-loop snapshot recommendation; recompute with a new observed state, not a full race replay. One or zero own services, synthetic binary weather, fixed rival prior, fixed traffic penalty, no inventory, physical pit lane or sporting integration. Near-optimal probability is model conditional, not calibrated confidence. Sample comparison exploratory."))

def spec(c):
    keys=("weight_mismatches","accounting_mismatches","invalid_actions","optimum_violations",
          "window_violations","replay_mismatches","negative_regret")
    return dict(hypothesis="Exact weighted pit-window candidates agree with independent segment accounting and legal optimum under the declared synthetic forecast; no hindsight in recommendation.",
                sources=["REF-106","IDEA-041","IDEA-045","IDEA-048"],
                config=dict(seed=20261202,cases=96),criteria={k:c("eq",0) for k in keys},evaluate=evaluate)
