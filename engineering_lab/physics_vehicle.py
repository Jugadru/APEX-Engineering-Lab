"""Independent frozen-force forward step; composes the Physics Lab references."""
from . import registry as reg, physics_aero as aero, physics_powertrain as powertrain, physics_load as load, physics_tyre as tyre, physics_energy as energy
from .physics_core import scalar, step_force

DRY_MASS_KG=642.0
THERMAL_ETA=0.3
DRIVE_ETA=0.93
KERS_ETA=0.9

def step(state,command,dt_s):
    reg.exact(state,"speed_mps fuel_kg store_j lap_j prior_ax_mps2")
    reg.exact(command,"throttle brake gear cut_s kers_w ay_mps2 grip_factor tyre_temp_k wear drag_loss load_loss")
    v=scalar(state["speed_mps"],0,200,"speed")
    fuel=scalar(state["fuel_kg"],0,1000,"fuel")
    store=scalar(state["store_j"],0,10000000,"store")
    lap=scalar(state["lap_j"],0,energy.KERS_LAP_J,"lap")
    prior_ax=scalar(state["prior_ax_mps2"],-100,100,"prior_ax")
    dt=scalar(dt_s,0,0.5,"vehicle dt")
    throttle=scalar(command["throttle"],0,1,"throttle")
    brake=scalar(command["brake"],0,1,"brake")
    ay=scalar(command["ay_mps2"],-30,30,"lateral demand")
    grip=scalar(command["grip_factor"],0,1,"grip factor")
    requested_kers=scalar(command["kers_w"],0,energy.KERS_POWER_W,"KERS request")
    m=DRY_MASS_KG+fuel
    air=aero.forces(v,1.2,0.8,2.5,command["drag_loss"],command["load_loss"])
    loads=load.corner_loads(m,prior_ax,ay,air["downforce_n"],0.46,0.43,0.33,3.2,1.45)
    front=loads["fl_n"]+loads["fr_n"]; rear=loads["rl_n"]+loads["rr_n"]
    front_share=front/loads["total_n"]; rear_share=1-front_share
    mu=grip*tyre.effective_mu(1.5,command["tyre_temp_k"],360,45,command["wear"])
    pt=powertrain.output(v,command["gear"],0.33,0 if brake else throttle,DRIVE_ETA,dt,command["cut_s"])
    kers_request=requested_kers*pt["duty"] if not brake and throttle and pt["rpm"]<=powertrain.LIMIT_RPM and v else 0.0
    args=(fuel,store,lap,pt["crank_power_w"],kers_request,dt,THERMAL_ETA,DRIVE_ETA,KERS_ETA)
    offers=energy.offers(*args)
    available=offers["engine_wheel_offer_j"]+offers["kers_wheel_offer_j"]
    # No clutch/launch model. Force offers bounded by frozen initial-speed power.
    drive_offer=(min(pt["wheel_force_n"],offers["engine_wheel_offer_j"]/(v*dt))+
                 offers["kers_wheel_offer_j"]/(v*dt)) if v and dt and not brake else 0.0
    lat=m*ay
    if brake:
        f=tyre.combined(front,mu,mu,-12000*brake*front_share,lat*front_share)
        r=tyre.combined(rear,mu,mu,-12000*brake*rear_share,lat*rear_share)
        braking=-(f["fx_n"]+r["fx_n"]); drive=0.0
    else:
        f=tyre.combined(front,mu,mu,0,lat*front_share)
        r=tyre.combined(rear,mu,mu,drive_offer,lat*rear_share)
        braking=0.0; drive=r["fx_n"]
    drag=air["drag_n"]; rolling=150.0
    def motion(force):
        return step_force(m,v,force-braking-drag-rolling,dt)
    trial=motion(drive)
    constrained=drive*trial["distance_m"]>available
    if constrained:
        # Work is monotone in nonnegative drive force for fixed resistance and dt.
        # Lower endpoint remains feasible; never increase force after the solve.
        lo,hi=0.0,drive
        for _ in range(48):
            mid=(lo+hi)*0.5
            if mid*motion(mid)["distance_m"]<=available: lo=mid
            else: hi=mid
        drive=lo
        trial=motion(drive)
    distance=trial["distance_m"]; drive_work=drive*distance
    ledger=energy.settle(*args,drive_work)
    # Only longitudinal work; lateral demand is reported, not integrated as motion.
    net_work=drive_work-(braking+drag+rolling)*distance
    next_state={"speed_mps":trial["speed_mps"],"fuel_kg":ledger["fuel_remaining_kg"],
                "store_j":ledger["store_remaining_j"],"lap_j":ledger["lap_remaining_j"],
                "prior_ax_mps2":(trial["speed_mps"]-v)/dt if dt else prior_ax}
    return {"state":next_state,"distance_m":distance,"mass_kg":m,"drive_n":drive,"brake_n":braking,"drag_n":drag,"rolling_n":rolling,
            "drive_work_j":drive_work,"brake_work_j":braking*distance,"drag_work_j":drag*distance,"rolling_work_j":rolling*distance,
            "delta_kinetic_j":trial["delta_kinetic_j"],"accepted_wheel_j":ledger["accepted_wheel_j"],"available_wheel_j":available,
            "energy_residual_j":abs(ledger["accepted_wheel_j"]-drive_work),
            "relative_work_error":abs(trial["delta_kinetic_j"]-net_work)/max(1,abs(net_work),abs(trial["delta_kinetic_j"])),
            "fuel_burn_kg":ledger["fuel_burn_kg"],"kers_used_j":ledger["kers_used_j"],"energy_constrained":constrained,
            "max_grip_utilization":max(f["utilization"],r["utilization"]),"lateral_force_n":f["fy_n"]+r["fy_n"],
            "lateral_unmet_n":abs(lat-f["fy_n"]-r["fy_n"]),"load_saturated":loads["saturated"]}

def initial(speed=30,fuel=5,store=400000,lap=400000):
    return {"speed_mps":speed,"fuel_kg":fuel,"store_j":store,"lap_j":lap,"prior_ax_mps2":0}

def control(**updates):
    return {"throttle":0,"brake":0,"gear":5,"cut_s":0,"kers_w":0,"ay_mps2":0,
            "grip_factor":1,"tyre_temp_k":360,"wear":0,"drag_loss":0,"load_loss":0,**updates}

def evaluate(config):
    rows=[]; bad=0; work_error=energy_error=mass_error=grip_error=0.0; capped=driven=braked=0
    for v in config["speeds"]:
        for fuel,store,lap in config["energy"]:
            for name,cmd in config["commands"].items():
                for grip in config["grip"]:
                    for dt in config["steps"]:
                        before=initial(v,fuel,store,lap)
                        after=step(before,control(**cmd,grip_factor=grip),dt)
                        ns=after["state"]
                        work_error=max(work_error,after["relative_work_error"])
                        energy_error=max(energy_error,after["energy_residual_j"])
                        mass_error=max(mass_error,abs(fuel-ns["fuel_kg"]-after["fuel_burn_kg"]))
                        grip_error=max(grip_error,max(0,after["max_grip_utilization"]-1))
                        bad+=not (ns["speed_mps"]>=0 and after["distance_m"]>=0 and 0<=ns["fuel_kg"]<=fuel and
                                  0<=ns["store_j"]<=store and 0<=ns["lap_j"]<=lap and
                                  after["drive_work_j"]<=after["available_wheel_j"]+1e-8 and
                                  (after["drive_n"]==0 or after["brake_n"]==0))
                        if cmd.get("brake",0): bad+=after["drive_n"]!=0
                        if name=="coast": bad+=ns["speed_mps"]>v
                        if dt==0: bad+=ns!=before or after["distance_m"]!=0
                        capped+=after["energy_constrained"]; driven+=after["drive_work_j"]>0; braked+=after["brake_work_j"]>0
                        rows.append({"command":name,"initial_mps":v,"initial_fuel_kg":fuel,"initial_store_j":store,
                                     "initial_lap_j":lap,"grip_factor":grip,"dt_s":dt,**after})
    return {"metrics":{"invalid_states":bad,"relative_work_error":work_error,"energy_residual_j":energy_error,
                       "fuel_residual_kg":mass_error,"grip_excess":grip_error,
                       "missing_operating_modes":int(not capped)+int(not driven)+int(not braked)},
            "observations":{"cases":len(rows),"energy_constrained_cases":capped,"drive_work_cases":driven,"brake_work_cases":braked,"rows":rows,
              "limitations":"Frozen-force forward-only reference; prescribed lateral demand, grip and temperature; mass frozen during tick. No clutch, actual steering, tyre state evolution, suspension motion, pit/strategy, traffic or real calibration."}}

def spec(c):
    return dict(hypothesis="Composed forward step preserves work-energy, grip and source limits, braking precedence and dt-zero state.",
        sources=["REF-107","IDEA-001","IDEA-005","IDEA-008","IDEA-010","IDEA-011","IDEA-015"],
        config={"seed":42,"speeds":[0,30,70],"energy":[[0,0,0],[0.001,1000,1000],[5,400000,400000]],
                "commands":{"coast":{},"drive":{"throttle":1,"kers_w":60000},"brake":{"brake":1,"ay_mps2":5},
                            "overlap":{"brake":0.5,"throttle":1,"kers_w":60000},"cut":{"throttle":1,"cut_s":0.2,"kers_w":60000}},
                "grip":[0.5,1],"steps":[0,0.2]},
        criteria={"invalid_states":c("eq",0),"relative_work_error":c("le",1e-10,"ratio"),
                  "energy_residual_j":c("le",1e-7,"J"),"fuel_residual_kg":c("le",1e-12,"kg"),
                  "grip_excess":c("le",1e-12,"ratio"),"missing_operating_modes":c("eq",0)},evaluate=evaluate)
