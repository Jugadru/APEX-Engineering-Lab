"""Illustrative bounded behavioral profiles; cannot override feasibility gates."""
from . import registry as reg, racecraft_core as core, racecraft_attack as attack

PROFILES={
    "patient":dict(aggression=20,confidence=30,patience=90,composure=80),
    "balanced":dict(aggression=50,confidence=60,patience=50,composure=60),
    "assertive":dict(aggression=90,confidence=90,patience=10,composure=70)}

def budget(profile,context):
    reg.exact(profile,"aggression confidence patience composure")
    reg.exact(context,"wet_permille wear_permille pressure_permille")
    for k,v in profile.items(): core.integer(v,0,100,k)
    for k,v in context.items(): core.integer(v,0,1000,k)
    nominal=1500+25*profile["aggression"]+15*profile["confidence"]+5*(100-profile["patience"])
    penalty=2*context["wet_permille"]+context["wear_permille"]+context["pressure_permille"]*(100-profile["composure"])//100
    return max(500,min(6000,nominal-penalty))

def decide(snapshot,ident,profile,context):
    threshold=budget(profile,context)
    candidate=attack.opportunity(snapshot,ident)
    if candidate["action"]!="ATTACK_CANDIDATE":
        return {**candidate,"budget_ms":threshold,"feasibility":"VETOED","preference":"NOT_EVALUATED"}
    if candidate["eta_ms"]>threshold:
        return {**candidate,"action":"HOLD","reason":"PERSONALITY_PREFERENCE",
                "lateral_mm":snapshot.car(ident).lateral_mm,"budget_ms":threshold,
                "feasibility":"CANDIDATE_ONLY","preference":"DECLINED"}
    return {**candidate,"budget_ms":threshold,"feasibility":"CANDIDATE_ONLY","preference":"ACCEPTED"}

def context(wet=0,wear=0,pressure=0):
    return dict(wet_permille=wet,wear_permille=wear,pressure_permille=pressure)

def evaluate(config):
    rows=[]; invalid=monotonic=distinct=0; counts={k:0 for k in PROFILES}; blocked=0
    for gap in config["gaps_mm"]:
        for closing in config["closing_mm_s"]:
            for lane in ("free","blocked"):
                cars=[core.row(1,100000,0,40000+closing),core.row(2,100000+gap)]
                if lane=="blocked": cars.extend([core.row(3,100000,-3000),core.row(4,100000,3000)])
                s=attack.snap(cars); baseline=attack.opportunity(s,1)
                for wet in config["wet_permille"]:
                    decisions=[]
                    for name,profile in PROFILES.items():
                        ctx=context(wet,config["wear_permille"],config["pressure_permille"])
                        r=decide(s,1,profile,ctx); accept=r["action"]=="ATTACK_CANDIDATE"
                        decisions.append(accept); counts[name]+=accept
                        if baseline["action"]!="ATTACK_CANDIDATE":
                            invalid+=r["action"]!="HOLD" or r["reason"]!=baseline["reason"]
                            blocked+=1
                        if accept:
                            invalid+=r["lateral_mm"]!=baseline["lateral_mm"] or r["target_id"]!=baseline["target_id"] or r["eta_ms"]>r["budget_ms"]
                        dry=decide(s,1,profile,context(0,config["wear_permille"],config["pressure_permille"]))
                        monotonic+=r["budget_ms"]>dry["budget_ms"] or (accept and dry["action"]!="ATTACK_CANDIDATE")
                        rows.append(dict(profile=name,gap_mm=gap,closing_mm_s=closing,wet_permille=wet,lane_case=lane,**r))
                    distinct+=len(set(decisions))>1
    return {"metrics":{"invalid_decisions":invalid,"wet_monotonic_violations":monotonic,"missing_diversity":int(not distinct)},
            "observations":{"cases":len(rows),"attack_counts":counts,"distinct_decision_contexts":distinct,"hard_veto_cases":blocked,
                           "rows":rows,"limitations":"Artificial ordinal profiles and deterministic budget; not real driver psychology, calibrated probabilities, lap time, grip or rule adjudication."}}

def spec(c):
    return dict(hypothesis="Illustrative profiles can differ in acceptance but never override geometric feasibility; wet context never raises attack budget.",
        sources=["REF-105","IDEA-025","IDEA-035","IDEA-040"],
        config={"seed":42,"gaps_mm":[8000,20000,30000],"closing_mm_s":[3000,6000,12000],"wet_permille":[0,400,800],"wear_permille":200,"pressure_permille":300},
        criteria={"invalid_decisions":c("eq",0),"wet_monotonic_violations":c("eq",0),"missing_diversity":c("eq",0)},evaluate=evaluate)
