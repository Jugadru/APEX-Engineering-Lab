"""Experimental multi-car solver using the existing coupled physical step.

Periodic straight strip, axis-aligned envelopes; no steering, launch or impact.
State is SI and retained without quantization. No partial state on failure.
"""
from fractions import Fraction as Q
from itertools import combinations
from . import registry as reg, racecraft_core as core, racecraft_collision as col
from . import racecraft_coupled as coupled, physics_vehicle as vehicle
from .physics_core import scalar

DT = 0.2
MAX_NODES = 4096
EPS = Q(1, 100000000)
LONG = Q(col.LONG, 1000)
LAT = Q(col.LAT, 1000)

def initial(progress, speed=40, lateral=0, lateral_speed=0, fuel=5):
    s = coupled.initial(speed, lateral, lateral_speed, fuel)
    s["progress_m"] = progress
    return s

def q(value):
    return Q(value)

def conflict(a, b, ea, eb, length):
    """Conservative chord envelope for continuous frozen-force trajectories.

    Both velocity components are monotone within a tick (forward velocity
    may plateau at zero). A path differs from its chord by at most dt times
    its velocity range. Sum both cars' bounds; touching counts as conflict.
    Rational interval arithmetic on stored binary values; extra small margin
    covers endpoint arithmetic in this bounded SI domain.
    """
    x = q(b["progress_m"]) - q(a["progress_m"])
    y = q(b["lateral_m"]) - q(a["lateral_m"])
    dx = q(eb["progress_m"]) - q(ea["progress_m"]) - x
    dy = q(eb["lateral_m"]) - q(ea["lateral_m"]) - y
    px = q(DT) * sum(abs(q(e["vehicle"]["speed_mps"])-q(s["vehicle"]["speed_mps"])) for s,e in ((a,ea),(b,eb))) + EPS
    py = q(DT) * sum(abs(q(e["lateral_speed_mps"])-q(s["lateral_speed_mps"])) for s,e in ((a,ea),(b,eb))) + EPS
    ly = col.interval(y, dy, LAT+py)
    if ly is None:
        return False
    limit = LONG+px
    lo, hi = min(x,x+dx)-limit, max(x,x+dx)+limit
    for k in range(-((-lo)//length), hi//length+1):
        lx = col.interval(x-k*length, dx, limit)
        if lx is not None and max(lx[0],ly[0]) <= min(lx[1],ly[1]):
            return True
    return False

def preventive(states, ident, length, command):
    # Ranking heuristic only; does not guarantee a future feasible trajectory.
    a = states[ident]
    for j,b in states.items():
        if j == ident:
            continue
        gap = (b["progress_m"]-a["progress_m"]) % length
        closing = a["vehicle"]["speed_mps"]-b["vehicle"]["speed_mps"]
        lateral_guard = float(LAT)+DT*(abs(a["lateral_speed_mps"])+abs(b["lateral_speed_mps"]))+0.6
        if closing > 0 and abs(a["lateral_m"]-b["lateral_m"]) <= lateral_guard:
            if 0 < gap <= float(LONG)+2*closing+closing*closing/8:
                return True
    return False

def alternatives(s, command, brake_first):
    # Preserve environment, gear and all other physical inputs. Only alter
    # control requests, never the force result or physical state.
    damp = max(-30, min(30, -s["lateral_speed_mps"]/DT))
    desired = dict(command)
    coast = dict(command, throttle=0, brake=0, kers_w=0)
    brake = dict(command, throttle=0, brake=1, kers_w=0)
    choices = [desired, coast, brake, dict(coast, ay_mps2=damp), dict(brake, ay_mps2=damp)]
    if brake_first:
        choices = [choices[2], choices[4], choices[0], choices[1], choices[3]]
    unique=[]
    for c in choices:
        if c not in unique:
            unique.append(c)
    return unique

def resolve(states, commands, length_m=5000, half_width_m=5, node_limit=MAX_NODES):
    length = scalar(length_m,100,20000,"track length")
    width = scalar(half_width_m,coupled.MARGIN_M,15,"half width")
    core.integer(node_limit,1,MAX_NODES,"node budget")
    reg.require(type(states) is dict and 1<=len(states)<=24 and all(type(i) is int and 0<=i<=255 for i in states),"roster")
    reg.require(type(commands) is dict and all(type(i) is int for i in commands) and set(commands)==set(states),"command roster")
    ids = sorted(states)
    # Validate all inputs before evaluating geometry, even for invalid starts.
    for i in ids:
        coupled.step(states[i],commands[i],0,width)
    def failed(status,nodes=0):
        return dict(status=status,states=None,selected=None,nodes=nodes)
    if any(abs(states[i]["lateral_m"])>width-coupled.MARGIN_M for i in ids):
        return failed("INITIAL_STATE_INVALID")
    for i,j in combinations(ids,2):
        a,b=states[i],states[j]
        if conflict(a,b,a,b,q(length)):
            return failed("INITIAL_STATE_INVALID")
    order = sorted(ids,key=lambda i:(-states[i]["progress_m"],i))
    choices={}
    for i in order:
        s=states[i]
        choices[i]=[]
        for cmd in alternatives(s,commands[i],preventive(states,i,length,commands[i])):
            result=coupled.step(s,cmd,DT,width)
            if result["state"] is not None:
                choices[i].append(dict(command=cmd,result=result))
    selected={};nodes=0;exhausted=False
    def search(k):
        nonlocal nodes,exhausted
        if k==len(order):
            return True
        i=order[k]
        for option in choices[i]:
            if nodes>=node_limit:
                exhausted=True
                return False
            nodes+=1
            end=option["result"]["state"]
            if any(conflict(states[i],states[j],end,selected[j]["result"]["state"],q(length)) for j in selected):
                continue
            selected[i]=option
            if search(k+1):
                return True
            del selected[i]
            if exhausted:
                return False
        return False
    if not search(0):
        return failed("SEARCH_BUDGET" if exhausted else "NO_FEASIBLE_DISCRETE_OPTION",nodes)
    return dict(status="FEASIBLE_COUPLED_STEP",states={i:selected[i]["result"]["state"] for i in ids},
                selected={i:selected[i] for i in ids},nodes=nodes)

def episode(states,ticks,grip=1):
    history=[]; max_nodes=0; invalid=0
    for _ in range(ticks):
        cmds={i:vehicle.control(grip_factor=grip) for i in states}
        r=resolve(states,cmds)
        max_nodes=max(max_nodes,r["nodes"])
        if r["states"] is None:
            return dict(status=r["status"],ticks=len(history),digest=reg.digest(history),invalid=invalid,max_nodes=max_nodes)
        for i,item in r["selected"].items():
            f=item["result"]["forward"]; nxt=r["states"][i]
            invalid+=not (f["max_grip_utilization"]<=1+1e-12 and f["relative_work_error"]<=1e-10 and
                          nxt["progress_m"]>=states[i]["progress_m"] and nxt["vehicle"]["fuel_kg"]<=states[i]["vehicle"]["fuel_kg"])
        states=r["states"]
        history.append([states[i] for i in sorted(states)])
    return dict(status="COMPLETE",ticks=len(history),digest=reg.digest(history),invalid=invalid,max_nodes=max_nodes)

def evaluate(config):
    scenarios={
      "parallel":({1:initial(100,40,-3),2:initial(100,40,3)},1),
      "catch":({1:initial(100,45),2:initial(125,40)},1),
      "wet_pack":({i:initial(100+i*30,40,(-1)**i*2.5) for i in range(1,25)},0.4)}
    rows=[]; invalid=mismatch=incomplete=0
    for name,(states,grip) in scenarios.items():
        a=episode(states,config["ticks"],grip)
        b=episode(dict(reversed(list(states.items()))),config["ticks"],grip)
        invalid+=a["invalid"];mismatch+=a!=b;incomplete+=a["status"]!="COMPLETE"
        rows.append(dict(name=name,**a))
    # Infeasible close approach and budget exhaustion must never commit state.
    s={1:initial(100,60),2:initial(106,0)}
    bad=resolve(s,{i:vehicle.control() for i in s},half_width_m=1.5)
    budget=resolve(scenarios["parallel"][0],{1:vehicle.control(),2:vehicle.control()},node_limit=1)
    invalid+=not (bad["states"] is None and bad["status"]=="NO_FEASIBLE_DISCRETE_OPTION")
    invalid+=not (budget["states"] is None and budget["status"]=="SEARCH_BUDGET")
    return dict(metrics=dict(invalid_states=invalid,replay_mismatches=mismatch,incomplete_episodes=incomplete),
                observations=dict(episodes=rows,ticks=sum(x["ticks"] for x in rows),infeasible=bad["status"],budget=budget["status"],
                limitations="Conservative strip envelopes, finite controls, synthetic coast episodes; not complete physical feasibility, steering, impact, historical geometry, full race or game integration."))

def spec(c):
    return dict(hypothesis="A bounded joint solver can use existing coupled force states without artificial displacement and fail atomically.",
        sources=["REF-105","REF-107","IDEA-005","IDEA-008","IDEA-033","IDEA-040"],
        config={"seed":42,"ticks":100},
        criteria={"invalid_states":c("eq",0),"replay_mismatches":c("eq",0),"incomplete_episodes":c("eq",0)},evaluate=evaluate)
