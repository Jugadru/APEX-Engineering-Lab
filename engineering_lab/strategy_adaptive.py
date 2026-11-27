"""Exact finite-horizon causal strategy reference for the existing synthetic model.

The known binary Markov transition is in per-mille. Integer Bellman values
are numerators over 1000**(remaining-1), in milliseconds. No observed future
weather, learned parameters, real tyre claims or runtime integration.
"""
from functools import lru_cache
from itertools import product
import random
from . import registry as reg, strategy_research as base

POLICIES=base.POLICIES+("adaptive",)
ACTIONS=("dry","wet",None)

def controller(flip):
    reg.require(type(flip) is int and 0<=flip<=1000,"flip probability")
    @lru_cache(maxsize=6000)
    def value(remaining,tyre,age,wet,pit_used):
        scale=1000**(remaining-1)
        options=(None,) if pit_used else (base.TYRES if remaining==1 else ACTIONS)
        candidates=[]
        for action in options:
            new=tyre if action is None else action
            new_age=age if action is None else 0
            spent=pit_used or action is not None
            now=base.lap_cost(new,new_age,wet)+(base.PIT_MS if action is not None else 0)
            total=now*scale
            if remaining>1:
                total+=(1000-flip)*value(remaining-1,new,new_age+1,wet,spent)[0]
                total+=flip*value(remaining-1,new,new_age+1,not wet,spent)[0]
            candidates.append((total,ACTIONS.index(action),action))
        best=min(candidates)
        return best[0],best[2]
    def solve(remaining,tyre,age,wet,pit_used=False):
        reg.require(type(remaining) is int and 1<=remaining<=20 and type(pit_used) is bool,"adaptive state")
        base.lap_cost(tyre,age,wet)
        reg.require(age+remaining-1<=32,"adaptive stint domain")
        numerator,action=value(remaining,tyre,age,wet,pit_used)
        return dict(numerator_ms=numerator,denominator=1000**(remaining-1),action=action)
    return solve

def decision_policy(policy,flip,seed,samples):
    reg.require(policy in POLICIES,"policy")
    solve=controller(flip)
    @lru_cache(maxsize=6000)
    def decide(lap,horizon,tyre,age,wet):
        if policy=="adaptive":
            return solve(horizon-lap,tyre,age,wet)["action"]
        return base.choose(policy,lap,horizon,tyre,age,wet,seed,samples,flip)
    return decide

def replay(weather,decide):
    reg.require(isinstance(weather,(tuple,list)) and 2<=len(weather)<=20 and all(type(w) is bool for w in weather),"episode weather")
    tyre="dry";age=4;stop=None;compound=None;total=0;trace=[]
    for lap,wet in enumerate(weather):
        action=decide(lap,len(weather),tyre,age,wet) if stop is None else None
        reg.require(action in ACTIONS,"invalid decision")
        if action is not None:
            stop=lap;compound=action;tyre=action;age=0;total+=base.PIT_MS
        cost=base.lap_cost(tyre,age,wet)
        total+=cost
        trace.append(dict(lap=lap,wet=wet,action=action,tyre=tyre,age=age,cost_ms=cost))
        age+=1
    reg.require(stop is not None,"mandatory pit missing")
    return dict(stop=stop,compound=compound,total_ms=total,trace=trace)

def weight(path,flip):
    # Both starting weather states are equally likely. Divide by
    # 2*1000**(H-1) outside this routine. Zero-probability paths still
    # exercise legal decisions and prefix invariance.
    result=1
    for previous,current in zip(path,path[1:]):
        result*=flip if previous!=current else 1000-flip
    return result

def exact_comparison(horizon,flip,seed,samples):
    reg.require(type(horizon) is int and 2<=horizon<=8,"enumeration budget")
    policies={p:decision_policy(p,flip,seed,samples) for p in POLICIES}
    totals={p:0 for p in POLICIES};prefixes={p:{} for p in POLICIES}
    invalid=causality=0;weight_sum=0
    for path in product((False,True),repeat=horizon):
        w=weight(path,flip);weight_sum+=w
        for p,decide in policies.items():
            result=replay(path,decide)
            invalid+=result["total_ms"]!=base.cost_plan(path,"dry",4,result["stop"],result["compound"])
            invalid+=sum(x["action"] is not None for x in result["trace"])!=1
            totals[p]+=w*result["total_ms"]
            for i,row in enumerate(result["trace"]):
                prefix=path[:i+1]
                causality+=row!=prefixes[p].setdefault(prefix,row)
    solve=controller(flip)
    expected=sum(solve(horizon,"dry",4,wet)["numerator_ms"] for wet in (False,True))
    denom=2*1000**(horizon-1)
    return dict(flip_per_mille=flip,paths=2**horizon,denominator=denom,
                weighted_costs_ms=totals,expected_cost_ms={p:totals[p]/denom for p in POLICIES},
                bellman_numerator_ms=expected,weight_mismatches=int(weight_sum!=denom),
                bellman_mismatches=int(expected!=totals["adaptive"]),
                dominance_violations=sum(totals["adaptive"]>totals[p] for p in base.POLICIES),
                invalid_actions=invalid,causality_violations=causality)

def evaluate(config):
    seed=config["seed"];h=config["horizon"];n=config["heldout"];samples=config["samples"]
    flips=config["flip_grid"];holdout_seed=config["heldout_seed"];flip=config["heldout_flip"]
    reg.require(type(seed) is int and 0<=seed<=2**32 and type(holdout_seed) is int and 0<=holdout_seed<=2**32 and seed!=holdout_seed,"independent seeds")
    reg.require(type(h) is int and 2<=h<=8 and type(n) is int and 1<=n<=128 and type(samples) is int and 1<=samples<=128,"experiment budget")
    reg.require(isinstance(flips,list) and 1<=len(flips)<=5 and all(type(f) is int and 0<=f<=1000 for f in flips) and flips==sorted(set(flips)) and type(flip) is int and flip in flips,"weather grid")
    exact=[exact_comparison(h,f,seed,samples) for f in flips]
    keys=("weight_mismatches","bellman_mismatches","dominance_violations","invalid_actions","causality_violations")
    metrics={k:sum(row[k] for row in exact) for k in keys}
    metrics.update(negative_regret=0,replay_mismatches=0)
    rng=random.Random(holdout_seed)
    policies={p:decision_policy(p,flip,seed,samples) for p in POLICIES}
    rows=[]
    for i in range(n):
        path=base.weather_path(rng,bool(rng.randrange(2)),h,flip)
        oracle=min(base.cost_plan(path,"dry",4,k,c) for k in range(h) for c in base.TYRES)
        row=dict(case=i,weather=path,oracle_ms=oracle)
        for p,decide in policies.items():
            result=replay(path,decide)
            metrics["replay_mismatches"]+=result!=replay(path,decide)
            metrics["invalid_actions"]+=result["total_ms"]!=base.cost_plan(path,"dry",4,result["stop"],result["compound"])
            regret=result["total_ms"]-oracle
            metrics["negative_regret"]+=regret<0
            row[p]=dict(stop=result["stop"],compound=result["compound"],total_ms=result["total_ms"],regret_ms=regret)
        rows.append(row)
    means={p:sum(r[p]["regret_ms"] for r in rows)/n for p in POLICIES}
    return dict(metrics=metrics,observations=dict(exact=exact,heldout_cases=n,
                mean_regret_ms=means,rows=rows,limitations="Exact optimality applies only to the synthetic known Markov distribution, one mandatory stop, two artificial tyre types and risk-neutral expected milliseconds. Heldout ranking is exploratory. No real race calibration, traffic, double stack, imperfect weather estimation or game integration."))

def spec(c):
    keys=("weight_mismatches","bellman_mismatches","dominance_violations","invalid_actions","causality_violations","negative_regret","replay_mismatches")
    return dict(hypothesis="Exact causal Bellman reference matches exhaustive weighted path replay and does not exceed either baseline expected cost under the same known distribution; legal and causal replay.",
                sources=["REF-106","IDEA-041","IDEA-045","IDEA-048"],
                config=dict(seed=42,horizon=8,heldout=64,samples=32,flip_grid=[0,250,500,1000],heldout_seed=20261127,heldout_flip=250),
                criteria={k:c("eq",0) for k in keys},evaluate=evaluate)
