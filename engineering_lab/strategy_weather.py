"""Causal Bayesian weather-transition forecast with unknown synthetic regime.

Two equally likely fixed flip rates per episode, observed current weather.
Exact rational posterior and Bellman reference; no future observations,
forecast service, measured weather or game integration.
"""
from fractions import Fraction
from functools import lru_cache
from itertools import product
import random
from . import registry as reg, strategy_research as base, strategy_adaptive as adaptive

POLICIES=("heuristic","fixed_forecast","bayesian")

def validate_rates(rates):
    reg.require(isinstance(rates,(list,tuple)) and len(rates)==2 and
                all(type(r) is int and 0<r<1000 for r in rates) and rates[0]<rates[1] and
                sum(rates)%2==0,"two ordered interior rates with integer prior mean")
    return tuple(rates)

def posterior(rates,changes,stays):
    rates=validate_rates(rates)
    reg.require(type(changes) is int and type(stays) is int and changes>=0 and stays>=0 and changes+stays<=19,"weather counts")
    weights=[r**changes*(1000-r)**stays for r in rates]
    total=sum(weights)
    return tuple(Fraction(w,total) for w in weights)

def forecast(rates,changes,stays):
    probs=posterior(rates,changes,stays)
    return sum((p*Fraction(r,1000) for p,r in zip(probs,rates)),Fraction())

def counts(prefix):
    reg.require(isinstance(prefix,(tuple,list)) and 1<=len(prefix)<=20 and all(type(w) is bool for w in prefix),"observed weather prefix")
    changes=sum(a!=b for a,b in zip(prefix,prefix[1:]))
    return changes,len(prefix)-1-changes

def controller(rates):
    rates=validate_rates(rates)
    @lru_cache(maxsize=12000)
    def value(remaining,tyre,age,wet,used,changes,stays):
        p=forecast(rates,changes,stays)
        options=(None,) if used else (base.TYRES if remaining==1 else adaptive.ACTIONS)
        rows=[]
        for action in options:
            new=tyre if action is None else action
            new_age=age if action is None else 0
            spent=used or action is not None
            cost=Fraction(base.lap_cost(new,new_age,wet)+(base.PIT_MS if action is not None else 0))
            if remaining>1:
                cost+=(1-p)*value(remaining-1,new,new_age+1,wet,spent,changes,stays+1)[0]
                cost+=p*value(remaining-1,new,new_age+1,not wet,spent,changes+1,stays)[0]
            rows.append((cost,adaptive.ACTIONS.index(action),action))
        best=min(rows)
        return best[0],best[2]
    def solve(remaining,tyre,age,prefix,used=False):
        changes,stays=counts(prefix)
        reg.require(type(remaining) is int and 1<=remaining<=8 and len(prefix)+remaining-1<=8 and type(used) is bool,"weather decision budget")
        base.lap_cost(tyre,age,prefix[-1])
        reg.require(age+remaining-1<=32,"stint domain")
        return value(remaining,tyre,age,prefix[-1],used,changes,stays)
    return solve

def policy_set(rates):
    rates=validate_rates(rates)
    prior=sum(rates)//2
    bayes=controller(rates); fixed=adaptive.controller(prior)
    def heuristic(remaining,tyre,age,prefix,horizon):
        return base.choose("heuristic",len(prefix)-1,horizon,tyre,age,prefix[-1],42,1,prior)
    def static(remaining,tyre,age,prefix,horizon):
        return fixed(remaining,tyre,age,prefix[-1])["action"]
    def dynamic(remaining,tyre,age,prefix,horizon):
        return bayes(remaining,tyre,age,prefix)[1]
    return dict(heuristic=heuristic,fixed_forecast=static,bayesian=dynamic)

def replay(path,choose):
    reg.require(isinstance(path,(tuple,list)) and 2<=len(path)<=8 and all(type(w) is bool for w in path),"weather path")
    tyre="dry";age=4;stop=None;compound=None;total=0;trace=[]
    for lap,wet in enumerate(path):
        prefix=tuple(path[:lap+1])
        action=choose(len(path)-lap,tyre,age,prefix,len(path)) if stop is None else None
        reg.require(action in adaptive.ACTIONS,"weather decision")
        if action is not None:
            stop=lap;compound=action;tyre=action;age=0;total+=base.PIT_MS
        cost=base.lap_cost(tyre,age,wet);total+=cost
        trace.append(dict(lap=lap,wet=wet,action=action,tyre=tyre,age=age,cost_ms=cost))
        age+=1
    reg.require(stop is not None,"mandatory pit missing")
    return dict(stop=stop,compound=compound,total_ms=total,trace=trace)

def exact(h,rates):
    rates=validate_rates(rates)
    reg.require(type(h) is int and 2<=h<=8,"enumeration budget")
    policies=policy_set(rates)
    totals={p:0 for p in POLICIES};prefixes={p:{} for p in POLICIES}
    weights=invalid=causal=0; brier_bayes=Fraction();brier_fixed=Fraction()
    denom=4*1000**(h-1)
    for path in product((False,True),repeat=h):
        w=sum(adaptive.weight(path,r) for r in rates);weights+=w
        for i in range(1,h):
            c,s=counts(path[:i]); y=int(path[i]!=path[i-1])
            brier_bayes+=w*(forecast(rates,c,s)-y)**2
            brier_fixed+=w*(Fraction(sum(rates),2000)-y)**2
        for p,choose in policies.items():
            result=replay(path,choose)
            invalid+=result["total_ms"]!=base.cost_plan(path,"dry",4,result["stop"],result["compound"])
            invalid+=sum(x["action"] is not None for x in result["trace"])!=1
            totals[p]+=w*result["total_ms"]
            for i,row in enumerate(result["trace"]):
                prefix=path[:i+1]
                causal+=row!=prefixes[p].setdefault(prefix,row)
    solve=controller(rates)
    want=sum((solve(h,"dry",4,(wet,))[0] for wet in (False,True)),Fraction())/2
    # Regime-known causal policy, not a future-weather oracle.
    lower=sum((Fraction(adaptive.controller(r)(h,"dry",4,wet)["numerator_ms"],1000**(h-1)) for r in rates for wet in (False,True)),Fraction())/4
    return dict(paths=2**h,expected_cost_ms={p:totals[p]/denom for p in POLICIES},
                known_regime_lower_ms=float(lower),
                brier=dict(bayesian=float(brier_bayes/(denom*(h-1))),fixed=float(brier_fixed/(denom*(h-1)))),
                metrics=dict(weight_mismatches=int(weights!=denom),
                             bellman_mismatches=int(want!=Fraction(totals["bayesian"],denom)),
                             dominance_violations=sum(totals["bayesian"]>totals[p] for p in POLICIES if p!="bayesian"),
                             information_bound_violations=int(want<lower),
                             forecast_score_violations=int(brier_bayes>brier_fixed),
                             invalid_actions=invalid,causality_violations=causal))

def evaluate(config):
    rates=validate_rates(config["rates"]);h=config["horizon"];n=config["cases_per_regime"];seed=config["seed"]
    regimes=config["holdout_rates"]
    reg.require(type(h) is int and 2<=h<=8 and type(n) is int and 1<=n<=64 and type(seed) is int and 0<=seed<=2**32,"experiment budget")
    reg.require(isinstance(regimes,list) and 1<=len(regimes)<=4 and all(type(r) is int and 0<=r<=1000 for r in regimes) and regimes==sorted(set(regimes)),"holdout regimes")
    result=exact(h,rates);metrics=dict(result.pop("metrics"),negative_regret=0,replay_mismatches=0)
    rng=random.Random(seed);policies=policy_set(rates);groups=[]
    for regime in regimes:
        regrets={p:0 for p in POLICIES};scores={p:Fraction() for p in ("bayesian","fixed")};rows=[]
        for i in range(n):
            path=base.weather_path(rng,bool(rng.randrange(2)),h,regime)
            oracle=min(base.cost_plan(path,"dry",4,k,t) for k in range(h) for t in base.TYRES)
            row=dict(case=i,weather=path,oracle_ms=oracle)
            for j in range(1,h):
                c,s=counts(path[:j]);y=int(path[j]!=path[j-1])
                scores["bayesian"]+=(forecast(rates,c,s)-y)**2
                scores["fixed"]+=(Fraction(sum(rates),2000)-y)**2
            for p,choose in policies.items():
                observed=replay(path,choose)
                metrics["replay_mismatches"]+=observed!=replay(path,choose)
                metrics["invalid_actions"]+=observed["total_ms"]!=base.cost_plan(path,"dry",4,observed["stop"],observed["compound"])
                regret=observed["total_ms"]-oracle;metrics["negative_regret"]+=regret<0
                regrets[p]+=regret
                row[p]=dict(stop=observed["stop"],compound=observed["compound"],regret_ms=regret)
            rows.append(row)
        groups.append(dict(regime=regime,in_prior=regime in rates,cases=n,mean_regret_ms={p:regrets[p]/n for p in POLICIES},
                           brier={p:float(v/(n*(h-1))) for p,v in scores.items()},rows=rows))
    return dict(metrics=metrics,observations=dict(exact=result,holdout=groups,
                limitations="Synthetic two-rate prior with equal weights, observed current binary weather, known model family, one mandatory stop; posterior uses only realized transitions. Exact dominance and Brier claims apply to the matched prior mixture only. Holdout including out-of-prior regime is exploratory; no radar, real climate or game integration."))

def spec(c):
    keys=("weight_mismatches","bellman_mismatches","dominance_violations","information_bound_violations","forecast_score_violations","invalid_actions","causality_violations","negative_regret","replay_mismatches")
    return dict(hypothesis="Under the declared synthetic latent-regime prior, causal Bayesian prediction and adaptive decisions match exact weighted replay and do not exceed fixed-prior baselines in expected cost or Brier score; known-regime policy is a lower bound.",
                sources=["REF-106","IDEA-041","IDEA-045","IDEA-048"],
                config=dict(seed=20261128,horizon=8,rates=[100,600],cases_per_regime=32,holdout_rates=[100,600,900]),
                criteria={k:c("eq",0) for k in keys},evaluate=evaluate)
