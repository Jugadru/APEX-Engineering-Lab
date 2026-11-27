"""Rigid-gear SI powertrain reference. Artificial V8-shaped curve; no clutch/shift controller."""
import math
from . import registry as reg
from .physics_core import scalar

RATIOS=(17.0,13.0,10.8,9.2,8.0,7.0,6.0)
CURVE=((0,0),(6000,200),(10000,280),(14000,320),(18000,290))
LIMIT_RPM=18000

def torque_nm(rpm):
    r=scalar(rpm,0,10000000,"rpm")
    if r>LIMIT_RPM: return 0.0
    for (a,x),(b,y) in zip(CURVE,CURVE[1:]):
        if r<=b: return x+(y-x)*(r-a)/(b-a)
    return float(CURVE[-1][1])

def output(speed_mps,gear,radius_m,throttle,efficiency,dt_s,cut_s=0):
    v=scalar(speed_mps,0,200,"speed_mps")
    reg.require(type(gear) is int and 1<=gear<=len(RATIOS),"invalid gear")
    radius=scalar(radius_m,0.1,1,"wheel radius")
    pedal=scalar(throttle,0,1,"throttle"); eta=scalar(efficiency,0,1,"efficiency")
    dt=scalar(dt_s,0,10,"dt_s"); cut=scalar(cut_s,0,10,"cut_s")
    ratio=RATIOS[gear-1]
    omega=v/radius*ratio; rpm=omega*60/(2*math.pi)
    torque=torque_nm(rpm)*pedal
    duty=max(0.0,dt-cut)/dt if dt else 0.0
    crank_power=torque*omega*duty
    force=torque*ratio/radius*eta*duty
    return {"rpm":rpm,"torque_nm":torque,"duty":duty,"crank_power_w":crank_power,
            "wheel_force_n":force,"wheel_power_w":force*v,"transmission_efficiency":eta}

def evaluate(config):
    rows=[]; err=0.0; invalid=0; limited=0
    for gear in range(1,8):
        for v in config["speeds"]:
            for throttle in config["throttles"]:
                for cut in config["cuts_s"]:
                    r=output(v,gear,config["radius_m"],throttle,config["efficiency"],config["dt_s"],cut)
                    expected=r["crank_power_w"]*config["efficiency"]
                    err=max(err,abs(r["wheel_power_w"]-expected)/max(1,expected))
                    invalid+=not (0<=r["duty"]<=1 and r["wheel_force_n"]>=0 and r["wheel_power_w"]>=0)
                    if r["rpm"]>LIMIT_RPM:
                        limited+=1; invalid+=r["wheel_force_n"]!=0
                    if cut>=config["dt_s"] or not throttle: invalid+=r["wheel_power_w"]!=0
                    rows.append({"gear":gear,"speed_mps":v,"throttle":throttle,"cut_s":cut,**r})
    return {"metrics":{"relative_power_error":err,"invalid_states":invalid,"missing_limiter_cases":int(limited==0)},
            "observations":{"cases":len(rows),"limiter_cases":limited,"rows":rows,
                            "limitations":"Artificial seven-ratio rigid gear, zero launch torque at zero speed, prescribed shift cut; no clutch, wheel slip, gear controller, transient engine or calibration."}}

def spec(c):
    return dict(hypothesis="Rigid gear wheel power matches crank power times efficiency; cut, throttle zero and overspeed cannot supply drive.",
                sources=["REF-107","IDEA-001","IDEA-002","IDEA-003","IDEA-004"],
                config={"seed":42,"speeds":[0,20,40,60,100],"throttles":[0,1],"cuts_s":[0,0.06,0.2],"radius_m":0.33,"efficiency":0.93,"dt_s":0.2},
                criteria={"relative_power_error":c("le",1e-12,"ratio"),"invalid_states":c("eq",0),"missing_limiter_cases":c("eq",0)},evaluate=evaluate)
