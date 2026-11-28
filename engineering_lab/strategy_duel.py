"""One-pit dry strategic duel over a four-lap window, with exogenous traffic.

Timing is elapsed time at equal-distance lap boundaries, not a spatial
overtaking or pit-lane simulation. Forecast alternatives never see the
realized rival schedule. All costs are artificial integer milliseconds.
"""
from dataclasses import dataclass
from itertools import product
import random
from . import registry as reg, strategy_tyre as tyre, strategy_research as base

HORIZON=4
SLICKS=("soft","medium","hard")
PLANS=tuple(product(range(HORIZON),SLICKS))
# Equal weight, known forecast distribution, independent realized draw.
FORECAST=tuple(product((1,2),(-500,500)))
TRAFFIC_WINDOW_MS=2000
TRAFFIC_LOSS_MS=1500

@dataclass(frozen=True)
class Snapshot:
    gap_ms:int
    own_age:int
    rival_age:int
    traffic_offsets:tuple

def validate(s):
    reg.require(isinstance(s,Snapshot),"snapshot")
    reg.require(type(s.gap_ms) is int and -5000<=s.gap_ms<=5000,"initial gap")
    reg.require(all(type(a) is int and 0<=a<=20 for a in (s.own_age,s.rival_age)),"tyre ages")
    reg.require(type(s.traffic_offsets) is tuple and len(s.traffic_offsets)<=4 and
                all(type(x) is int and 0<=x<=50000 for x in s.traffic_offsets) and
                tuple(sorted(s.traffic_offsets))==s.traffic_offsets,"traffic offsets")

def validate_plan(plan):
    reg.require(isinstance(plan,(tuple,list)) and len(plan)==2 and type(plan[0]) is int and
                0<=plan[0]<HORIZON and plan[1] in SLICKS,"pit plan")

def timeline(offset,age,plan,pace=0):
    """Entry, post-service departure and lap-end times at common boundaries."""
    validate_plan(plan)
    reg.require(type(offset) is int and -5000<=offset<=5000 and type(age) is int and 0<=age<=20 and
                type(pace) is int and -1000<=pace<=1000,"timeline state")
    stop,compound=plan;current="medium";clock=offset;rows=[]
    for lap in range(HORIZON):
        entry=clock
        if lap==stop:
            clock+=base.PIT_MS;current=compound;age=0
        depart=clock
        cost=tyre.lap_cost(current,age,False)+pace;clock+=cost
        rows.append(dict(lap=lap,entry_ms=entry,departure_ms=depart,end_ms=clock,compound=current,age=age))
        age+=1
    return rows

def traffic_delay(departure,other_departures):
    # Equal-boundary time proxy: another car crossed just before us.
    reg.require(type(departure) is int and isinstance(other_departures,(tuple,list)) and
                all(type(x) is int for x in other_departures),"traffic timing")
    return TRAFFIC_LOSS_MS if any(0<=departure-x<=TRAFFIC_WINDOW_MS for x in other_departures) else 0

def simulate(s,plan,rival):
    validate(s);validate_plan(plan)
    reg.require(isinstance(rival,(tuple,list)) and len(rival)==2 and all(type(x) is int for x in rival) and tuple(rival) in FORECAST,"rival scenario")
    stop,compound=plan;rstop,pace=rival
    own=timeline(s.gap_ms,s.own_age,plan)
    other=timeline(0,s.rival_age,(rstop,"soft"),pace)
    exit_ms=own[stop]["departure_ms"]
    # Same boundary departure times: include rival's service if simultaneous.
    exits=[other[stop]["departure_ms"]]+[x+90000*stop for x in s.traffic_offsets]
    delay=traffic_delay(exit_ms,exits)
    finish=own[-1]["end_ms"]+delay;rfinish=other[-1]["end_ms"]
    finish_order=[rfinish]+[x+90000*HORIZON for x in s.traffic_offsets]
    return dict(stop=stop,compound=compound,rival_stop=rstop,
                tactic="undercut" if stop<rstop else "overcut" if stop>rstop else "same_lap",
                exit_ms=exit_ms,exit_rank=1+sum(x<=exit_ms for x in exits),
                traffic_ms=delay,own_finish_ms=finish,rival_finish_ms=rfinish,
                gap_ms=finish-rfinish,finish_rank=1+sum(x<=finish for x in finish_order),
                ahead=finish<rfinish)

def reference_result(s,plan,rival):
    """Independent prefix/segment accounting for audit; no timeline or simulate calls."""
    stop,compound=plan;rstop,pace=rival
    def crossing(initial,age,k,new,rate,boundary,after_service):
        old_laps=min(boundary,k)
        new_laps=max(0,boundary-k)
        return (initial+sum(tyre.lap_cost("medium",age+i,False) for i in range(old_laps))
                +sum(tyre.lap_cost(new,i,False) for i in range(new_laps))
                +boundary*rate+base.PIT_MS*int(boundary>k or (boundary==k and after_service)))
    own_exit=crossing(s.gap_ms,s.own_age,stop,compound,0,stop,True)
    rival_exit=crossing(0,s.rival_age,rstop,"soft",pace,stop,True)
    exit_field=[rival_exit]+[x+90000*stop for x in s.traffic_offsets]
    traffic=1500 if any(own_exit-2000<=x<=own_exit for x in exit_field) else 0
    own_finish=crossing(s.gap_ms,s.own_age,stop,compound,0,HORIZON,False)+traffic
    rival_finish=crossing(0,s.rival_age,rstop,"soft",pace,HORIZON,False)
    finish_field=[rival_finish]+[x+90000*HORIZON for x in s.traffic_offsets]
    # Equal timestamps are ranked conservatively after the other cars.
    exit_rank=sorted(exit_field+[own_exit]).index(own_exit)+exit_field.count(own_exit)+1
    finish_rank=sorted(finish_field+[own_finish]).index(own_finish)+finish_field.count(own_finish)+1
    return dict(exit_ms=own_exit,traffic_ms=traffic,own_finish_ms=own_finish,
                rival_finish_ms=rival_finish,gap_ms=own_finish-rival_finish,
                exit_rank=exit_rank,finish_rank=finish_rank,ahead=own_finish<rival_finish,
                tactic=("undercut" if stop<rstop else "overcut" if stop>rstop else "same_lap"))

def reference_score(s,plan):
    rows=[reference_result(s,plan,rival) for rival in FORECAST]
    return (sum(x["gap_ms"]>=0 for x in rows),sum(x["gap_ms"] for x in rows),
            sum(x["own_finish_ms"] for x in rows))

def audit_result(metrics,s,p,rival,x):
    expected=reference_result(s,p,rival)
    metrics["accounting_mismatches"]+=int(any(x[k]!=expected[k] for k in
        ("exit_ms","traffic_ms","own_finish_ms","rival_finish_ms","gap_ms","tactic")))
    metrics["rank_violations"]+=int(any(x[k]!=expected[k] for k in
        ("exit_rank","finish_rank","ahead")))

def score(s,plan):
    rows=[simulate(s,plan,rival) for rival in FORECAST]
    # First objective is non-wins: an exact tie is conservatively not a win.
    return (sum(not x["ahead"] for x in rows),sum(x["gap_ms"] for x in rows),
            sum(x["own_finish_ms"] for x in rows))

def choose(s):
    validate(s)
    # Baseline ignores opponent and traffic; same tyre model and action space.
    # min is stable: the first candidate wins an exact tie.
    solo=min(PLANS,key=lambda p:timeline(s.gap_ms,s.own_age,p)[-1]["end_ms"])
    ranked=min(PLANS,key=lambda p:score(s,p))
    return dict(solo=solo,duel=ranked)

def evaluate(config):
    seed=config["seed"];n=config["cases"]
    reg.require(type(seed) is int and 0<=seed<=2**32 and type(n) is int and 1<=n<=128,"fixture budget")
    # Fixed boundary grid, then independent sampled states and realized rivals.
    grid=[Snapshot(g,a,b,t) for g,a,b,t in product((-3000,0,3000),(4,10),(4,10),((),(24000,27000)))]
    metrics=dict(score_violations=0,invalid_actions=0,accounting_mismatches=0,
                 rank_violations=0,replay_mismatches=0,negative_hindsight_regret=0)
    for s in grid:
        plans=choose(s)
        metrics["score_violations"]+=int(plans["duel"]!=min(PLANS,key=lambda p:reference_score(s,p)))
        for p in PLANS:
            for rival in FORECAST:
                audit_result(metrics,s,p,rival,simulate(s,p,rival))
    rng=random.Random(seed);rows=[]
    totals={p:dict(wins=0,gap=0,traffic=0,undercut=0,overcut=0,same_lap=0) for p in ("solo","duel")}
    for i in range(n):
        s=Snapshot(rng.randrange(-5000,5001),rng.randrange(4,13),rng.randrange(4,13),
                   tuple(sorted({rng.randrange(18000,33001) for _ in range(2)})))
        plans=choose(s) # frozen before realizing rival
        realized=FORECAST[rng.randrange(len(FORECAST))]
        oracle=min(reference_result(s,p,realized)["gap_ms"] for p in PLANS)
        metrics["score_violations"]+=int(plans["duel"]!=min(PLANS,key=lambda p:reference_score(s,p)))
        row=dict(case=i,snapshot=dict(gap_ms=s.gap_ms,own_age=s.own_age,rival_age=s.rival_age,
                                     traffic_offsets=s.traffic_offsets),rival=realized)
        metrics["replay_mismatches"]+=int(plans!=choose(s))
        for policy,plan in plans.items():
            metrics["invalid_actions"]+=int(plan not in PLANS)
            x=simulate(s,plan,realized);metrics["replay_mismatches"]+=int(x!=simulate(s,plan,realized))
            audit_result(metrics,s,plan,realized,x)
            metrics["negative_hindsight_regret"]+=int(x["gap_ms"]<oracle)
            t=totals[policy];t["wins"]+=int(x["ahead"]);t["gap"]+=x["gap_ms"];t["traffic"]+=x["traffic_ms"];t[x["tactic"]]+=1
            row[policy]=x
        rows.append(row)
    summary={p:dict(wins=t["wins"],mean_gap_ms=t["gap"]/n,mean_traffic_ms=t["traffic"]/n,
                    undercut=t["undercut"],overcut=t["overcut"],same_lap=t["same_lap"]) for p,t in totals.items()}
    return dict(metrics=metrics,observations=dict(grid_cases=len(grid),evaluated_grid_plans=len(grid)*len(PLANS)*len(FORECAST),
        sampled_cases=n,summary=summary,rows=rows,
        limitations="Four-lap dry one-stop open-loop duel, equal-weight known rival forecasts, fixed rival and background pace, one lap-exit traffic delay. Rank is equal-distance crossing order proxy, not actual track position. No rival response, passing physics, pit queue, team coordination or sporting integration. Sampled win/gap ranking exploratory."))

def spec(c):
    keys=("score_violations","invalid_actions","accounting_mismatches","rank_violations","replay_mismatches","negative_hindsight_regret")
    return dict(hypothesis="A causal forecast-aware pit window minimizes lexicographic expected rival loss count and gap over the same action space as solo planning; legal and reconciled timing.",
                sources=["REF-106","IDEA-041","IDEA-045","IDEA-048"],
                config=dict(seed=20261201,cases=96),criteria={k:c("eq",0) for k in keys},evaluate=evaluate)
