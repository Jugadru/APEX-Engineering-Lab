"""Bounded lap-boundary traffic forecast; no spatial passing or sporting state."""
from dataclasses import dataclass
from itertools import product
from fractions import Fraction
import random
from . import registry as reg, strategy_window as window, strategy_duel as duel, strategy_tyre as tyre, strategy_research as base

W=2000
CAP=3000
DENSITY=250

@dataclass(frozen=True)
class Car:
    compound:str
    age:int
    pace_ms:int=0

@dataclass(frozen=True)
class State:
    window_state:window.State
    background:tuple

def validate(s):
    reg.require(isinstance(s,State),"traffic state")
    candidates=window.plans(s.window_state)
    reg.require(type(s.background) is tuple and len(s.background)==len(s.window_state.duel_state.traffic_offsets),"background alignment")
    for c in s.background:
        reg.require(isinstance(c,Car) and isinstance(c.compound,str) and c.compound in window.COMPOUNDS
                    and type(c.age) is int and 0<=c.age<=20 and type(c.pace_ms) is int and -2000<=c.pace_ms<=2000,"background car")
    return candidates

def loss(own_cost,field):
    """Field rows are (our departure minus theirs, their free lap cost).
    Only cars ahead (including ties) and slower than us create pressure.
    Catch within one lap or within the residual proximity window is a proxy,
    not a collision or a prediction of completed passes.
    """
    reg.require(type(own_cost) is int and own_cost>0 and isinstance(field,(tuple,list)) and len(field)<=5,"traffic step")
    pressures=[]
    for row in field:
        reg.require(isinstance(row,(tuple,list)) and len(row)==2 and all(type(x) is int for x in row) and row[1]>0,"traffic row")
        gap,cost=row;adv=cost-own_cost
        if gap>=0 and adv>0:
            pressure=max(0,min(W,W+adv-gap))
            if pressure:
                pressures.append((adv,adv*pressure//W))
    if not pressures:
        return dict(loss_ms=0,affected=0,clear=True)
    # Never sum individual car delays; one shared congestion budget.
    largest=max(a for a,_ in pressures)
    delay=min(CAP,largest,max(v for _,v in pressures)+DENSITY*(len(pressures)-1))
    return dict(loss_ms=delay,affected=len(pressures),clear=False)

def reference_loss(own_cost,field):
    """Independent rational expression, then integer rounding."""
    active=[(cost-own_cost,Fraction(W+cost-own_cost-gap,W)) for gap,cost in field
            if gap>=0 and cost>own_cost and gap<W+cost-own_cost]
    if not active:
        return (0,0,True)
    values=[int(a*min(Fraction(1),p)) for a,p in active]
    return (min(CAP,max(a for a,_ in active),max(values)+DENSITY*(len(active)-1)),len(active),False)

def outcome(s,plan,path,rival):
    candidates=validate(s)
    reg.require(type(plan) is tuple and len(plan)==2 and (plan==window.NONE or
                (type(plan[0]) is int and isinstance(plan[1],str))) and plan in candidates,"legal plan")
    reg.require(type(path) is tuple and len(path)==window.H and all(type(x) is bool for x in path)
                and path[0]==s.window_state.prefix[-1],"weather")
    reg.require(type(rival) is tuple and len(rival)==2 and all(type(x) is int for x in rival)
                and rival in duel.FORECAST,"rival")
    ws=s.window_state;d=ws.duel_state;stop,new=plan;rstop,rpace=rival
    own=d.gap_ms;other=0;bg=list(d.traffic_offsets);age=d.own_age;rage=d.rival_age
    compound=ws.compound;rc="medium";trace=[]
    for lap,wet in enumerate(path):
        if lap==rstop:
            other+=base.PIT_MS;rc="soft";rage=0
        if lap==stop:
            own+=base.PIT_MS;compound=new;age=0
        free=tyre.lap_cost(compound,age,wet)
        rfree=tyre.lap_cost(rc,rage,wet)+rpace
        costs=[tyre.lap_cost(c.compound,c.age+lap,wet)+c.pace_ms for c in s.background]
        field=[(own-other,rfree)]+[(own-x,c) for x,c in zip(bg,costs)]
        step=loss(free,field)
        trace.append(dict(lap=lap,departure_ms=own,free_ms=free,field=field,**step))
        own+=free+step["loss_ms"];other+=rfree
        bg=[x+c for x,c in zip(bg,costs)]
        age+=1;rage+=1
    return dict(own_ms=own,rival_ms=other,gap_ms=own-other,
                traffic_ms=sum(r["loss_ms"] for r in trace),
                exit_clear=(trace[stop]["clear"] if stop is not None else None),trace=trace)

def choose(s):
    cs=validate(s);sc=window.forecasts(s.window_state);den=sum(w for _,_,w in sc)
    scores={};delays={};clears={}
    for p in cs:
        rows=[outcome(s,p,path,r) for path,r,_ in sc]
        scores[p]=sum(w*x["gap_ms"] for x,(_,_,w) in zip(rows,sc))
        delays[p]=sum(w*x["traffic_ms"] for x,(_,_,w) in zip(rows,sc))
        clears[p]=sum(w for x,(_,_,w) in zip(rows,sc) if x["exit_clear"] is True)
    best=min(cs,key=scores.get)
    old=window.recommend(s.window_state)["plan"]
    return dict(plan=best,baseline=old,expected_gap_ms=scores[best]/den,
                expected_traffic_ms=delays[best]/den,
                exit_clear_probability=clears[best]/den if best[0] is not None else None,
                eligible=sorted({p[0] for p in cs if p[0] is not None
                                 and scores[p]-scores[best]<=window.TOLERANCE*den}))

def audit(s,p,path,rival,result,metrics):
    # Legacy independent segment sum supplies the clean elapsed reference only.
    own,other,old_delay=window.reference(s.window_state,p,path,rival)
    trace=result["trace"];total=0
    for row in trace:
        expected=reference_loss(row["free_ms"],row["field"])
        actual=(row["loss_ms"],row["affected"],row["clear"])
        metrics["step_mismatches"]+=int(expected!=actual)
        metrics["bound_violations"]+=int(not 0<=row["loss_ms"]<=CAP or (row["clear"] and row["loss_ms"]!=0))
        metrics["order_violations"]+=int(loss(row["free_ms"],list(reversed(row["field"])))!=loss(row["free_ms"],row["field"]))
        total+=row["loss_ms"]
    metrics["accounting_mismatches"]+=int(result["own_ms"]!=own-old_delay+total or result["rival_ms"]!=other
        or result["traffic_ms"]!=total or result["gap_ms"]!=result["own_ms"]-other)
    metrics["accounting_mismatches"]+=sum(a["departure_ms"]+a["free_ms"]+a["loss_ms"]+
        (base.PIT_MS if p[0]==b["lap"] else 0)!=b["departure_ms"] for a,b in zip(trace,trace[1:]))

def evaluate(config):
    seed=config["seed"];n=config["cases"]
    reg.require(type(seed) is int and 0<=seed<=2**32 and type(n) is int and 1<=n<=64,"budget")
    metrics=dict(step_mismatches=0,bound_violations=0,order_violations=0,accounting_mismatches=0,
                 optimum_violations=0,invalid_actions=0,replay_mismatches=0,negative_regret=0)
    grid=[State(window.State(duel.Snapshot(g,a,8,offsets),"medium",(wet,),req),cars)
          for g,a,wet,req,(offsets,cars) in product((-2000,2000),(4,18),(False,True),(False,True),
            (((),()),((24000,24000),(Car("medium",8),Car("hard",12,500)))))]
    for s in grid:
        cs=validate(s);sc=window.forecasts(s.window_state);scores={}
        for p in cs:
            scores[p]=0
            for path,rival,w in sc:
                x=outcome(s,p,path,rival);audit(s,p,path,rival,x,metrics)
                scores[p]+=w*x["gap_ms"]
        choice=choose(s)
        metrics["optimum_violations"]+=int(choice["plan"]!=min(cs,key=scores.get))
    rng=random.Random(seed);rows=[];sums={p:0 for p in ("fixed_proxy","variable")}
    regrets=dict(sums);traffic=dict(sums)
    for i in range(n):
        wet=bool(rng.randrange(2))
        offsets=tuple(sorted(rng.randrange(18000,33001) for _ in range(2)))
        cars=tuple(Car(rng.choice(window.COMPOUNDS),rng.randrange(4,17),rng.randrange(-500,1001)) for _ in offsets)
        s=State(window.State(duel.Snapshot(rng.randrange(-5000,5001),rng.randrange(4,21),rng.randrange(4,21),offsets),
            "wet" if wet else "medium",(wet,),bool(i%2),manual=2 if i%7==0 else None),cars)
        r=choose(s);metrics["replay_mismatches"]+=int(r!=choose(s))
        rate=(100,600,900)[i%3];path=[wet]
        for _ in range(window.H-1):
            path.append(path[-1] ^ (rng.randrange(1000)<rate))
        path=tuple(path);rival=rng.choice(duel.FORECAST)
        oracle=min(outcome(s,p,path,rival)["own_ms"] for p in validate(s))
        row=dict(case=i,rate=rate,weather=path,rival=rival,offsets=offsets,
            background=[dict(compound=c.compound,age=c.age,pace_ms=c.pace_ms) for c in cars])
        for policy,p in (("fixed_proxy",r["baseline"]),("variable",r["plan"])):
            metrics["invalid_actions"]+=int(p not in validate(s))
            x=outcome(s,p,path,rival);audit(s,p,path,rival,x,metrics)
            regret=x["own_ms"]-oracle;metrics["negative_regret"]+=int(regret<0)
            sums[policy]+=x["own_ms"];regrets[policy]+=regret;traffic[policy]+=x["traffic_ms"]
            row[policy]=dict(plan=p,elapsed_ms=x["own_ms"],traffic_ms=x["traffic_ms"],regret_ms=regret)
        rows.append(row)
    return dict(metrics=metrics,observations=dict(grid_states=len(grid),forecast_scenarios=32,sampled_cases=n,
        mean_elapsed_ms={p:v/n for p,v in sums.items()},mean_regret_ms={p:v/n for p,v in regrets.items()},
        mean_traffic_ms={p:v/n for p,v in traffic.items()},rows=rows,
        limitations="Synthetic temporal pressure at equal-distance lap boundaries, capped per lap; all field cars except own have exogenous free pace, no physical passing or interaction response. Clear means no modeled slower-car pressure, not aerodynamic clean air. Both policies evaluated in same variable proxy; ranking exploratory, not external validation. No game integration."))

def spec(c):
    keys=("step_mismatches","bound_violations","order_violations","accounting_mismatches",
          "optimum_violations","invalid_actions","replay_mismatches","negative_regret")
    return dict(hypothesis="Variable congestion pressure respects bounds and permutation invariance; timing reconciles with independent clean segment reference, and forecast choice minimizes declared expected gap.",
                sources=["REF-106","IDEA-041","IDEA-045","IDEA-048"],
                config=dict(seed=20261203,cases=64),criteria={k:c("eq",0) for k in keys},evaluate=evaluate)
