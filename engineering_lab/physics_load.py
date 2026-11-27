"""Quasi-static load redistribution and a separate underdamped spring reference."""
import math
from . import registry as reg
from .physics_core import scalar

def corner_loads(mass_kg,ax_mps2,ay_mps2,downforce_n,front_fraction,aero_front_fraction,cg_m,wheelbase_m,track_m):
    m=scalar(mass_kg,1,100000,"mass"); ax=scalar(ax_mps2,-100,100,"ax"); ay=scalar(ay_mps2,-100,100,"ay")
    aero=scalar(downforce_n,0,100000,"downforce")
    front=scalar(front_fraction,0,1,"front_fraction"); af=scalar(aero_front_fraction,0,1,"aero_front_fraction")
    cg=scalar(cg_m,0,5,"cg"); wb=scalar(wheelbase_m,0.1,20,"wheelbase"); track=scalar(track_m,0.1,20,"track")
    total=m*9.81+aero
    static_front=m*9.81*front+aero*af
    req_long=m*ax*cg/wb
    req_lat=m*ay*cg/track
    front_n=min(total,max(0.0,static_front-req_long))
    rear_n=total-front_n
    # Positive ay loads right side; proportional axle share, no roll model.
    lat=max(-total/2,min(total/2,req_lat))
    frac=lat/total
    corners={"fl_n":front_n*(0.5-frac),"fr_n":front_n*(0.5+frac),
             "rl_n":rear_n*(0.5-frac),"rr_n":rear_n*(0.5+frac)}
    return {**corners,"total_n":total,"requested_long_n":req_long,"realized_long_n":static_front-front_n,
            "requested_lat_n":req_lat,"realized_lat_n":lat,
            "saturated":not 0<=static_front-req_long<=total or abs(req_lat)>total/2}

def spring_step(mass_kg,k_n_per_m,c_ns_per_m,x_m,v_mps,dt_s):
    """Analytical unforced underdamped perturbation about static equilibrium."""
    m=scalar(mass_kg,1,10000,"sprung mass"); k=scalar(k_n_per_m,1,10000000,"spring")
    c=scalar(c_ns_per_m,0,1000000,"damper"); x=scalar(x_m,-2,2,"deflection"); v=scalar(v_mps,-100,100,"velocity")
    dt=scalar(dt_s,0,10,"dt_s")
    alpha=c/(2*m); omega2=k/m-alpha*alpha
    reg.require(omega2>0,"reference supports only underdamped/undamped case")
    omega=math.sqrt(omega2)
    z=omega*dt
    # sin(z)/omega evaluated with limiting value near zero.
    sinc=dt if z==0 else dt*math.sin(z)/z
    decay=math.exp(-alpha*dt); cosine=math.cos(z)
    end_x=decay*(x*cosine+(v+alpha*x)*sinc)
    end_v=decay*(v*cosine-(alpha*v+k/m*x)*sinc)
    return {"x_m":end_x,"v_mps":end_v,"initial_energy_j":0.5*(k*x*x+m*v*v),
            "energy_j":0.5*(k*end_x*end_x+m*end_v*end_v)}

def evaluate(config):
    rows=[]; bad=0; balance=energy_excess=partition=0.0; saturated=0
    for m in config["masses"]:
        for ax in config["accel"]:
            for ay in config["accel"]:
                for aero in config["aero"]:
                    r=corner_loads(m,ax,ay,aero,0.46,0.43,0.33,3.2,1.45)
                    values=[r[k] for k in ("fl_n","fr_n","rl_n","rr_n")]
                    balance=max(balance,abs(sum(values)-r["total_n"]))
                    bad+=min(values)<0
                    saturated+=r["saturated"]
                    rows.append({"mass_kg":m,"ax_mps2":ax,"ay_mps2":ay,"aero_n":aero,**r})
    springs=0
    for damping in config["damping"]:
        for dt in config["steps"]:
            r=spring_step(150,30000,damping,0.02,0.1,dt)
            half=spring_step(150,30000,damping,0.02,0.1,dt/2)
            end=spring_step(150,30000,damping,half["x_m"],half["v_mps"],dt/2)
            energy_excess=max(energy_excess,max(0.0,r["energy_j"]-r["initial_energy_j"]))
            partition=max(partition,abs(r["x_m"]-end["x_m"]),abs(r["v_mps"]-end["v_mps"]))
            springs+=1
    return {"metrics":{"negative_loads":bad,"load_residual_n":balance,"energy_excess_j":energy_excess,"partition_error":partition,"missing_saturation_cases":int(saturated==0)},
            "observations":{"load_cases":len(rows),"spring_cases":springs,"saturated_cases":saturated,"rows":rows,
              "limitations":"Quasi-static proportional lateral split with explicit saturation; separate linear underdamped sprung-mass perturbation. No roll stiffness, unsprung mass, track input, bump stops or real suspension calibration."}}

def spec(c):
    return dict(hypothesis="Corner loads conserve total and remain nonnegative; saturation is explicit; unforced damped spring cannot gain energy.",
                sources=["REF-107","IDEA-006","IDEA-007","IDEA-008","IDEA-009"],
                config={"seed":42,"masses":[600,800],"accel":[-40,0,40],"aero":[0,3000],"damping":[0,1000,3000],"steps":[0,0.02,0.2,1]},
                criteria={"negative_loads":c("eq",0),"load_residual_n":c("le",1e-8,"N"),"energy_excess_j":c("le",1e-10,"J"),"partition_error":c("le",1e-10,"SI_component_max"),"missing_saturation_cases":c("eq",0)},evaluate=evaluate)
