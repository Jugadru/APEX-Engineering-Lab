"""Constant-force longitudinal toy model in SI, independent of Core 2."""
import math
from . import registry as reg

def integrate(mass_kg,force_n,v0_mps,dt_s,steps):
    reg.require(all(reg.numeric(v) for v in (mass_kg,force_n,v0_mps,dt_s)) and mass_kg>0 and force_n>=0 and v0_mps>=0 and dt_s>0 and type(steps) is int and 1<=steps<=1000,"invalid model inputs")
    a=force_n/mass_kg
    v=v0_mps; x=0.0; euler=0.0
    for _ in range(steps):
        next_v=v+a*dt_s
        x+=(v+next_v)*0.5*dt_s
        euler+=v*dt_s
        v=next_v
    return v,x,euler

def evaluate(config):
    max_v=max_x=0.0; invalid=violations=0; rows=[]
    for force in config["forces_n"]:
        previous=None
        for mass in config["masses_kg"]:
            a=force/mass
            if previous is not None and a>previous: violations+=1
            previous=a
            for steps in config["steps"]:
                t=config["duration_s"]; v0=config["initial_mps"]
                v,x,e=integrate(mass,force,v0,t/steps,steps)
                expected_v=v0+a*t; expected_x=v0*t+0.5*a*t*t
                max_v=max(max_v,abs(v-expected_v)); max_x=max(max_x,abs(x-expected_x))
                invalid+=not all(math.isfinite(y) for y in (v,x,e))
                rows.append({"mass_kg":mass,"force_n":force,"steps":steps,"acceleration_mps2":a,
                             "velocity_error_mps":abs(v-expected_v),"position_error_m":abs(x-expected_x),
                             "euler_error_m":abs(e-expected_x)})
    return {"metrics":{"velocity_error_mps":max_v,"position_error_m":max_x,"monotonic_violations":violations,"invalid_values":invalid},
            "observations":{"cases":len(rows),"rows":rows,"limitations":"Constant force, flat straight, no drag, shift, aero or tyre dynamics; SI toy model only."}}
