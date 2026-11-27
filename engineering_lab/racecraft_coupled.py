"""Local 2D force-coupled reference; not a yaw/steering or sporting controller."""
from . import registry as reg, physics_vehicle as vehicle
from .physics_core import scalar
from . import racecraft_space as space

MARGIN_M=(space.WIDTH_MM/2+space.BUFFER_MM)/1000

def lateral_path(y,vy,ay,dt):
    end=y+vy*dt+0.5*ay*dt*dt
    points=[y,end]
    if ay:
        t=-vy/ay
        if 0<t<dt:points.append(y+vy*t+0.5*ay*t*t)
    return end,vy+ay*dt,min(points),max(points)

def initial(speed=40,y=0,vy=0,fuel=5):
    return dict(progress_m=0.0,lateral_m=y,lateral_speed_mps=vy,vehicle=vehicle.initial(speed,fuel))

def step(state,command,dt_s,half_width_m=5):
    reg.exact(state,"progress_m lateral_m lateral_speed_mps vehicle")
    x=scalar(state["progress_m"],0,2000000,"progress")
    y=scalar(state["lateral_m"],-15,15,"lateral position")
    vy=scalar(state["lateral_speed_mps"],-10,10,"lateral velocity")
    width=scalar(half_width_m,MARGIN_M,15,"track half-width")
    dt=scalar(dt_s,0,0.5,"dt")
    limit=width-MARGIN_M
    # Call the existing force/energy reference, never a duplicate force budget.
    f=vehicle.step(state["vehicle"],command,dt)
    ay=f["lateral_force_n"]/f["mass_kg"]
    end_y,end_vy,lo,hi=lateral_path(y,vy,ay,dt)
    result={"state":None,"status":"BOUNDARY_BLOCKED","lateral_accel_mps2":ay,
            "lateral_min_m":lo,"lateral_max_m":hi,"forward":f,
            "lateral_kinematic_work_residual_j":abs(0.5*f["mass_kg"]*(end_vy-vy)*(end_vy+vy)-f["lateral_force_n"]*(end_y-y))}
    if abs(y)>limit:return {**result,"status":"INITIAL_OUTSIDE"}
    if lo<-limit or hi>limit:return result
    if dt and (state["vehicle"]["speed_mps"]<5 or f["state"]["speed_mps"]<5) and (vy or ay):
        return {**result,"status":"LOW_SPEED_LATERAL_NOT_MODELLED"}
    if abs(end_vy)>10 or x+f["distance_m"]>2000000:
        return {**result,"status":"MOTION_DOMAIN_BLOCKED"}
    nxt=dict(progress_m=x+f["distance_m"],lateral_m=end_y,lateral_speed_mps=end_vy,vehicle=f["state"])
    return {**result,"status":"FEASIBLE_REFERENCE_STEP","state":nxt}

def evaluate(config):
    rows=[];invalid=0;residual=work=grip=0.0;accepted=blocked=0
    for speed in config["speeds"]:
        for factor in config["grip"]:
            for demand in config["lateral_accel"]:
                for brake in config["brake"]:
                    s=initial(speed)
                    cmd=vehicle.control(throttle=0.5,brake=brake,ay_mps2=demand,grip_factor=factor)
                    r=step(s,cmd,0.2);f=r["forward"]
                    invalid+=r["status"]!="FEASIBLE_REFERENCE_STEP"
                    if r["state"] is not None:
                        accepted+=1;n=r["state"]
                        invalid+=not (n["progress_m"]>=s["progress_m"] and abs(n["lateral_m"])<=5-MARGIN_M and
                                      abs(r["lateral_accel_mps2"])<=abs(demand)+1e-9 and
                                      0<=n["vehicle"]["fuel_kg"]<=s["vehicle"]["fuel_kg"])
                    residual=max(residual,r["lateral_kinematic_work_residual_j"])
                    work=max(work,f["relative_work_error"]);grip=max(grip,max(0,f["max_grip_utilization"]-1))
                    rows.append(dict(speed_mps=speed,grip=factor,ay_request_mps2=demand,brake=brake,status=r["status"],ay_mps2=r["lateral_accel_mps2"]))
    # Feed accepted force/energy/lateral states into the next reference step.
    sequences=[]
    for sign in (-1,1):
        s=initial();history=[]
        for t in range(8):
            r=step(s,vehicle.control(throttle=0.1,ay_mps2=sign*(2 if t<4 else -2)),0.2)
            if r["state"] is None:
                invalid+=1;break
            residual=max(residual,r["lateral_kinematic_work_residual_j"])
            work=max(work,r["forward"]["relative_work_error"])
            grip=max(grip,max(0,r["forward"]["max_grip_utilization"]-1))
            s=r["state"];history.append(s)
        invalid+=len(history)!=8
        invalid+=abs(s["lateral_speed_mps"])>1e-8 or not 0.5<=sign*s["lateral_m"]<=2
        sequences.append(dict(sign=sign,ticks=len(history),final_lateral_m=s["lateral_m"],final_vy_mps=s["lateral_speed_mps"],digest=reg.digest(history)))
    for s,cmd in [(initial(y=3.79,vy=1),vehicle.control()),(initial(y=-3.79,vy=-1),vehicle.control())]:
        original=reg.digest(s);r=step(s,cmd,0.2)
        blocked+=r["status"]=="BOUNDARY_BLOCKED" and r["state"] is None
        invalid+=reg.digest(s)!=original
    return {"metrics":{"invalid_states":invalid,"boundary_count_error":abs(blocked-2),
                        "lateral_work_residual_j":residual,"longitudinal_relative_work_error":work,"grip_excess":grip},
            "observations":{"force_cases":len(rows),"accepted_force_cases":accepted,"boundary_blocked":blocked,"sequences":sequences,"rows":rows,
              "limitations":"Local straight strip, stateful lateral velocity using actual saturated lateral force, frozen mass/force per tick. Separate work identities, not full 2D drivetrain energy, yaw, steering, thermal evolution, real geometry or calibrated motion."}}

def spec(c):
    return dict(hypothesis="Existing combined grip and force ledger supports bounded local lateral kinematics without teleport or accepting an out-of-envelope path.",
        sources=["REF-107","IDEA-005","IDEA-008","IDEA-015","IDEA-033"],config={"seed":42,"speeds":[30,50],"grip":[0.3,1],"lateral_accel":[-12,0,12],"brake":[0,1]},
        criteria={"invalid_states":c("eq",0),"boundary_count_error":c("eq",0),"lateral_work_residual_j":c("le",1e-8,"J"),
                  "longitudinal_relative_work_error":c("le",1e-10,"ratio"),"grip_excess":c("le",1e-12,"ratio")},evaluate=evaluate)
