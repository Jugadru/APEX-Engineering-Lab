"""Independent synthetic combined friction, lumped thermal and wear references."""
import math
from .physics_core import scalar

def combined(normal_n,mu_x,mu_y,fx_request_n,fy_request_n):
    n=scalar(normal_n,0,100000,"normal_n")
    xcap=n*scalar(mu_x,0,5,"mu_x"); ycap=n*scalar(mu_y,0,5,"mu_y")
    fx=scalar(fx_request_n,-1000000,1000000,"fx_request_n")
    fy=scalar(fy_request_n,-1000000,1000000,"fy_request_n")
    # Zero capacity means that component is impossible, not an infinite norm.
    fx=fx if xcap else 0.0; fy=fy if ycap else 0.0
    utilization=math.hypot(fx/xcap if xcap else 0,fy/ycap if ycap else 0)
    scale=1/max(1.0,utilization)
    fx*=scale; fy*=scale
    return {"fx_n":fx,"fy_n":fy,"utilization":math.hypot(fx/xcap if xcap else 0,fy/ycap if ycap else 0)}

def thermal_step(temp_k,ambient_k,heat_w,capacity_j_per_k,cooling_w_per_k,dt_s):
    t=scalar(temp_k,1,2000,"temp_k"); ambient=scalar(ambient_k,1,2000,"ambient_k")
    q=scalar(heat_w,0,100000,"heat_w"); c=scalar(capacity_j_per_k,1,1000000,"capacity")
    h=scalar(cooling_w_per_k,0,10000,"cooling"); dt=scalar(dt_s,0,10,"dt_s")
    # Exact solution of C*dT/dt=Q-h*(T-Ta); stable near zero h.
    z=h*dt/c
    phi=-math.expm1(-z)/z if z else 1.0
    end=t+(q-h*(t-ambient))*dt/c*phi
    # A reference outside the declared temperature domain cannot be chained.
    # Reject instead of clipping temperature and concealing energy imbalance.
    return scalar(end,1,2000,"result temperature outside model domain (K)")

def wear_step(wear,slip_work_j,wear_energy_j):
    w=scalar(wear,0,1,"wear")
    q=scalar(slip_work_j,0,1e8,"slip_work_j")
    cap=scalar(wear_energy_j,1,1e10,"wear_energy_j")
    return min(1.0,w+q/cap)

def effective_mu(peak,temp_k,optimum_k,width_k,wear):
    p=scalar(peak,0,5,"peak_mu")
    t=scalar(temp_k,1,2000,"temp_k"); opt=scalar(optimum_k,1,2000,"optimum_k")
    w=scalar(width_k,1,1000,"width_k"); worn=scalar(wear,0,1,"wear")
    return p*math.exp(-((t-opt)/w)**2)*(1-0.5*worn)

def evaluate(config):
    rows=[]; ellipse_error=thermal_error=0.0; invalid=wear_bad=0
    for n in config["loads_n"]:
        for mu in config["mu"]:
            for fx,fy in config["requests_n"]:
                r=combined(n,mu,mu,fx,fy)
                ellipse_error=max(ellipse_error,max(0.0,r["utilization"]-1))
                invalid+=not (abs(r["fx_n"])<=abs(fx)+1e-10 and abs(r["fy_n"])<=abs(fy)+1e-10 and
                              r["fx_n"]*fx>=0 and r["fy_n"]*fy>=0)
                rows.append({"load_n":n,"mu":mu,"request_x_n":fx,"request_y_n":fy,**r})
    thermal_cases=0
    for t in config["temps_k"]:
        for q in config["heat_w"]:
            for h in config["cooling_w_per_k"]:
                a=thermal_step(t,300,q,1000,h,2)
                b=thermal_step(thermal_step(t,300,q,1000,h,1),300,q,1000,h,1)
                thermal_error=max(thermal_error,abs(a-b))
                invalid+=not math.isfinite(a) or a<=0
                thermal_cases+=1
    wear_cases=0
    for w in (0,0.5,1):
        for energy in (0,1000,1000000):
            new=wear_step(w,energy,10000)
            wear_bad+=not w<=new<=1
            wear_bad+=effective_mu(1.5,360,360,30,new)>effective_mu(1.5,360,360,30,w)
            wear_cases+=1
    return {"metrics":{"ellipse_excess":ellipse_error,"thermal_partition_error_k":thermal_error,
                       "invalid_states":invalid,"wear_violations":wear_bad},
            "observations":{"grip_cases":len(rows),"thermal_cases":thermal_cases,"wear_cases":wear_cases,"rows":rows,
                            "limitations":"Synthetic radial force projection; one thermal node, monotonic energy-proxy wear; no slip curve, pressure, grain/blister, compound data or tyre calibration."}}

def spec(c):
    return dict(hypothesis="Combined force stays inside friction ellipse; exact thermal step partitions consistently and wear never recovers.",
                sources=["REF-107","IDEA-015","IDEA-016","IDEA-017"],
                config={"seed":42,"loads_n":[0,2000,4000],"mu":[0,0.6,1.5],"requests_n":[[0,0],[4000,0],[0,-4000],[3000,3000],[-3000,2000]],"temps_k":[280,300,380],"heat_w":[0,4000],"cooling_w_per_k":[0,0.000001,80]},
                criteria={"ellipse_excess":c("le",1e-12,"ratio"),"thermal_partition_error_k":c("le",1e-10,"K"),"invalid_states":c("eq",0),"wear_violations":c("eq",0)},evaluate=evaluate)
