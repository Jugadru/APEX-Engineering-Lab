"""Bounded mass/grip/force interaction in a flat straight toy model."""
from . import registry as reg

def acceleration(mass_kg,mu,force_n,gravity_mps2=9.81):
    reg.require(all(reg.numeric(v) for v in (mass_kg,mu,force_n,gravity_mps2)) and mass_kg>0 and mu>=0 and force_n>=0 and gravity_mps2>0,"invalid sensitivity inputs")
    engine=force_n/mass_kg
    traction=mu*gravity_mps2
    return min(engine,traction),("traction" if traction<engine else "engine" if engine<traction else "equal")

def evaluate(config):
    masses=config["masses_kg"]; mus=config["grip"]; forces=config["forces_n"]; g=config["gravity_mps2"]
    table={}; rows=[]; regimes={"engine":0,"traction":0,"equal":0}; bad=mass_bad=grip_bad=0
    for f in forces:
        for m in masses:
            for mu in mus:
                a,regime=acceleration(m,mu,f,g)
                table[f,m,mu]=a; regimes[regime]+=1
                bad+=not (0<=a<=f/m and a<=mu*g)
                rows.append({"force_n":f,"mass_kg":m,"mu":mu,"acceleration_mps2":a,"regime":regime})
    mass_effect=[]; grip_effect=[]
    for f in forces:
        for mu in mus:
            for a,b in zip(masses,masses[1:]): mass_bad+=table[f,b,mu]>table[f,a,mu]
            mass_effect.append(table[f,masses[-1],mu]-table[f,masses[0],mu])
        for m in masses:
            for a,b in zip(mus,mus[1:]): grip_bad+=table[f,m,b]<table[f,m,a]
            grip_effect.append(table[f,m,mus[-1]]-table[f,m,mus[0]])
    return {"metrics":{"bound_violations":bad,"mass_monotonic_violations":mass_bad,"grip_monotonic_violations":grip_bad,
                       "missing_regimes":int(regimes["engine"]==0)+int(regimes["traction"]==0)},
            "observations":{"cases":len(rows),"regimes":regimes,"rows":rows,
                 "mass_effect_range_mps2":[min(mass_effect),max(mass_effect)],"grip_effect_range_mps2":[min(grip_effect),max(grip_effect)],
                 "limitations":"Deterministic grid, not statistical inference; flat straight, fixed friction coefficient, no aero, load transfer, tyre temperature or calibrated parameters."}}
