"""Small-angle dynamic bicycle reference with actual axle grip saturation.

Synthetic parameters, fixed 10 ms substeps. Body lateral velocity and yaw
moment are propagated; not a full planar work-energy or steering calibration.
"""
import math
from . import registry as reg, physics_vehicle as vehicle
from .physics_core import scalar

DT=0.01
FRONT_M=1.728
REAR_M=1.472
INERTIA=900.0
## Synthetic stable-understeer reference: rear cornering stiffness has
## reserve relative to its CG lever arm (CR*REAR_M > CF*FRONT_M).
## Not estimates of a 2012 tyre or car.
CF=45000.0
CR=90000.0
STEER_MAX=0.3
STEER_RATE=0.8

def initial(speed=40):
    return dict(x_m=0.0,y_m=0.0,heading_rad=0.0,yaw_rad_s=0.0,
                body_vy_mps=0.0,steer_rad=0.0,vehicle=vehicle.initial(speed))

def step(state,command,steer_target,substeps=20):
    reg.exact(state,"x_m y_m heading_rad yaw_rad_s body_vy_mps steer_rad vehicle")
    reg.require(type(substeps) is int and 1<=substeps<=50,"substeps")
    target=scalar(steer_target,-STEER_MAX,STEER_MAX,"steer target")
    x=scalar(state["x_m"],-2000000,2000000,"x")
    y=scalar(state["y_m"],-2000000,2000000,"y")
    h=scalar(state["heading_rad"],-math.pi,math.pi,"heading")
    r=scalar(state["yaw_rad_s"],-3,3,"yaw rate")
    w=scalar(state["body_vy_mps"],-15,15,"body lateral speed")
    steer=scalar(state["steer_rad"],-STEER_MAX,STEER_MAX,"steer")
    forward=state["vehicle"]
    # Validate baseline command and state before modifying requested lateral demand.
    vehicle.step(forward,command,0)
    reg.require(command["ay_mps2"]==0,"steering replaces prescribed lateral demand")
    def failure(reason):
        return dict(status=reason,state=None,trace=[])
    trace=[]
    for _ in range(substeps):
        v=forward["speed_mps"]
        if not 10<=v<=100:
            return failure("SPEED_DOMAIN")
        steer+=max(-STEER_RATE*DT,min(STEER_RATE*DT,target-steer))
        af=steer-(w+FRONT_M*r)/v
        ar=-(w-REAR_M*r)/v
        if max(abs(af),abs(ar))>0.35:
            return failure("SLIP_DOMAIN")
        fyf,fyr=CF*af,CR*ar
        mass=vehicle.DRY_MASS_KG+forward["fuel_kg"]
        ay=max(-30,min(30,(fyf+fyr)/mass))
        f=vehicle.step(forward,dict(command,ay_mps2=ay),DT,(fyf,fyr))
        front,rear=f["front_lateral_n"],f["rear_lateral_n"]
        moment=FRONT_M*front-REAR_M*rear
        rd=moment/INERTIA
        wd=(front+rear)/mass-v*r
        nr=r+DT*rd
        nw=w+DT*wd
        nv=f["state"]["speed_mps"]
        if not (10<=nv<=100 and abs(nr)<=3 and abs(nw)<=15):
            return failure("MOTION_DOMAIN")
        mid_h=h+0.25*DT*(r+nr)
        dx=f["distance_m"]*math.cos(mid_h)-DT*(w+nw)*0.5*math.sin(mid_h)
        dy=f["distance_m"]*math.sin(mid_h)+DT*(w+nw)*0.5*math.cos(mid_h)
        x+=dx;y+=dy
        h=(h+DT*(r+nr)*0.5+math.pi)%(2*math.pi)-math.pi
        if max(abs(x),abs(y))>2000000:
            return failure("POSITION_DOMAIN")
        trace.append(dict(front_n=front,rear_n=rear,yaw_moment_nm=moment,
                          yaw_accel_rad_s2=rd,body_ay_mps2=wd,steer_rad=steer,
                          grip=f["max_grip_utilization"],work_error=f["relative_work_error"]))
        r,w,forward=nr,nw,f["state"]
    nxt=dict(x_m=x,y_m=y,heading_rad=h,yaw_rad_s=r,body_vy_mps=w,
             steer_rad=steer,vehicle=forward)
    return dict(status="FEASIBLE_YAW_REFERENCE",state=nxt,trace=trace)

def episode(target,grip,brake,ticks):
    state=initial();history=[];invalid=0;max_grip=0.0;max_work=0.0
    for i in range(ticks):
        r=step(state,vehicle.control(grip_factor=grip,brake=brake),
               target if i<ticks//2 else 0)
        if r["state"] is None:
            return dict(status=r["status"],ticks=len(history),invalid=invalid,max_grip=max_grip,max_work=max_work)
        for t in r["trace"]:
            max_grip=max(max_grip,t["grip"])
            max_work=max(max_work,t["work_error"])
            invalid+=abs(t["yaw_moment_nm"]-(FRONT_M*t["front_n"]-REAR_M*t["rear_n"]))>1e-9
        state=r["state"];history.append(state)
    return dict(status="COMPLETE",ticks=len(history),invalid=invalid,max_grip=max_grip,max_work=max_work,
                state=state,digest=reg.digest(history))

def evaluate(config):
    rows=[];bad=repeat=0;grip=work=mirror=0.0
    for factor in config["grip"]:
        for brake in config["brake"]:
            a=episode(config["steer"],factor,brake,config["ticks"])
            b=episode(-config["steer"],factor,brake,config["ticks"])
            repeat+=a!=episode(config["steer"],factor,brake,config["ticks"])
            for r in (a,b):
                bad+=r["status"]!="COMPLETE" or r["invalid"]!=0
                grip=max(grip,r["max_grip"]);work=max(work,r["max_work"])
            if a["status"]==b["status"]=="COMPLETE":
                x,y=a["state"],b["state"]
                mirror=max(mirror,abs(x["x_m"]-y["x_m"]),
                           *(abs(x[k]+y[k]) for k in ("y_m","heading_rad","yaw_rad_s","body_vy_mps","steer_rad")))
                bad+=not (x["y_m"]>0 and y["y_m"]<0)
            rows.append(dict(grip=factor,brake=brake,positive=a,negative=b))
    return dict(metrics=dict(invalid=bad,replay_mismatches=repeat,grip_excess=max(0,grip-1),
                             forward_work_error=work,mirror_error=mirror),
                observations=dict(cases=rows,limitations="Synthetic small-angle bicycle; axle force sharing with longitudinal reference, no exact full planar energy, low-speed model, historical calibration, track boundaries or multi-car application."))

def spec(c):
    return dict(hypothesis="Stateful steering and axle moment can produce bounded repeatable yaw using existing combined force budgets.",
                sources=["REF-107","IDEA-005","IDEA-008","IDEA-015","IDEA-033"],config={"seed":42,"grip":[0.4,1],"brake":[0,0.2],"steer":0.04,"ticks":10},
                criteria={"invalid":c("eq",0),"replay_mismatches":c("eq",0),"grip_excess":c("le",1e-12,"ratio"),
                          "forward_work_error":c("le",1e-10,"ratio"),"mirror_error":c("le",1e-9,"SI")},evaluate=evaluate)
