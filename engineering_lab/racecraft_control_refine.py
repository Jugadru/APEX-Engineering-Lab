"""Feasible continuous-domain control refinement of the oriented solver.

A deterministic line search towards each requested control, with every new
trajectory checked against other selected paths. Not global optimization:
a disconnected feasible region may be missed, and the budget is finite.
"""
from . import registry as reg, racecraft_oriented as o, racecraft_yaw as yaw, physics_vehicle as vehicle
from .physics_core import scalar

FIELDS={"throttle":1.0,"brake":1.0,"kers_w":60000.0}
MAX_EVAL=192
ITERATIONS=8

def loss(candidate,desired,target):
    c=candidate["command"]
    return sum(((c[k]-desired[k])/scale)**2 for k,scale in FIELDS.items())+((candidate["steer_target"]-target)/yaw.STEER_MAX)**2

def interpolate(safe,desired,target,alpha):
    reg.require(0<=alpha<=1,"interpolation fraction")
    cmd=dict(safe["command"])
    for k in FIELDS:
        cmd[k]=(1-alpha)*cmd[k]+alpha*desired[k]
    angle=(1-alpha)*safe["steer_target"]+alpha*target
    return cmd,angle

def refine(states,commands,targets,half_width_m=6,node_limit=o.MAX_NODES,eval_limit=MAX_EVAL):
    reg.require(type(eval_limit) is int and 0<=eval_limit<=MAX_EVAL,"refinement budget")
    width=scalar(half_width_m,1.1,30,"strip half width")
    base=o.resolve(states,commands,targets,width,node_limit)
    if base["states"] is None:
        return {**base,"evaluations":0,"initial_loss":None,"final_loss":None}
    selected=dict(base["selected"])
    ids=sorted(selected)
    initial=sum(loss(selected[i],commands[i],targets[i]) for i in ids)
    evaluations=0
    for i in ids:
        original=selected[i]
        if loss(original,commands[i],targets[i])==0:
            continue
        lo,hi=0.0,1.0
        best=original
        # Search only along the segment to the driver's request. Every
        # acceptance is explicit; no assumption that safety is monotone.
        for _ in range(ITERATIONS):
            if evaluations>=eval_limit:
                break
            alpha=(lo+hi)/2
            cmd,target=interpolate(original,commands[i],targets[i],alpha)
            candidate=o.path(states[i],cmd,target,width)
            evaluations+=1
            if (candidate is not None and loss(candidate,commands[i],targets[i])<loss(best,commands[i],targets[i])
                and not any(o.collide(candidate["poses"],p["poses"]) for j,p in selected.items() if i!=j)):
                best=candidate;lo=alpha
            else:
                hi=alpha
        selected[i]=best
    final=sum(loss(selected[i],commands[i],targets[i]) for i in ids)
    return {**base,"selected":selected,"states":{i:selected[i]["state"] for i in ids},
            "evaluations":evaluations,"initial_loss":initial,"final_loss":final}

def evaluate(config):
    rows=[];invalid=repeat=improved=0
    for grip in config["grip"]:
        for lateral in config["lateral"]:
            s={1:dict(yaw.initial(),y_m=lateral)}
            commands={1:vehicle.control(grip_factor=grip)}
            targets={1:config["target"]}
            result=refine(s,commands,targets)
            if result["states"] is None:
                invalid+=1;rows.append(dict(grip=grip,lateral=lateral,status=result["status"]));continue
            invalid+=result["final_loss"]>result["initial_loss"]+1e-12
            improved+=result["final_loss"]<result["initial_loss"]-1e-12
            repeat+=result!=refine(s,commands,targets)
            rows.append(dict(grip=grip,lateral=lateral,initial=result["initial_loss"],final=result["final_loss"],
                             evaluations=result["evaluations"],target=result["selected"][1]["steer_target"]))
    return dict(metrics=dict(invalid=invalid,replay_mismatches=repeat,missing_improvement=int(improved==0)),
                observations=dict(rows=rows,improved=improved,limitations="Coordinate-wise bounded line search in real-valued controls; safe interpolated yaw paths only, not global optimality or track-wide viability."))

def spec(c):
    return dict(hypothesis="Bounded continuous control refinement can decrease command deviation while retaining joint path feasibility.",
                sources=["REF-107","IDEA-005","IDEA-008","IDEA-033"],config={"seed":42,"grip":[.4,1],"lateral":[4.7,4.8,4.9],"target":.25},
                criteria={"invalid":c("eq",0),"replay_mismatches":c("eq",0),"missing_improvement":c("eq",0)},evaluate=evaluate)
