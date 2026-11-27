"""Original SI reference primitives; bounded forward-motion domain, no game state."""
from . import registry as reg

def scalar(value,lo,hi,name):
    reg.require(reg.numeric(value) and lo<=value<=hi,"invalid "+name)
    return float(value)

def step_force(mass_kg,speed_mps,force_n,dt_s):
    """Exact constant net force until stop; no reversing or negative displacement."""
    m=scalar(mass_kg,1,100000,"mass_kg")
    v=scalar(speed_mps,0,100000,"speed_mps")
    force=scalar(force_n,-10000000,10000000,"force_n")
    dt=scalar(dt_s,0,10,"dt_s")
    a=force/m
    stop=v/-a if a<0 else None
    if stop is not None and stop<=dt:
        active=stop
        end=0.0  # Exact stop identity; avoid positive rounding residue.
    elif v==0 and a<=0:
        active=0.0
        end=0.0
    else:
        active=dt
        end=max(0.0,v+a*active)
    distance=(v+end)*0.5*active
    work=force*distance
    delta=0.5*m*(end-v)*(end+v)
    residual=abs(delta-work)/max(1.0,abs(delta),abs(work))
    return {"speed_mps":end,"distance_m":distance,"moving_interval_s":active,
            "net_work_j":work,"delta_kinetic_j":delta,"relative_work_error":residual}

def evaluate(config):
    rows=[]; err=0.0; invalid=0
    for m in config["masses_kg"]:
        for v in config["speeds_mps"]:
            for force in config["forces_n"]:
                for dt in config["steps_s"]:
                    r=step_force(m,v,force,dt)
                    err=max(err,r["relative_work_error"])
                    invalid+=not (r["speed_mps"]>=0 and r["distance_m"]>=0 and 0<=r["moving_interval_s"]<=dt)
                    rows.append({"mass_kg":m,"initial_mps":v,"force_n":force,"dt_s":dt,**r})
    return {"metrics":{"relative_work_error":err,"invalid_states":invalid},
            "observations":{"cases":len(rows),"rows":rows,"limitations":"Constant net force and forward-only stop. No external energy source, powertrain or tyre model."}}

def spec(c):
    return dict(hypothesis="Exact forward constant-force step conserves work-energy and cannot reverse under braking.",
                sources=["REF-107","IDEA-005","IDEA-008"],config={"seed":42,"masses_kg":[600,800],"speeds_mps":[0,1,40],"forces_n":[-8000,0,6000],"steps_s":[0,0.2,2]},
                criteria={"relative_work_error":c("le",1e-10,"ratio"),"invalid_states":c("eq",0)},evaluate=evaluate)
