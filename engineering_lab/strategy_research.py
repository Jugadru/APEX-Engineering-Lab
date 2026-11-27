"""Bounded one-stop strategy research with observed weather and forecast sampling.

Synthetic integer millisecond costs, not an F1 tyre model. No simulator or
sporting state. A policy sees only the current weather, never the future path.
"""
import random
from . import registry as reg

TYRES=("dry","wet")
POLICIES=("heuristic","monte_carlo")
PIT_MS=24000

def lap_cost(tyre,age,wet):
    reg.require(tyre in TYRES and type(age) is int and 0<=age<=32 and type(wet) is bool,"lap state")
    return 90000+age*(400 if tyre=="dry" else 200)+(8000 if (tyre=="wet")!=wet else 0)

def weather_path(rng,wet,horizon,flip):
    reg.require(type(wet) is bool and type(horizon) is int and 1<=horizon<=20 and type(flip) is int and 0<=flip<=1000,"weather configuration")
    rows=[wet]
    for _ in range(horizon-1):
        if rng.randrange(1000)<flip:
            wet=not wet
        rows.append(wet)
    return tuple(rows)

def cost_plan(weather,tyre,age,stop,compound):
    # stop is before the lap at index stop; one mandatory stop.
    reg.require(0<=stop<len(weather) and compound in TYRES,"stop plan")
    total=0
    for i,wet in enumerate(weather):
        if i==stop:
            tyre,age=compound,0
            total+=PIT_MS
        total+=lap_cost(tyre,age,wet)
        age+=1
    return total

def choose(policy,lap,horizon,tyre,age,wet,seed,samples,flip):
    reg.require(policy in POLICIES and type(lap) is int and type(horizon) is int and 0<=lap<horizon<=20,"decision horizon")
    reg.require(type(seed) is int and 0<=seed<=2**32 and type(samples) is int and 1<=samples<=128,"forecast budget")
    lap_cost(tyre,age,wet)
    reg.require(type(flip) is int and 0<=flip<=1000,"flip probability")
    compound="wet" if wet else "dry"
    if policy=="heuristic":
        return compound if lap>=horizon//2 or lap==horizon-1 or compound!=tyre else None
    # Common forecast paths for all candidate plans. Seeds depend only on the
    # declared forecast seed and decision index, not hidden realized weather.
    rng=random.Random(seed+104729*lap)
    forecasts=[weather_path(rng,wet,horizon-lap,flip) for _ in range(samples)]
    _,stop,new=min((sum(cost_plan(path,tyre,age,k,c) for path in forecasts),k,c)
                   for k in range(horizon-lap) for c in TYRES)
    return new if stop==0 else None

def episode(policy,weather,seed,samples,flip):
    reg.require(isinstance(weather,(tuple,list)) and 2<=len(weather)<=20 and all(type(x) is bool for x in weather),"episode weather")
    tyre="dry";age=4;total=0;stop=None;trace=[]
    for lap,wet in enumerate(weather):
        action=None if stop is not None else choose(policy,lap,len(weather),tyre,age,wet,seed,samples,flip)
        if action is not None:
            stop=lap;tyre,age=action,0;total+=PIT_MS
        cost=lap_cost(tyre,age,wet);total+=cost
        trace.append(dict(lap=lap,wet=wet,action=action,tyre=tyre,age=age,cost_ms=cost))
        age+=1
    return dict(stop=stop,total_ms=total,trace=trace)

def evaluate(config):
    seed=config["seed"];h=config["horizon"];n=config["heldout"];samples=config["samples"];flip=config["flip_per_mille"]
    reg.require(type(seed) is int and 0<=seed<=2**32-1000003 and type(n) is int and 1<=n<=128,"heldout budget")
    reg.require(type(h) is int and 2<=h<=20,"horizon")
    rng=random.Random(seed+1000003)
    rows=[];invalid=repeat=negative=0
    for i in range(n):
        weather=weather_path(rng,bool(rng.randrange(2)),h,flip)
        oracle=min(cost_plan(weather,"dry",4,k,c) for k in range(h) for c in TYRES)
        row=dict(case=i,weather=weather,oracle_ms=oracle)
        for policy in POLICIES:
            result=episode(policy,weather,seed,samples,flip)
            repeat+=result!=episode(policy,weather,seed,samples,flip)
            actions=[x["lap"] for x in result["trace"] if x["action"] is not None]
            invalid+=len(actions)!=1 or actions!=[result["stop"]]
            regret=result["total_ms"]-oracle
            negative+=regret<0
            row[policy]=dict(stop=result["stop"],total_ms=result["total_ms"],regret_ms=regret,
                             compound=next((x["action"] for x in result["trace"] if x["action"] is not None),None))
        rows.append(row)
    means={p:sum(r[p]["regret_ms"] for r in rows)/n for p in POLICIES}
    return dict(metrics=dict(invalid_actions=invalid,replay_mismatches=repeat,negative_regret=negative),
                observations=dict(cases=n,forecast_samples=samples,mean_regret_ms=means,
                                  regret_delta_ms=means["monte_carlo"]-means["heuristic"],
                                  rows=rows,limitations="Synthetic one mandatory stop, two artificial tyre types, binary weather and known transition probability; forecasts never access realized future. Hindsight oracle is evaluation only. No traffic, double stack, actual tyre data, strategy superiority gate or game integration."))

def spec(c):
    return dict(hypothesis="A bounded causal Monte Carlo policy and simple heuristic complete one legal stop with deterministic paired replay and nonnegative hindsight regret.",
                sources=["REF-106","IDEA-041","IDEA-045","IDEA-048"],
                config=dict(seed=42,horizon=8,heldout=32,samples=32,flip_per_mille=250),
                criteria=dict(invalid_actions=c("eq",0),replay_mismatches=c("eq",0),negative_regret=c("eq",0)),
                evaluate=evaluate)
