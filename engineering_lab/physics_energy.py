"""Synthetic fuel/energy offers and single-debit accepted work, all in SI."""
from .physics_core import scalar

LHV_J_KG=43000000.0
KERS_POWER_W=60000.0
KERS_LAP_J=400000.0

def offers(fuel_kg,store_j,lap_j,engine_shaft_w,kers_request_w,dt_s,thermal_eta,drive_eta,kers_eta):
    fuel=scalar(fuel_kg,0,1000,"fuel")
    store=scalar(store_j,0,10000000,"store"); lap=scalar(lap_j,0,KERS_LAP_J,"lap budget")
    power=scalar(engine_shaft_w,0,2000000,"engine shaft power"); request=scalar(kers_request_w,0,2000000,"KERS request")
    dt=scalar(dt_s,0,10,"dt")
    th=scalar(thermal_eta,0.01,1,"thermal efficiency"); de=scalar(drive_eta,0.01,1,"drive efficiency"); ke=scalar(kers_eta,0.01,1,"KERS efficiency")
    shaft=min(power*dt,fuel*LHV_J_KG*th)
    electric=min(request,KERS_POWER_W)*dt
    source=min(electric,store,lap)
    return {"engine_wheel_offer_j":shaft*de,"kers_wheel_offer_j":source*ke,
            "engine_shaft_offer_j":shaft,"kers_source_offer_j":source}

def settle(fuel_kg,store_j,lap_j,engine_shaft_w,kers_request_w,dt_s,thermal_eta,drive_eta,kers_eta,demand_wheel_j):
    offer=offers(fuel_kg,store_j,lap_j,engine_shaft_w,kers_request_w,dt_s,thermal_eta,drive_eta,kers_eta)
    demand=scalar(demand_wheel_j,0,100000000,"wheel work demand")
    # Explicit policy: consume accepted KERS offer first; no debit for unused offer.
    kers_wheel=min(demand,offer["kers_wheel_offer_j"])
    engine_wheel=min(demand-kers_wheel,offer["engine_wheel_offer_j"])
    source=min(offer["kers_source_offer_j"],kers_wheel/kers_eta)
    burn=min(fuel_kg,engine_wheel/(drive_eta*thermal_eta*LHV_J_KG))
    # Recalculate delivery from actual bounded debits, not from requested energy.
    accepted=source*kers_eta+burn*LHV_J_KG*thermal_eta*drive_eta
    return {**offer,"fuel_burn_kg":burn,"fuel_remaining_kg":fuel_kg-burn,
            "kers_used_j":source,"store_remaining_j":store_j-source,"lap_remaining_j":lap_j-source,
            "accepted_wheel_j":accepted,"unmet_wheel_j":max(0.0,demand-accepted),
            "source_conversion_loss_j":burn*LHV_J_KG*(1-thermal_eta*drive_eta)+source*(1-kers_eta)}

def evaluate(config):
    rows=[]; bad=0; max_mass=max_energy=max_demand=0.0; constrained=0
    for fuel in config["fuel_kg"]:
        for store in config["store_j"]:
            for lap in config["lap_j"]:
                for demand in config["demand_j"]:
                    for dt in config["dt_s"]:
                        r=settle(fuel,store,lap,500000,100000,dt,0.3,0.93,0.9,demand)
                        bad+=not (0<=r["fuel_burn_kg"]<=fuel and 0<=r["kers_used_j"]<=min(store,lap,KERS_POWER_W*dt)
                                  and r["fuel_remaining_kg"]>=0 and r["store_remaining_j"]>=0 and r["lap_remaining_j"]>=0)
                        constrained+=r["unmet_wheel_j"]>1e-8
                        max_mass=max(max_mass,abs(fuel-r["fuel_remaining_kg"]-r["fuel_burn_kg"]))
                        input_energy=r["fuel_burn_kg"]*LHV_J_KG+r["kers_used_j"]
                        max_energy=max(max_energy,abs(input_energy-r["accepted_wheel_j"]-r["source_conversion_loss_j"])/max(1,input_energy))
                        max_demand=max(max_demand,abs(demand-r["accepted_wheel_j"]-r["unmet_wheel_j"]))
                        rows.append({"initial_fuel_kg":fuel,"initial_store_j":store,"initial_lap_j":lap,"demand_j":demand,"dt_s":dt,**r})
    return {"metrics":{"invalid_states":bad,"mass_error_kg":max_mass,"relative_energy_error":max_energy,"demand_error_j":max_demand,"missing_constrained_cases":int(constrained==0)},
            "observations":{"cases":len(rows),"constrained_cases":constrained,"rows":rows,
                 "limitations":"Synthetic 43 MJ/kg and fixed efficiencies, source-side 60 kW/400 kJ reference limits from existing APEX era model, accepted KERS-first allocation. No idle burn, recharge, refuelling, lap reset or actual 2012 calibration."}}

def spec(c):
    return dict(hypothesis="Accepted wheel work cannot exceed offers, fuel and KERS are debited once and energy conversion losses balance.",
                sources=["REF-107","IDEA-001","IDEA-002","IDEA-005"],config={"seed":42,"fuel_kg":[0,0.001,2],"store_j":[0,1000,500000],"lap_j":[0,5000,400000],"demand_j":[0,5000,200000],"dt_s":[0,0.2]},
                criteria={"invalid_states":c("eq",0),"mass_error_kg":c("le",1e-12,"kg"),"relative_energy_error":c("le",1e-12,"ratio"),"demand_error_j":c("le",1e-8,"J"),"missing_constrained_cases":c("eq",0)},evaluate=evaluate)
