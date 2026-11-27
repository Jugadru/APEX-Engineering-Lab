"""Bounded closed-loop kinematics; not a full vehicle or sporting controller."""
from fractions import Fraction as Q
from itertools import combinations
from . import registry as reg, racecraft_core as core, racecraft_collision as col
from . import racecraft_space as space, racecraft_integration as tactical, physics_core

DT=Q(1,5)
ACCEL=400 # mm/s change per 0.2 s
BRAKE=1600
LAT_STEP=500
MAX_NODES=4096

def options(car,aim,width):
    """Fixed constant-acceleration options; speed lattice ensures exact endpoints."""
    reg.require(car.speed_mm_s%10==0,"motion speed lattice 10 mm/s")
    limit=width-space.WIDTH_MM//2-space.BUFFER_MM
    core.integer(aim,-width,width,"aim")
    y=car.lateral_mm+max(-LAT_STEP,min(LAT_STEP,aim-car.lateral_mm))
    offsets=list(dict.fromkeys([y,car.lateral_mm]))
    out=[]
    for v in dict.fromkeys([min(200000,car.speed_mm_s+ACCEL),car.speed_mm_s,max(0,car.speed_mm_s-BRAKE)]):
        x=car.progress_mm+(car.speed_mm_s+v)//10
        if x>2000000000: continue
        for offset in offsets:
            if abs(offset)<=limit:
                out.append(dict(progress_mm=x,lateral_mm=offset,speed_mm_s=v))
    return out

def swept_conflict(s,a,b,ea,eb):
    """Sufficient conservative separation for quadratic longitudinal motion.
    Each constant-acceleration arc differs from its chord by <= |dv|/40 mm.
    Enlarge the relative longitudinal envelope by both arc error bounds.
    Lateral center is linear; rectangles remain axis aligned.
    """
    x=b.progress_mm-a.progress_mm
    dx=(eb["progress_mm"]-b.progress_mm)-(ea["progress_mm"]-a.progress_mm)
    y=b.lateral_mm-a.lateral_mm
    dy=(eb["lateral_mm"]-b.lateral_mm)-(ea["lateral_mm"]-a.lateral_mm)
    pad=(abs(ea["speed_mm_s"]-a.speed_mm_s)+abs(eb["speed_mm_s"]-b.speed_mm_s)+39)//40
    long=col.LONG+pad
    ly=col.interval(y,dy,col.LAT)
    if ly is None:return False
    lo=min(x,x+dx)-long;hi=max(x,x+dx)+long
    for k in range(-((-lo)//s.length_mm),hi//s.length_mm+1):
        lx=col.interval(x-k*s.length_mm,dx,long)
        if lx is not None and max(lx[0],ly[0])<=min(lx[1],ly[1]):return True
    return False

def resolve(s,aims,node_limit=MAX_NODES):
    core.integer(node_limit,1,MAX_NODES,"search budget")
    cars=tuple(c for c in s.cars if c.active)
    reg.require(isinstance(aims,dict) and all(type(i) is int for i in aims) and set(aims)=={c.id for c in cars},"aim roster")
    for c in cars:core.integer(aims[c.id],-s.half_width_mm,s.half_width_mm,"aim")
    if any(abs(c.lateral_mm)>s.half_width_mm-space.WIDTH_MM//2-space.BUFFER_MM for c in cars):
        return dict(status="INITIAL_STATE_INVALID",snapshot=None,nodes=0)
    for a,b in combinations(cars,2):
        if col.contact(s,a.id,b.id,col.endpoint(a.progress_mm,a.lateral_mm),col.endpoint(b.progress_mm,b.lateral_mm))["contact"]:
            return dict(status="INITIAL_STATE_INVALID",snapshot=None,nodes=0)
    order=sorted(cars,key=lambda c:(-c.progress_mm,c.id))
    choices={c.id:options(c,aims[c.id],s.half_width_mm) for c in order}
    selected={}; nodes=0; exhausted=False
    def search(k):
        nonlocal nodes,exhausted
        if k==len(order):return True
        a=order[k]
        for ea in choices[a.id]:
            if nodes>=node_limit:
                exhausted=True;return False
            nodes+=1
            if any(swept_conflict(s,a,b,ea,selected[b.id]) for b in order[:k]):continue
            selected[a.id]=ea
            if search(k+1):return True
            del selected[a.id]
            if exhausted:return False
        return False
    if s.tick==1000000:return dict(status="STATE_LIMIT",snapshot=None,nodes=0)
    if not search(0):
        return dict(status="SEARCH_BUDGET" if exhausted else "NO_FEASIBLE_DISCRETE_OPTION",snapshot=None,nodes=nodes)
    rows=[dict(id=c.id,active=True,**selected[c.id]) if c.active else core.row(c.id,c.progress_mm,c.lateral_mm,c.speed_mm_s,False) for c in s.cars]
    nxt=core.Snapshot.from_rows(s.tick+1,s.length_mm,s.half_width_mm,rows)
    return dict(status="FEASIBLE_MODEL_STEP",snapshot=nxt,nodes=nodes)

def sample_position(a,b,t):
    # independent actual quadratic trajectory, t normalized to [0,1]
    return (a.progress_mm+DT*(a.speed_mm_s*t+Q(b.speed_mm_s-a.speed_mm_s,2)*t*t),
            a.lateral_mm+(b.lateral_mm-a.lateral_mm)*t)

def check_step(s,nxt):
    errors=0; residual=[0.0,0.0]
    cars=[c for c in s.cars if c.active]
    for a in cars:
        b=nxt.car(a.id);dv=b.speed_mm_s-a.speed_mm_s
        errors+=not (-BRAKE<=dv<=ACCEL and abs(b.lateral_mm-a.lateral_mm)<=LAT_STEP and b.progress_mm>=a.progress_mm)
        ref=physics_core.step_force(700,a.speed_mm_s/1000,700*dv/200,0.2)
        residual[0]=max(residual[0],abs(ref["distance_m"]-(b.progress_mm-a.progress_mm)/1000));residual[1]=max(residual[1],abs(ref["speed_mps"]-b.speed_mm_s/1000))
    for a,b in combinations(cars,2):
        for i in range(21):
            t=Q(i,20);x,y=sample_position(a,nxt.car(a.id),t);u,v=sample_position(b,nxt.car(b.id),t)
            d=(u-x)%s.length_mm
            errors+=min(d,s.length_mm-d)<=col.LONG and abs(v-y)<=col.LAT
    return errors,residual

def run_episode(rows,ticks,reverse=False):
    s=core.Snapshot.from_rows(0,5000000,5000,rows[::-1] if reverse else rows)
    history=[s.payload()]; memory=None; errors=0;residual=[0.0,0.0];max_nodes=0;advanced=0
    for _ in range(ticks):
        profiles,ctx=tactical.inputs(s)
        p=tactical.plan(s,profiles,ctx,memory)
        aims={d["id"]:d["aim_mm"] for d in p["decisions"]}
        r=resolve(s,aims)
        max_nodes=max(max_nodes,r["nodes"])
        if r["snapshot"] is None:
            return dict(status=r["status"],ticks=advanced,digest=reg.digest(history),errors=errors,residual=residual,max_nodes=max_nodes)
        nxt=r["snapshot"]
        bad,err=check_step(s,nxt);errors+=bad;residual=[max(x,y) for x,y in zip(residual,err)]
        advanced+=1;history.append(nxt.payload());s=nxt;memory=p["memory"]
    return dict(status="COMPLETE",ticks=advanced,digest=reg.digest(history),errors=errors,residual=residual,max_nodes=max_nodes,
                distance_mm=sum(c.progress_mm for c in s.cars)-sum(r["progress_mm"] for r in rows))

def evaluate(config):
    scenarios={"parallel":[core.row(1,100000,-3000,40000),core.row(2,100000,3000,40000)],
               "catch":[core.row(1,100000,0,45000),core.row(2,120000,0,40000)],
               "pack":[core.row(i,100000+i*30000,(-1)**i*2500,35000) for i in range(1,25)]}
    rows=[];errors=mismatches=incomplete=0;residual=[0.0,0.0]
    for name,rs in scenarios.items():
        a=run_episode(rs,config["ticks"]);b=run_episode(rs,config["ticks"],True)
        errors+=a["errors"];residual=[max(x,y) for x,y in zip(residual,a["residual"])]
        mismatches+=a!=b;incomplete+=a["status"]!="COMPLETE" or a.get("distance_mm",0)<=0
        rows.append(dict(scenario=name,**a))
    # Impossible one-tick close approach: no artificial zero-speed fallback.
    s=core.Snapshot.from_rows(0,5000000,1500,[core.row(1,100000,0,60000),core.row(2,106000,0,0)])
    r=resolve(s,{1:0,2:0})
    errors+=r["snapshot"] is not None or r["status"]!="NO_FEASIBLE_DISCRETE_OPTION"
    return {"metrics":{"invalid_motion":errors,"replay_mismatches":mismatches,"incomplete_episodes":incomplete,"distance_error_m":residual[0],"speed_error_mps":residual[1]},
            "observations":{"episodes":rows,"infeasible_status":r["status"],"ticks":sum(x["ticks"] for x in rows),
             "limitations":"Synthetic bounded constant-acceleration/linear lateral model, conservative chord envelope, finite options and budget; not full coupled dynamics, real track, sport or guaranteed feasible recovery."}}

def spec(c):
    return dict(hypothesis="Bounded physically consistent longitudinal steps can evolve scripted-free states without artificial freezing, report infeasible cases, and replay deterministically.",
      sources=["REF-105","REF-107","IDEA-030","IDEA-033","IDEA-040","IDEA-005"],config={"seed":42,"ticks":16},
      criteria={"invalid_motion":c("eq",0),"replay_mismatches":c("eq",0),"incomplete_episodes":c("eq",0),"distance_error_m":c("le",1e-9,"m"),"speed_error_mps":c("le",1e-9,"m/s")},evaluate=evaluate)
