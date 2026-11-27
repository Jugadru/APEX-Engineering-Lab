"""Analytical coast oracle and bounded multi-tick invariants for the isolated vehicle."""
import math
from . import registry as reg, physics_vehicle as vehicle
from .physics_core import scalar

def exact_coast(speed_mps,mass_kg,duration_s):
    """dv/dt=-(150+0.48*v^2)/m until rest, with exact displacement."""
    v=scalar(speed_mps,0,200,"speed")
    m=scalar(mass_kg,1,100000,"mass")
    t=scalar(duration_s,0,10,"duration")
    a,b=150/m,0.48/m
    angle=math.atan(v*math.sqrt(b/a))
    remaining=max(0.0,angle-math.sqrt(a*b)*t)
    end=min(v,math.sqrt(a/b)*math.tan(remaining))
    # log1p keeps the small displacement limit well conditioned.
    x=math.log1p(b*(v-end)*(v+end)/(a+b*end*end))/(2*b)
    return {"speed_mps":end,"distance_m":x}

def coast(speed,steps,duration=4):
    reg.require(type(steps) is int and 8<=steps<=1000,"bounded coast steps")
    duration=scalar(duration,0,10,"duration")
    dt=duration/steps
    reg.require(dt==0 or 1e-6<=dt<=0.5,"coast timestep domain")
    state=vehicle.initial(speed=speed); x=0.0
    for _ in range(steps):
        r=vehicle.step(state,vehicle.control(),dt)
        state=r["state"]; x+=r["distance_m"]
    return {"speed_mps":state["speed_mps"],"distance_m":x}

def sequence(initial):
    state=dict(initial)
    initial_ke=0.5*(vehicle.DRY_MASS_KG+state["fuel_kg"])*state["speed_mps"]**2
    work=[]; removed=[]; burns=[]; used=[]; invalid=0; distance=0.0
    # Fixed 120-tick command schedule, no RNG, no launch, recharge or lap reset.
    commands=[vehicle.control(throttle=1,kers_w=60000),vehicle.control(),
              vehicle.control(brake=0.7,ay_mps2=5),vehicle.control(),
              vehicle.control(throttle=1,kers_w=60000,grip_factor=0.5),
              vehicle.control(throttle=1,cut_s=0.2,kers_w=60000)]
    for command in commands:
        for _ in range(20):
            previous=state
            row=vehicle.step(previous,command,0.2)
            state=row["state"]
            work.append(row["drive_work_j"]-row["brake_work_j"]-row["drag_work_j"]-row["rolling_work_j"])
            # At each tick's end, removed fuel carries its share of kinetic energy.
            removed.append(0.5*row["fuel_burn_kg"]*state["speed_mps"]**2)
            burns.append(row["fuel_burn_kg"]); used.append(row["kers_used_j"])
            distance+=row["distance_m"]
            invalid+=not (0<=state["fuel_kg"]<=previous["fuel_kg"] and
                          0<=state["store_j"]<=previous["store_j"] and
                          0<=state["lap_j"]<=previous["lap_j"] and
                          state["speed_mps"]>=0 and row["distance_m"]>=0 and
                          row["energy_residual_j"]<=1e-7 and row["max_grip_utilization"]<=1+1e-12)
    final_ke=0.5*(vehicle.DRY_MASS_KG+state["fuel_kg"])*state["speed_mps"]**2
    net=math.fsum(work); change=final_ke-initial_ke+math.fsum(removed)
    return {"final_state":state,"ticks":120,"distance_m":distance,"invalid_ticks":invalid,
            "relative_work_error":abs(net-change)/max(1,abs(net),abs(change)),
            "fuel_residual_kg":abs(initial["fuel_kg"]-state["fuel_kg"]-math.fsum(burns)),
            "store_residual_j":abs(initial["store_j"]-state["store_j"]-math.fsum(used)),
            "lap_residual_j":abs(initial["lap_j"]-state["lap_j"]-math.fsum(used))}

def evaluate(config):
    rows=[]; fine_v=fine_x=0.0; convergence=0
    for speed in config["speeds"]:
        oracle=exact_coast(speed,vehicle.DRY_MASS_KG+5,config["duration_s"])
        prev=None
        for steps in config["steps"]:
            r=coast(speed,steps,config["duration_s"])
            ev=abs(r["speed_mps"]-oracle["speed_mps"]); ex=abs(r["distance_m"]-oracle["distance_m"])
            if prev is not None: convergence+=int(ev>prev[0]+1e-9)+int(ex>prev[1]+1e-9)
            prev=(ev,ex)
            rows.append({"initial_mps":speed,"steps":steps,"dt_s":config["duration_s"]/steps,
                         "speed_error_mps":ev,"position_error_m":ex,**r})
        fine_v=max(fine_v,prev[0]); fine_x=max(fine_x,prev[1])
    sequences=[]; invalid=mismatches=0; work=fuel=store=lap=0.0
    for v,f,s,l in config["initial_states"]:
        start=vehicle.initial(v,f,s,l)
        r=sequence(start); repeat=sequence(start)
        mismatches+=reg.digest(r)!=reg.digest(repeat)
        invalid+=r["invalid_ticks"]; work=max(work,r["relative_work_error"]); fuel=max(fuel,r["fuel_residual_kg"])
        store=max(store,r["store_residual_j"]); lap=max(lap,r["lap_residual_j"])
        sequences.append({"initial":start,**r,"repeat_sha256":reg.digest(repeat)})
    return {"metrics":{"convergence_violations":convergence,"fine_speed_error_mps":fine_v,"fine_position_error_m":fine_x,
                       "invalid_ticks":invalid,"determinism_mismatches":mismatches,"relative_work_error":work,
                       "fuel_residual_kg":fuel,"store_residual_j":store,"lap_residual_j":lap},
            "observations":{"coast_cases":len(rows),"sequence_cases":len(sequences),"sequence_ticks_including_repeat":len(sequences)*240,
                "rows":rows,"sequences":sequences,"limitations":"Analytical coast oracle for fixed artificial drag/rolling forces; frozen-tick forward model, no race, measured vehicle data, platform-wide bitwise guarantee or lateral integration."}}

def spec(c):
    return dict(hypothesis="Refinement reduces coast error against analytical reference; repeated multi-tick sequences preserve state, mass and cumulative work.",
        sources=["REF-107","IDEA-005","IDEA-008","IDEA-010"],config={"seed":42,"speeds":[0.5,30,60],"duration_s":4,
        "steps":[20,40,80,160],"initial_states":[[30,5,400000,400000],[70,0.001,1000,1000],[60,0,0,0]]},
        criteria={"convergence_violations":c("eq",0),"fine_speed_error_mps":c("le",0.2,"m/s"),"fine_position_error_m":c("le",0.5,"m"),
                  "invalid_ticks":c("eq",0),"determinism_mismatches":c("eq",0),"relative_work_error":c("le",1e-8,"ratio"),
                  "fuel_residual_kg":c("le",1e-10,"kg"),"store_residual_j":c("le",1e-6,"J"),"lap_residual_j":c("le",1e-6,"J")},evaluate=evaluate)
