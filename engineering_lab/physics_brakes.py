"""Straight-line friction-limited brake work and adiabatic heat ledger."""
import math
from . import registry as reg
from .physics_core import scalar,step_force

def brake_step(mass_kg,speed_mps,request_n,normal_n,mu,dt_s,front_fraction):
    m=scalar(mass_kg,1,100000,"mass_kg")
    v=scalar(speed_mps,0,200,"speed_mps")
    request=scalar(request_n,0,1000000,"request_n")
    cap=scalar(normal_n,0,100000,"normal_n")*scalar(mu,0,5,"mu")
    front=scalar(front_fraction,0,1,"front_fraction")
    force=min(request,cap)
    step=step_force(m,v,-force,dt_s)
    heat=-step["net_work_j"]
    return {**step,"brake_force_n":force,"demand_exceeds_grip":request>cap,
            "heat_j":heat,"front_heat_j":heat*front,"rear_heat_j":heat*(1-front)}

def stopping_distance(mass_kg,speed_mps,brake_n):
    m=scalar(mass_kg,1,100000,"mass_kg")
    v=scalar(speed_mps,0,200,"speed_mps")
    f=scalar(brake_n,0,1000000,"brake_n")
    if not v: return 0.0
    if not f: return None
    distance=m*v*v/(2*f)
    reg.require(math.isfinite(distance),"stopping distance not representable in binary64")
    return distance

def heat_rise(heat_j,capacity_j_per_k):
    return scalar(heat_j,0,1e10,"heat_j")/scalar(capacity_j_per_k,1,1e7,"heat capacity")

def evaluate(config):
    rows=[]; bad=0; balance=distance_error=0.0
    for m in config["masses"]:
        for v in config["speeds"]:
            for mu in config["mu"]:
                for request in config["requests"]:
                    r=brake_step(m,v,request,m*9.81,mu,config["dt"],0.6)
                    bad+=not (0<=r["speed_mps"]<=v and 0<=r["brake_force_n"]<=request and
                              r["brake_force_n"]<=m*9.81*mu and r["heat_j"]>=0)
                    balance=max(balance,abs(r["front_heat_j"]+r["rear_heat_j"]-r["heat_j"])/max(1,r["heat_j"]),r["relative_work_error"])
                    d=stopping_distance(m,v,r["brake_force_n"])
                    if d is not None:
                        distance_error=max(distance_error,max(0,r["distance_m"]-d))
                        if r["speed_mps"]==0: distance_error=max(distance_error,abs(r["distance_m"]-d))
                    rows.append({"mass_kg":m,"initial_mps":v,"mu":mu,"request_n":request,"stop_distance_m":d,**r})
    return {"metrics":{"invalid_states":bad,"relative_heat_work_error":balance,"stop_distance_excess_m":distance_error},
            "observations":{"cases":len(rows),"rows":rows,"limitations":"Constant straight-line brake force, all brake work assigned to heat; demand saturation is not wheel-lock detection; no cooling, ABS, disc temperature model or tyre calibration."}}

def spec(c):
    return dict(hypothesis="Friction-limited braking cannot reverse, exceeds neither request nor grip, and dissipated work balances heat and kinetic loss.",
                sources=["REF-107","IDEA-013","IDEA-014","IDEA-015"],config={"seed":42,"masses":[600,800],"speeds":[0,5,60],"mu":[0,0.6,1.5],"requests":[0,4000,12000],"dt":2},
                criteria={"invalid_states":c("eq",0),"relative_heat_work_error":c("le",1e-10,"ratio"),"stop_distance_excess_m":c("le",1e-10,"m")},evaluate=evaluate)
