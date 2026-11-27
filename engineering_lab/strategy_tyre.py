"""Synthetic nonlinear lap-cost model and causal multi-stint reference.

Age is completed laps, not measured wear. Parameters are invented test
fixtures, not fitted compounds, physical grip or 2012 tyre specifications.
"""
from fractions import Fraction
from functools import lru_cache
from itertools import product
import random
from . import registry as reg, strategy_research as base, strategy_adaptive as adaptive, strategy_weather as weather, strategy_stints as stints

# fresh offset, linear age penalty, cliff age, quadratic post-cliff coefficient (ms)
PROFILES={"soft":(0,220,5,750),"medium":(350,150,8,450),
          "hard":(850,90,12,250),"wet":(500,130,8,350)}
ACTIONS=(None,*PROFILES)
POLICIES=("single_stop","multi_stop")
MAX_HORIZON=12

def lap_cost(tyre,age,wet):
    reg.require(isinstance(tyre,str) and tyre in PROFILES and type(age) is int and 0<=age<=32 and type(wet) is bool,"tyre lap state")
    offset,slope,cliff,curve=PROFILES[tyre]
    return 90000+offset+slope*age+curve*max(0,age-cliff)**2+(8000 if (tyre=="wet")!=wet else 0)

def controller(rates,maximum=3):
    rates=weather.validate_rates(rates);stints.validate_budget(1,maximum)
    @lru_cache(maxsize=128)
    def prediction(c,s):
        return weather.forecast(rates,c,s)
    @lru_cache(maxsize=60000)
    def value(remaining,tyre,age,wet,used,c,s):
        p=prediction(c,s);rows=[]
        for action in ACTIONS:
            next_used=used+int(action is not None)
            if next_used>maximum or next_used+remaining-1<1:
                continue
            new=tyre if action is None else action
            new_age=age if action is None else 0
            cost=Fraction(lap_cost(new,new_age,wet)+(base.PIT_MS if action is not None else 0))
            if remaining>1:
                cost+=(1-p)*value(remaining-1,new,new_age+1,wet,next_used,c,s+1)[0]
                cost+=p*value(remaining-1,new,new_age+1,not wet,next_used,c+1,s)[0]
            rows.append((cost,ACTIONS.index(action),action))
        best=min(rows)
        return best[0],best[2]
    def solve(remaining,tyre,age,prefix,used=0):
        c,s=weather.counts(prefix)
        reg.require(type(remaining) is int and 1<=remaining<=MAX_HORIZON and len(prefix)+remaining-1<=MAX_HORIZON,"horizon")
        reg.require(type(used) is int and 0<=used<=maximum and used<=len(prefix)-1,"pit state")
        lap_cost(tyre,age,prefix[-1])
        reg.require(age+remaining-1<=32,"age domain")
        return value(remaining,tyre,age,prefix[-1],used,c,s)
    return solve

def valid_path(path):
    reg.require(isinstance(path,(tuple,list)) and 2<=len(path)<=MAX_HORIZON and all(type(w) is bool for w in path),"weather path")

def replay(path,choose,maximum=3):
    valid_path(path);stints.validate_budget(1,maximum)
    tyre="medium";age=4;stops=[];trace=[];total=0
    for lap,wet in enumerate(path):
        action=choose(len(path)-lap,tyre,age,tuple(path[:lap+1]),len(stops))[1]
        reg.require(action in ACTIONS,"action")
        if action is not None:
            reg.require(len(stops)<maximum,"pit limit")
            stops.append((lap,action));tyre=action;age=0;total+=base.PIT_MS
        cost=lap_cost(tyre,age,wet);total+=cost
        trace.append(dict(lap=lap,wet=wet,action=action,tyre=tyre,age=age,cost_ms=cost))
        age+=1
    reg.require(1<=len(stops)<=maximum,"mandatory pit")
    return dict(total_ms=total,stops=stops,trace=trace)

def plan_cost(path,stops,maximum=3):
    valid_path(path);stints.validate_budget(1,maximum)
    reg.require(isinstance(stops,(list,tuple)) and 1<=len(stops)<=maximum,"pit count")
    start=0;last=-1;tyre="medium";age=4;total=0
    for row in stops:
        reg.require(isinstance(row,(list,tuple)) and len(row)==2,"pit row")
        lap,new=row
        reg.require(type(lap) is int and last<lap<len(path) and isinstance(new,str) and new in PROFILES,"pit order/compound")
        total+=sum(lap_cost(tyre,age+i,path[start+i]) for i in range(lap-start))+base.PIT_MS
        start=lap;last=lap;tyre=new;age=0
    return total+sum(lap_cost(tyre,age+i,path[start+i]) for i in range(len(path)-start))

def hindsight(path,maximum=3):
    """Independent segment DP with perfect weather, evaluation only."""
    valid_path(path);stints.validate_budget(1,maximum)
    h=len(path)
    @lru_cache(maxsize=None)
    def segment(start,end,tyre,age):
        return sum(lap_cost(tyre,age+i,path[start+i]) for i in range(end-start))
    # Earliest service at lap zero is allowed; every subsequent stint >=1 lap.
    @lru_cache(maxsize=None)
    def tail(start,tyre,left):
        best=segment(start,h,tyre,0)
        if left:
            best=min(best,min((segment(start,k,tyre,0)+base.PIT_MS+tail(k,new,left-1)
                               for k in range(start+1,h) for new in PROFILES),default=best))
        return best
    return min(segment(0,k,"medium",4)+base.PIT_MS+tail(k,new,maximum-1)
               for k in range(h) for new in PROFILES)

def exact(h,rates):
    rates=weather.validate_rates(rates)
    reg.require(type(h) is int and 2<=h<=8,"exact budget")
    policies={p:controller(rates,1 if p=="single_stop" else 3) for p in POLICIES}
    totals={p:0 for p in POLICIES};counts={p:0 for p in POLICIES};prefixes={p:{} for p in POLICIES}
    weights=invalid=causal=0;denom=4*1000**(h-1)
    for path in product((False,True),repeat=h):
        w=sum(adaptive.weight(path,r) for r in rates);weights+=w
        for p,choose in policies.items():
            cap=1 if p=="single_stop" else 3
            result=replay(path,choose,cap)
            invalid+=result["total_ms"]!=plan_cost(path,result["stops"],cap)
            invalid+=len(result["stops"])!=sum(x["action"] is not None for x in result["trace"])
            totals[p]+=w*result["total_ms"];counts[p]+=w*len(result["stops"])
            for i,row in enumerate(result["trace"]):
                prefix=path[:i+1];causal+=row!=prefixes[p].setdefault(prefix,row)
    want={p:sum((s(h,"medium",4,(wet,))[0] for wet in (False,True)),Fraction())/2 for p,s in policies.items()}
    return dict(paths=2**h,expected_cost_ms={p:totals[p]/denom for p in POLICIES},
                expected_stops={p:counts[p]/denom for p in POLICIES},
                metrics=dict(weight_mismatches=int(weights!=denom),
                             bellman_mismatches=sum(want[p]!=Fraction(totals[p],denom) for p in POLICIES),
                             dominance_violations=int(totals["multi_stop"]>totals["single_stop"]),
                             invalid_actions=invalid,causality_violations=causal))

def evaluate(config):
    h=config["horizon"];n=config["cases_per_regime"];seed=config["seed"];rates=weather.validate_rates(config["rates"])
    regimes=config["holdout_rates"];eh=config["exact_horizon"]
    reg.require(type(h) is int and 2<=h<=MAX_HORIZON and type(n) is int and 1<=n<=32 and type(seed) is int and 0<=seed<=2**32,"experiment budget")
    reg.require(isinstance(regimes,list) and 1<=len(regimes)<=4 and all(type(r) is int and 0<=r<=1000 for r in regimes) and regimes==sorted(set(regimes)),"holdout regimes")
    result=exact(eh,rates);metrics=dict(result.pop("metrics"),negative_regret=0,replay_mismatches=0,curve_violations=0)
    curves={}
    for tyre,(_,slope,cliff,curve) in PROFILES.items():
        costs=[lap_cost(tyre,a,tyre=="wet") for a in range(33)]
        deltas=[b-a for a,b in zip(costs,costs[1:])]
        metrics["curve_violations"]+=sum(x<0 for x in deltas)+sum(b<a for a,b in zip(deltas,deltas[1:]))
        metrics["curve_violations"]+=int(deltas[cliff]<=slope or deltas[cliff-1]!=slope)
        curves[tyre]=costs
    rng=random.Random(seed);policies={p:controller(rates,1 if p=="single_stop" else 3) for p in POLICIES};groups=[]
    for regime in regimes:
        sums={p:0 for p in POLICIES};regrets={p:0 for p in POLICIES};counts={p:0 for p in POLICIES};rows=[]
        for i in range(n):
            path=base.weather_path(rng,bool(rng.randrange(2)),h,regime)
            oracle=hindsight(path);row=dict(case=i,weather=path,oracle_ms=oracle)
            for p,choose in policies.items():
                cap=1 if p=="single_stop" else 3
                observed=replay(path,choose,cap)
                metrics["replay_mismatches"]+=observed!=replay(path,choose,cap)
                metrics["invalid_actions"]+=observed["total_ms"]!=plan_cost(path,observed["stops"],cap)
                regret=observed["total_ms"]-oracle;metrics["negative_regret"]+=regret<0
                sums[p]+=observed["total_ms"];regrets[p]+=regret;counts[p]+=len(observed["stops"])
                row[p]=dict(stops=observed["stops"],total_ms=observed["total_ms"],regret_ms=regret)
            rows.append(row)
        groups.append(dict(regime=regime,cases=n,mean_cost_ms={p:sums[p]/n for p in POLICIES},
                           mean_regret_ms={p:regrets[p]/n for p in POLICIES},mean_stops={p:counts[p]/n for p in POLICIES},rows=rows))
    return dict(metrics=metrics,observations=dict(exact=result,holdout=groups,matched_weather_cost_curves_ms=curves,profiles=PROFILES,
                limitations="Invented lap-age cost curves, binary weather, known two-rate prior family, fixed pit cost and one to three services. No real compound data, thermal or force coupling, tyre inventory or regulations. Matched-prior expected dominance only; sampled longer horizon is exploratory. No game integration."))

def spec(c):
    keys=("weight_mismatches","bellman_mismatches","dominance_violations","invalid_actions","causality_violations","negative_regret","replay_mismatches","curve_violations")
    return dict(hypothesis="Synthetic nonlinear tyre costs have monotone convex age penalty and explicit cliff; causal multi-stop policy reconciles exact weighted replay, expected value no worse than single stop under identical costs.",
                sources=["REF-106","IDEA-041","IDEA-045","IDEA-048"],
                config=dict(seed=20261130,horizon=12,exact_horizon=8,rates=[100,600],cases_per_regime=24,holdout_rates=[100,600,900]),
                criteria={k:c("eq",0) for k in keys},evaluate=evaluate)
