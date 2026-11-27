"""One-stop synthetic pit cost comparison; no game state or future data in selection."""
import random
from . import registry as reg

def scenario(rng,horizon):
    # Integer milliseconds internally for exact arithmetic. Artificial costs,
    # not empirical F1 times or a calibrated tyre degradation law.
    old_slope=rng.randrange(250,1251)
    new_slope=rng.randrange(50,301)
    return {"old":[90000+old_slope*(5+i) for i in range(horizon)],
            "fresh":[90000+new_slope*i for i in range(horizon)],
            "pit":[18000+rng.randrange(0,12001) for _ in range(horizon)]}

def direct(s,entries):
    h=len(s["old"])
    return [sum(s["old"][:k])+sum(s["fresh"][:h-k])+s["pit"][k-1] for k in entries]

def prefix(values):
    out=[0]
    for v in values: out.append(out[-1]+v)
    return out

def indexed(s,entries):
    h=len(s["old"])
    a,b=prefix(s["old"]),prefix(s["fresh"])
    return [a[k]+b[h-k]+s["pit"][k-1] for k in entries]

def best(costs,entries):
    return min(zip(costs,entries))[1]

def evaluate(config):
    h=config["horizon"]; entries=config["entries"]
    reg.require(type(h) is int and 2<=h<=20 and isinstance(entries,list) and entries==sorted(set(entries)) and bool(entries)
                and all(type(k) is int and 1<=k<h for k in entries),"pit entries")
    seed=config["seed"]; n=config["training"]; ntest=config["heldout"]
    reg.require(type(n) is int and type(ntest) is int and 1<=n<=128 and 1<=ntest<=128,"bounded sample count")
    train_rng=random.Random(seed)
    training=[scenario(train_rng,h) for _ in range(n)]
    # Both policies choose once, before the independent held-out scenarios exist.
    nominal={"old":[90000+750*(5+i) for i in range(h)],
             "fresh":[90000+175*i for i in range(h)],"pit":[24000]*h}
    nominal_choice=best(direct(nominal,entries),entries)
    samples=[indexed(s,entries) for s in training]
    mc_choice=best([sum(row[i] for row in samples) for i in range(len(entries))],entries)
    heldout_rng=random.Random(seed+1000003)
    heldout=[scenario(heldout_rng,h) for _ in range(ntest)]
    mismatches=sum(direct(s,entries)!=indexed(s,entries) for s in training+heldout+[nominal])
    invalid=int(nominal_choice not in entries)+int(mc_choice not in entries)
    regrets={"nominal":[],"sampled":[]}
    for s in heldout:
        c=direct(s,entries); oracle=min(c)
        regrets["nominal"].append(c[entries.index(nominal_choice)]-oracle)
        regrets["sampled"].append(c[entries.index(mc_choice)]-oracle)
    mean={k:sum(v)/ntest/1000 for k,v in regrets.items()}
    # Model-level addition counts, including prefix construction, excluding
    # indexing, selection, allocation and RNG. Direct sums use one addition
    # per term and two combining additions per option.
    count=len(training)+len(heldout)+1
    b=count*len(entries)*(h+2)
    c=count*(2*h+2*len(entries))
    return {"metrics":{"cost_mismatches":mismatches,"invalid_actions":invalid,"extra_additions":c-b},
            "observations":{"scenarios":count,"training":n,"heldout":ntest,"entries":entries,
                "nominal_entry":nominal_choice,"sampled_entry":mc_choice,"mean_regret_s":mean,
                "regret_delta_s":mean["sampled"]-mean["nominal"],
                "nominal_regret_s_by_case":[v/1000 for v in regrets["nominal"]],
                "sampled_regret_s_by_case":[v/1000 for v in regrets["sampled"]],
                "direct_additions_model":b,"prefix_additions_model":c,
                "limitations":"Artificial single-stop horizon; choices frozen before heldout generation. Hindsight oracle is evaluation only. Regret direction exploratory, not an acceptance criterion; no real race, tyre/weather calibration, traffic feedback or runtime timing."}}
