"""Causal reactive rival in the four-lap strategy laboratory.

The own policy chooses an open-loop legal plan. The opponent sees only
frozen pre-service observations and completed earlier pit decisions.
No physical overtaking, game authority or calibrated strategist traits.
"""
from itertools import product
import random
from . import registry as reg, strategy_window as window, strategy_traffic as traffic, strategy_duel as duel, strategy_tyre as tyre, strategy_research as base

PROFILES=("cover","extend")
CLOSE=5000
CLIFF=4000
EXTEND_MARGIN=500

def rival_action(lap,nominal,profile,used,deferred,wet,age,compound,own_age,own_compound,gap,pace,previous_pit_gap):
    """Pure decision on a frozen pre-service observation; no own plan argument."""
    if used:
        return None,"spent"
    fresh="wet" if wet else "soft"
    if lap==window.H-1:
        return fresh,"deadline"
    if (compound=="wet")!=wet:
        return fresh,"weather"
    own_cost=tyre.lap_cost(own_compound,own_age,wet)
    rival_cost=tyre.lap_cost(compound,age,wet)+pace
    if tyre.lap_cost(compound,age,wet)-tyre.lap_cost(compound,0,wet)>=CLIFF:
        return fresh,"wear"
    if profile=="cover" and previous_pit_gap is not None and abs(previous_pit_gap)<=CLOSE:
        return fresh,"cover"
    if lap<nominal:
        return None,"wait"
    if profile=="extend" and not deferred and previous_pit_gap is None and abs(gap)<=CLOSE and rival_cost<=own_cost+EXTEND_MARGIN:
        return None,"extend"
    return fresh,"scheduled"

def scenarios(s):
    return tuple((path,rival,profile,weight) for path,rival,weight in window.forecasts(s.window_state) for profile in PROFILES)

def outcome(s,p,path,rival,profile):
    candidates=traffic.validate(s)
    reg.require(type(p) is tuple and len(p)==2 and (p==window.NONE or (type(p[0]) is int and isinstance(p[1],str))) and p in candidates,"legal plan")
    reg.require(type(path) is tuple and len(path)==window.H and all(type(x) is bool for x in path) and path[0]==s.window_state.prefix[-1],"weather")
    reg.require(type(rival) is tuple and len(rival)==2 and all(type(x) is int for x in rival) and rival in duel.FORECAST,"rival")
    reg.require(isinstance(profile,str) and profile in PROFILES,"profile")
    ws=s.window_state;d=ws.duel_state;nominal,pace=rival
    own=d.gap_ms;other=0;bg=list(d.traffic_offsets)
    oc=ws.compound;rc="medium";oa=d.own_age;ra=d.rival_age
    own_pit_gap=None;rstop=None;rnew=None;deferred=False;trace=[]
    for lap,wet in enumerate(path):
        gap=own-other
        action,reason=rival_action(lap,nominal,profile,rstop is not None,deferred,wet,ra,rc,oa,oc,gap,pace,own_pit_gap)
        oa_action=p[1] if p[0]==lap else None
        # Both decisions precede either service; only subsequent laps see own_pit_gap.
        if reason=="extend":
            deferred=True
        if action is not None:
            other+=base.PIT_MS;rc=action;ra=0;rstop=lap;rnew=action
        if oa_action is not None:
            own_pit_gap=gap;own+=base.PIT_MS;oc=oa_action;oa=0
        free=tyre.lap_cost(oc,oa,wet);rfree=tyre.lap_cost(rc,ra,wet)+pace
        costs=[tyre.lap_cost(c.compound,c.age+lap,wet)+c.pace_ms for c in s.background]
        # Reciprocal temporal pressure from the two focal cars; background stays exogenous.
        own_field=[(own-other,rfree)]+[(own-x,c) for x,c in zip(bg,costs)]
        rival_field=[(other-own,free)]+[(other-x,c) for x,c in zip(bg,costs)]
        od=traffic.loss(free,own_field)["loss_ms"]
        rd=traffic.loss(rfree,rival_field)["loss_ms"]
        trace.append(dict(lap=lap,own_action=oa_action,rival_action=action,reason=reason,
                          own_departure=own,rival_departure=other,own_free=free,rival_free=rfree,
                          own_field=own_field,rival_field=rival_field,own_delay=od,rival_delay=rd))
        own+=free+od;other+=rfree+rd;bg=[x+c for x,c in zip(bg,costs)];oa+=1;ra+=1
    return dict(own_ms=own,rival_ms=other,gap_ms=own-other,rival_stop=rstop,rival_compound=rnew,
                own_traffic_ms=sum(x["own_delay"] for x in trace),rival_traffic_ms=sum(x["rival_delay"] for x in trace),trace=trace)

def score(s,p,sc):
    return sum(w*outcome(s,p,path,rival,profile)["gap_ms"] for path,rival,profile,w in sc)

def choose(s):
    cs=traffic.validate(s);sc=scenarios(s)
    scores={p:score(s,p,sc) for p in cs}
    best=min(cs,key=scores.get)
    return dict(plan=best,baseline=traffic.choose(s)["plan"],expected_gap_ms=scores[best]/sum(x[3] for x in sc))

def audit(s,p,path,rival,profile,x,metrics,prefixes):
    d=s.window_state.duel_state;trace=x["trace"];own_actions=[];rival_actions=[]
    for i,row in enumerate(trace):
        # Same realized prefix and prior own actions must imply same rival action.
        key=(rival,profile,path[:i+1],tuple(own_actions))
        decision=(row["rival_action"],row["reason"])
        metrics["causality_violations"]+=int(prefixes.setdefault(key,decision)!=decision)
        own_actions.append(row["own_action"]);rival_actions.append(row["rival_action"])
        for side in ("own","rival"):
            loss=row[side+"_delay"]
            metrics["traffic_violations"]+=int(loss!=traffic.reference_loss(row[side+"_free"],row[side+"_field"])[0] or not 0<=loss<=traffic.CAP)
    own_stops=[(i,a) for i,a in enumerate(own_actions) if a is not None]
    rival_stops=[(i,a) for i,a in enumerate(rival_actions) if a is not None]
    metrics["illegal_stops"]+=int(own_stops!=([] if p==window.NONE else [p]) or len(rival_stops)!=1 or rival_stops!=[(x["rival_stop"],x["rival_compound"])])
    metrics["repeat_reactions"]+=int(sum(r["reason"]=="extend" for r in trace)>1 or sum(r["reason"]=="cover" for r in trace)>1)
    def clean(initial,age,compound,stops,pace):
        k,new=stops[0] if stops else (None,None)
        before=window.H if k is None else k
        cost=initial+sum(tyre.lap_cost(compound,age+i,path[i]) for i in range(before))+window.H*pace
        if k is not None:
            cost+=base.PIT_MS+sum(tyre.lap_cost(new,i-k,path[i]) for i in range(k,window.H))
        return cost
    for side,initial,age,compound,stops,pace in (("own",d.gap_ms,d.own_age,s.window_state.compound,own_stops,0),("rival",0,d.rival_age,"medium",rival_stops,rival[1])):
        delay=sum(r[side+"_delay"] for r in trace)
        metrics["accounting_mismatches"]+=int(x[side+"_ms"]!=clean(initial,age,compound,stops,pace)+delay or x[side+"_traffic_ms"]!=delay)
        clock=initial
        for row in trace:
            clock+=base.PIT_MS*int(row[side+"_action"] is not None)
            metrics["accounting_mismatches"]+=int(clock!=row[side+"_departure"])
            clock+=row[side+"_free"]+row[side+"_delay"]
        metrics["accounting_mismatches"]+=int(clock!=x[side+"_ms"])
    metrics["accounting_mismatches"]+=int(x["gap_ms"]!=x["own_ms"]-x["rival_ms"])

def evaluate(config):
    n=config["cases"];seed=config["seed"]
    reg.require(type(n) is int and 1<=n<=48 and type(seed) is int and 0<=seed<=2**32,"budget")
    metrics=dict(causality_violations=0,traffic_violations=0,illegal_stops=0,repeat_reactions=0,
                 accounting_mismatches=0,optimum_violations=0,replay_mismatches=0,negative_regret=0)
    grid=[traffic.State(window.State(duel.Snapshot(g,a,ra,offsets),"medium",(wet,),True),cars)
          for g,a,ra,wet,(offsets,cars) in product((-2000,2000),(4,18),(4,18),(False,True),
                    (((),()),((24000,),(traffic.Car("hard",10,500),))))]
    reasons={k:0 for k in ("cover","extend","weather","wear","deadline","scheduled")}
    for s in grid:
        cs=traffic.validate(s);sc=scenarios(s);prefixes={};scores={}
        for p in cs:
            scores[p]=0
            for path,rival,profile,w in sc:
                x=outcome(s,p,path,rival,profile)
                audit(s,p,path,rival,profile,x,metrics,prefixes)
                scores[p]+=w*x["gap_ms"]
                for row in x["trace"]:
                    if row["reason"] in reasons:
                        reasons[row["reason"]]+=1
        metrics["optimum_violations"]+=int(choose(s)["plan"]!=min(cs,key=scores.get))
    rng=random.Random(seed);rows=[];gaps={p:0 for p in ("prior","adaptive")};regrets=dict(gaps);wins=dict(gaps)
    for i in range(n):
        wet=bool(rng.randrange(2));offsets=(rng.randrange(18000,33001),)
        s=traffic.State(window.State(duel.Snapshot(rng.randrange(-5000,5001),rng.randrange(4,21),rng.randrange(4,21),offsets),
                 "wet" if wet else "medium",(wet,),bool(i%2),manual=2 if i%7==0 else None),
                 (traffic.Car("hard",rng.randrange(4,17),rng.randrange(-500,1001)),))
        r=choose(s);metrics["replay_mismatches"]+=int(r!=choose(s))
        # Draw the realized opponent and weather only after the own choice.
        rate=(100,600,900)[i%3];path=[wet]
        for _ in range(window.H-1):
            path.append(path[-1] ^ (rng.randrange(1000)<rate))
        path=tuple(path);rival=rng.choice(duel.FORECAST);profile=rng.choice(PROFILES)
        oracle=min(outcome(s,p,path,rival,profile)["gap_ms"] for p in traffic.validate(s))
        row=dict(case=i,weather=path,rival=rival,profile=profile,rate=rate,manual=s.window_state.manual)
        prefixes={}
        for policy,p in (("prior",r["baseline"]),("adaptive",r["plan"])):
            x=outcome(s,p,path,rival,profile);audit(s,p,path,rival,profile,x,metrics,prefixes)
            regret=x["gap_ms"]-oracle;metrics["negative_regret"]+=int(regret<0)
            gaps[policy]+=x["gap_ms"];regrets[policy]+=regret;wins[policy]+=int(x["gap_ms"]<0)
            row[policy]=dict(plan=p,gap_ms=x["gap_ms"],regret_ms=regret,rival_stop=x["rival_stop"],
                             rival_compound=x["rival_compound"],reasons=[z["reason"] for z in x["trace"]])
        rows.append(row)
    return dict(metrics=metrics,observations=dict(grid_states=len(grid),forecast_scenarios=64,sampled_cases=n,grid_reasons=reasons,
        mean_gap_ms={p:v/n for p,v in gaps.items()},mean_regret_ms={p:v/n for p,v in regrets.items()},wins=wins,rows=rows,
        limitations="Four-lap open-loop own plan versus one causal reactive rival, equal-weight cover/extend traits, reciprocal temporal pressure only for the focal pair, one rival stop. No future observations, physical passes, pit queue, calibrated behavior, game integration or superiority claim; sample comparison exploratory."))

def spec(c):
    keys=("causality_violations","traffic_violations","illegal_stops","repeat_reactions","accounting_mismatches",
          "optimum_violations","replay_mismatches","negative_regret")
    return dict(hypothesis="A reactive opponent obeys frozen observations and one-stop rules, timing reconciles, and response-aware open-loop choice minimizes declared expected gap.",
                sources=["REF-106","IDEA-041","IDEA-045","IDEA-048"],
                config=dict(seed=20261204,cases=48),criteria={k:c("eq",0) for k in keys},evaluate=evaluate)
