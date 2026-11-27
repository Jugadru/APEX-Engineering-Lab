"""Joint bounded yaw motion with oriented rectangle checks.

Cartesian straight-strip laboratory, not historical track geometry. A 10 ms
numerical substep is represented by linear center and shortest-angle heading
interpolation. Unresolved swept intervals are rejected conservatively.
"""
import math
from itertools import combinations
from . import registry as reg, racecraft_yaw as yaw, physics_vehicle as vehicle
from .physics_core import scalar

HALF_L=2.65
HALF_W=1.05
RADIUS=math.hypot(HALF_L,HALF_W)
EPS=1e-8
MAX_DEPTH=12
MAX_NODES=4096
SUBSTEPS=20

def pose(s):
    return (s["x_m"],s["y_m"],s["heading_rad"])

def angle_delta(a,b):
    return (b-a+math.pi)%(2*math.pi)-math.pi

def interp(a,b,t):
    return (a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+angle_delta(a[2],b[2])*t)

def axes(p):
    c,s=math.cos(p[2]),math.sin(p[2])
    return ((c,s),(-s,c))

def dot(a,b):
    return a[0]*b[0]+a[1]*b[1]

def support(p,axis):
    a,b=axes(p)
    return HALF_L*abs(dot(a,axis))+HALF_W*abs(dot(b,axis))

def separation(a,b):
    delta=(b[0]-a[0],b[1]-a[1])
    return max(abs(dot(delta,axis))-support(a,axis)-support(b,axis) for axis in (*axes(a),*axes(b)))

def travel(a,b):
    return math.hypot(b[0]-a[0],b[1]-a[1])+RADIUS*abs(angle_delta(a[2],b[2]))

def swept(a,ae,b,be):
    """True means contact or unresolved; False certifies separation in the
    declared interpolation, using a fixed separating axis and motion bounds.
    """
    # Center-only broad phase: circumscribed disks cannot intersect.
    center_a=math.hypot(ae[0]-a[0],ae[1]-a[1])
    center_b=math.hypot(be[0]-b[0],be[1]-b[1])
    if math.hypot(b[0]-a[0],b[1]-a[1])>2*RADIUS+center_a+center_b+EPS:
        return False
    bound=travel(a,ae)+travel(b,be)
    def visit(lo,hi,depth):
        mid=(lo+hi)/2
        gap=separation(interp(a,ae,mid),interp(b,be,mid))
        if gap<=EPS:
            return True
        if gap>bound*(hi-lo)/2+EPS:
            return False
        if depth==MAX_DEPTH:
            return True
        return visit(lo,mid,depth+1) or visit(mid,hi,depth+1)
    if separation(a,b)<=EPS or separation(ae,be)<=EPS:
        return True
    return visit(0,1,0)

def inside(a,b,width):
    # Bound the entire interpolated body, not just its center.
    delta=travel(a,b)
    def visit(lo,hi,depth):
        p=interp(a,b,(lo+hi)/2)
        margin=width-abs(p[1])-support(p,(0,1))
        if margin<=EPS:
            return False
        if margin>delta*(hi-lo)/2+EPS:
            return True
        if depth==MAX_DEPTH:
            return False
        mid=(lo+hi)/2
        return visit(lo,mid,depth+1) and visit(mid,hi,depth+1)
    return all(abs(p[1])+support(p,(0,1))<width-EPS for p in (a,b)) and visit(0,1,0)

def path(state,cmd,target,width):
    s=state
    poses=[pose(s)]
    for index in range(SUBSTEPS):
        # The outer 200 ms interval owns the shift duration.
        r=yaw.step(s,yaw.substep_command(cmd,index),target,1)
        if r["state"] is None:
            return None
        s=r["state"]
        p=pose(s)
        if not inside(poses[-1],p,width):
            return None
        poses.append(p)
    return dict(state=s,poses=poses,command=cmd,steer_target=target)

def collide(a,b):
    return any(swept(a[i],a[i+1],b[i],b[i+1]) for i in range(SUBSTEPS))

def controls(command,target):
    coast=dict(command,throttle=0,brake=0,kers_w=0)
    brake=dict(coast,brake=1)
    # Prioritize request; bounded fallback is not continuous optimality.
    result=[]
    for item in [(command,target),(command,0),(coast,target),(coast,0),(brake,0),
                 (brake,target),(coast,-.04),(coast,.04)]:
        if item not in result:
            result.append(item)
    return result

def resolve(states,commands,targets,half_width_m=6,node_limit=MAX_NODES):
    width=scalar(half_width_m,1.1,30,"strip half width")
    reg.require(type(node_limit) is int and 1<=node_limit<=MAX_NODES,"node limit")
    reg.require(type(states) is dict and 1<=len(states)<=24 and all(type(i) is int and 0<=i<=255 for i in states),"roster")
    reg.require(type(commands) is dict and type(targets) is dict and set(states)==set(commands)==set(targets),"input roster")
    ids=sorted(states)
    def fail(status,nodes=0):
        return dict(status=status,states=None,selected=None,nodes=nodes)
    for i in ids:
        # Validate all fields even when geometry is initially invalid.
        yaw.step(states[i],commands[i],targets[i],1)
    if any(not inside(pose(states[i]),pose(states[i]),width) for i in ids):
        return fail("INITIAL_STATE_INVALID")
    if any(separation(pose(states[i]),pose(states[j]))<=EPS for i,j in combinations(ids,2)):
        return fail("INITIAL_STATE_INVALID")
    # Lazily build candidate trajectories; each option computed at most once.
    order=sorted(ids,key=lambda i:(-states[i]["x_m"],i))
    cache={i:{} for i in ids}
    options={i:controls(commands[i],targets[i]) for i in ids}
    chosen={};nodes=0;exhausted=False
    def search(index):
        nonlocal nodes,exhausted
        if index==len(order):
            return True
        i=order[index]
        for k,(cmd,target) in enumerate(options[i]):
            if nodes>=node_limit:
                exhausted=True
                return False
            nodes+=1
            if k not in cache[i]:
                cache[i][k]=path(states[i],cmd,target,width)
            p=cache[i][k]
            if p is None or any(collide(p["poses"],q["poses"]) for q in chosen.values()):
                continue
            chosen[i]=p
            if search(index+1):
                return True
            del chosen[i]
            if exhausted:
                return False
        return False
    if not search(0):
        return fail("SEARCH_BUDGET" if exhausted else "NO_FEASIBLE_DISCRETE_OPTION",nodes)
    return dict(status="FEASIBLE_ORIENTED_STEP",states={i:chosen[i]["state"] for i in ids},
                selected={i:chosen[i] for i in ids},nodes=nodes)

def episode(states,grip,ticks):
    history=[];nodes=0
    for t in range(ticks):
        commands={i:vehicle.control(grip_factor=grip) for i in states}
        targets={i:0 for i in states}
        r=resolve(states,commands,targets)
        nodes=max(nodes,r["nodes"])
        if r["states"] is None:
            return dict(status=r["status"],ticks=t,max_nodes=nodes)
        states=r["states"]
        history.append([states[i] for i in sorted(states)])
    return dict(status="COMPLETE",ticks=ticks,max_nodes=nodes,digest=reg.digest(history))

def evaluate(config):
    rows=[];bad=repeat=0
    for grip in config["grip"]:
        states={i:dict(yaw.initial(),x_m=i*30,y_m=(-1)**i*2.0) for i in range(24)}
        a=episode(states,grip,config["ticks"])
        b=episode(dict(reversed(list(states.items()))),grip,config["ticks"])
        bad+=a["status"]!="COMPLETE";repeat+=a!=b
        rows.append(dict(grip=grip,**a))
    # Rotated contact and mid-interval crossing with disjoint endpoints.
    bad+=not (separation((0,0,0),(0,2.5,0))>0 and separation((0,0,math.pi/2),(0,2.5,0))<=0)
    bad+=not swept((-8,0,0),(8,0,0),(0,0,0),(0,0,0))
    return dict(metrics=dict(invalid=bad,replay_mismatches=repeat),
                observations=dict(episodes=rows,limitations="Synthetic Cartesian strip; linear pose interpolation of 10 ms numerical substeps; conservative uncertain contact; finite alternatives, no impact, launch, curved track or official integration."))

def spec(c):
    return dict(hypothesis="Joint yaw states respect oriented swept separation and strip bounds under bounded deterministic control selection.",
                sources=["REF-107","IDEA-005","IDEA-008","IDEA-033"],config={"seed":42,"grip":[.4,1],"ticks":8},
                criteria={"invalid":c("eq",0),"replay_mismatches":c("eq",0)},evaluate=evaluate)
