"""Bounded causal multi-stint extension of the existing synthetic weather model.

At least one and at most three pit stops; one action before each lap.
No inventory, race rules, calibrated compounds, or game integration.
"""
from fractions import Fraction
from functools import lru_cache
from itertools import product
import random
from . import registry as reg, strategy_research as base, strategy_adaptive as adaptive, strategy_weather as weather

POLICIES=("single_stop","multi_stop")
ACTIONS=(None,"dry","wet") # tie: conserve stop, then dry, then wet

def validate_budget(minimum,maximum):
    reg.require(type(minimum) is int and type(maximum) is int and 0<=minimum<=maximum<=3,"pit budget")

def controller(rates,minimum=1,maximum=3):
    rates=weather.validate_rates(rates)
    validate_budget(minimum,maximum)
    @lru_cache(maxsize=24000)
    def value(remaining,tyre,age,wet,used,changes,stays):
        p=weather.forecast(rates,changes,stays)
        rows=[]
        for action in ACTIONS:
            next_used=used+int(action is not None)
            if next_used>maximum or next_used+remaining-1<minimum:
                continue
            new=tyre if action is None else action
            new_age=age if action is None else 0
            cost=Fraction(base.lap_cost(new,new_age,wet)+(base.PIT_MS if action is not None else 0))
            if remaining>1:
                cost+=(1-p)*value(remaining-1,new,new_age+1,wet,next_used,changes,stays+1)[0]
                cost+=p*value(remaining-1,new,new_age+1,not wet,next_used,changes+1,stays)[0]
            rows.append((cost,ACTIONS.index(action),action))
        reg.require(bool(rows),"no feasible pit plan")
        best=min(rows)
        return best[0],best[2]
    def solve(remaining,tyre,age,prefix,used=0):
        c,s=weather.counts(prefix)
        reg.require(type(remaining) is int and 1<=remaining<=8 and len(prefix)+remaining-1<=8,"stint horizon")
        reg.require(type(used) is int and 0<=used<=maximum and used<=len(prefix)-1 and used+remaining>=minimum,"stops used")
        base.lap_cost(tyre,age,prefix[-1])
        reg.require(age+remaining-1<=32,"stint age domain")
        return value(remaining,tyre,age,prefix[-1],used,c,s)
    return solve

def replay(path,choose,minimum=1,maximum=3):
    validate_budget(minimum,maximum)
    reg.require(isinstance(path,(tuple,list)) and 2<=len(path)<=8 and all(type(w) is bool for w in path) and minimum<=len(path),"weather path")
    tyre="dry";age=4;stops=[];trace=[];total=0
    for lap,wet in enumerate(path):
        action=choose(len(path)-lap,tyre,age,tuple(path[:lap+1]),len(stops))[1]
        reg.require(action in ACTIONS,"invalid action")
        if action is not None:
            reg.require(len(stops)<maximum,"pit budget exceeded")
            stops.append((lap,action));tyre=action;age=0;total+=base.PIT_MS
        reg.require(len(stops)+len(path)-lap-1>=minimum,"mandatory pit infeasible")
        cost=base.lap_cost(tyre,age,wet);total+=cost
        trace.append(dict(lap=lap,wet=wet,action=action,tyre=tyre,age=age,cost_ms=cost,stops_used=len(stops)))
        age+=1
    reg.require(minimum<=len(stops)<=maximum,"pit count")
    return dict(total_ms=total,stops=stops,trace=trace)

def plan_cost(path,stops,minimum=1,maximum=3):
    validate_budget(minimum,maximum)
    reg.require(isinstance(path,(tuple,list)) and 2<=len(path)<=8 and all(type(w) is bool for w in path),"weather path")
    reg.require(isinstance(stops,(tuple,list)) and minimum<=len(stops)<=maximum,"pit count")
    last=-1;total=0;start=0;tyre="dry";age=4
    # Separate stint-sum evaluator, including service cost even on lap zero.
    for row in stops:
        reg.require(isinstance(row,(tuple,list)) and len(row)==2,"pit record")
        lap,compound=row
        reg.require(type(lap) is int and last<lap<len(path) and compound in base.TYRES,"pit order or compound")
        total+=sum(base.lap_cost(tyre,age+i,path[start+i]) for i in range(lap-start))+base.PIT_MS
        last=lap;start=lap;tyre=compound;age=0
    total+=sum(base.lap_cost(tyre,age+i,path[start+i]) for i in range(len(path)-start))
    return total

def hindsight(path,minimum=1,maximum=3):
    validate_budget(minimum,maximum)
    reg.require(isinstance(path,(tuple,list)) and 2<=len(path)<=8 and all(type(w) is bool for w in path) and minimum<=len(path),"weather path")
    # Independent complete-plan enumeration; never called by a controller.
    from itertools import combinations
    return min(plan_cost(path,list(zip(laps,types)),minimum,maximum)
               for n in range(minimum,min(maximum,len(path))+1)
               for laps in combinations(range(len(path)),n)
               for types in product(base.TYRES,repeat=n))

def exact(h,rates):
    rates=weather.validate_rates(rates)
    reg.require(type(h) is int and 2<=h<=8,"enumeration budget")
    policies={"single_stop":controller(rates,1,1),"multi_stop":controller(rates,1,3)}
    totals={p:0 for p in POLICIES};stop_totals={p:0 for p in POLICIES}
    prefixes={p:{} for p in POLICIES}
    weights=invalid=causal=compat=0
    denom=4*1000**(h-1)
    old=weather.controller(rates)
    for path in product((False,True),repeat=h):
        w=sum(adaptive.weight(path,r) for r in rates);weights+=w
        original=weather.replay(path,lambda remaining,tyre,age,prefix,horizon:old(remaining,tyre,age,prefix)[1])
        for p,choose in policies.items():
            cap=1 if p=="single_stop" else 3
            result=replay(path,choose,1,cap)
            invalid+=result["total_ms"]!=plan_cost(path,result["stops"],1,cap)
            invalid+=len(result["stops"])!=sum(x["action"] is not None for x in result["trace"])
            totals[p]+=w*result["total_ms"];stop_totals[p]+=w*len(result["stops"])
            if cap==1:
                # Ties may choose another equally valued plan; compare expected
                # value separately, not per-path cost or stop timing.
                compat+=int(len(result["stops"])!=1 or original["stop"] is None)
            for i,row in enumerate(result["trace"]):
                prefix=path[:i+1];causal+=row!=prefixes[p].setdefault(prefix,row)
    wants={p:sum((solve(h,"dry",4,(wet,))[0] for wet in (False,True)),Fraction())/2 for p,solve in policies.items()}
    old_value=sum((old(h,"dry",4,(wet,))[0] for wet in (False,True)),Fraction())/2
    return dict(paths=2**h,expected_cost_ms={p:totals[p]/denom for p in POLICIES},
                expected_stops={p:stop_totals[p]/denom for p in POLICIES},
                metrics=dict(weight_mismatches=int(weights!=denom),
                             bellman_mismatches=sum(wants[p]!=Fraction(totals[p],denom) for p in POLICIES),
                             single_stop_mismatches=compat+int(wants["single_stop"]!=old_value),
                             dominance_violations=int(totals["multi_stop"]>totals["single_stop"]),
                             invalid_actions=invalid,causality_violations=causal))

def evaluate(config):
    h=config["horizon"];n=config["cases_per_regime"];seed=config["seed"];rates=weather.validate_rates(config["rates"])
    regimes=config["holdout_rates"]
    reg.require(type(h) is int and 2<=h<=8 and type(n) is int and 1<=n<=32 and type(seed) is int and 0<=seed<=2**32,"experiment budget")
    reg.require(isinstance(regimes,list) and 1<=len(regimes)<=4 and all(type(r) is int and 0<=r<=1000 for r in regimes) and regimes==sorted(set(regimes)),"holdout regimes")
    result=exact(h,rates);metrics=dict(result.pop("metrics"),negative_regret=0,replay_mismatches=0)
    rng=random.Random(seed);policies={"single_stop":controller(rates,1,1),"multi_stop":controller(rates,1,3)};groups=[]
    for regime in regimes:
        totals={p:0 for p in POLICIES};regrets={p:0 for p in POLICIES};counts={p:0 for p in POLICIES};rows=[]
        for i in range(n):
            path=base.weather_path(rng,bool(rng.randrange(2)),h,regime)
            oracle=hindsight(path);row=dict(case=i,weather=path,oracle_ms=oracle)
            for p,choose in policies.items():
                cap=1 if p=="single_stop" else 3
                observed=replay(path,choose,1,cap)
                metrics["replay_mismatches"]+=observed!=replay(path,choose,1,cap)
                metrics["invalid_actions"]+=observed["total_ms"]!=plan_cost(path,observed["stops"],1,cap)
                regret=observed["total_ms"]-oracle;metrics["negative_regret"]+=regret<0
                totals[p]+=observed["total_ms"];regrets[p]+=regret;counts[p]+=len(observed["stops"])
                row[p]=dict(stops=observed["stops"],total_ms=observed["total_ms"],regret_ms=regret)
            rows.append(row)
        groups.append(dict(regime=regime,cases=n,mean_cost_ms={p:totals[p]/n for p in POLICIES},
                           mean_regret_ms={p:regrets[p]/n for p in POLICIES},mean_stops={p:counts[p]/n for p in POLICIES},rows=rows))
    return dict(metrics=metrics,observations=dict(exact=result,holdout=groups,
                limitations="Synthetic eight-lap horizon, one to three stops, binary weather with two-rate prior, linear tyre age cost and fixed service cost. Expected dominance is within matched prior only. No inventory, mandatory compound rules, traffic, double stack, real tyre data or game integration."))

def spec(c):
    keys=("weight_mismatches","bellman_mismatches","single_stop_mismatches","dominance_violations","invalid_actions","causality_violations","negative_regret","replay_mismatches")
    return dict(hypothesis="Causal one-to-three-stop Bellman reference matches weighted exhaustive replay and retains the one-stop expected value; expanded feasible actions cannot increase expected cost under the same synthetic prior.",
                sources=["REF-106","IDEA-041","IDEA-045","IDEA-048"],
                config=dict(seed=20261129,horizon=8,rates=[100,600],cases_per_regime=24,holdout_rates=[100,600,900]),
                criteria={k:c("eq",0) for k in keys},evaluate=evaluate)
