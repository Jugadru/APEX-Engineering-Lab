"""Causal attack opportunity and observed crossing; no sporting pass award."""
from . import registry as reg, racecraft_core as core, racecraft_space as space

CLEAR=space.BODY_MM+space.BUFFER_MM
SIDE=space.WIDTH_MM+space.BUFFER_MM
RANGE=38000

def opportunity(snapshot,ident):
    awareness=space.Awareness(snapshot); a=awareness.own(ident)
    def hold(reason,target=None):
        return dict(action="HOLD",reason=reason,target_id=target,lateral_mm=a.lateral_mm,eta_ms=None)
    front=awareness.leaders(ident,RANGE)["front"]
    if not front: return hold("NO_LEADER")
    b=awareness.cars[front["id"]]
    gap=front["gap_mm"]; closing=front["closing_mm_s"]
    if b.progress_mm-a.progress_mm!=gap: return hold("NOT_CLASSIFIED_RIVAL",b.id)
    if gap<=CLEAR: return hold("GAP_TOO_SMALL",b.id)
    if closing<2000: return hold("INSUFFICIENT_CLOSING",b.id)
    eta=((gap+CLEAR)*1000+closing-1)//closing
    if eta>6000: return hold("HORIZON_TOO_LONG",b.id)
    candidates=[]
    for offset in (-3000,3000):
        if abs(offset-b.lateral_mm)<=SIDE or abs(offset)>snapshot.half_width_mm: continue
        if not awareness.clearance(ident,offset)["clear"]: continue
        # Frozen destination corridor; veto close and closing traffic, not a time-sweep guarantee.
        conflict=False
        for o in awareness.nearby(ident,RANGE):
            other=awareness.cars[o["id"]]
            if abs(other.lateral_mm-offset)>SIDE: continue
            g=o["gap_mm"]; rel=o["closing_mm_s"]
            if abs(g)<=CLEAR or (g>0 and rel>0 and (g-CLEAR)*1000<=rel*eta) or (g<0 and rel<0 and (-g-CLEAR)*1000<=-rel*eta):
                conflict=True; break
        if not conflict: candidates.append(offset)
    if not candidates: return hold("NO_CLEAR_CORRIDOR",b.id)
    target=min(candidates,key=lambda x:(abs(x-a.lateral_mm),x))
    return dict(action="ATTACK_CANDIDATE",reason="FROZEN_FEASIBILITY",target_id=b.id,lateral_mm=target,eta_ms=eta)

def observed_crossing(samples,attacker,target):
    reg.require(attacker!=target and isinstance(samples,(tuple,list)) and 2<=len(samples)<=32,"crossing sequence")
    first=samples[0]; last=samples[-1]
    a=first.car(attacker); b=first.car(target)
    start=b.progress_mm-a.progress_mm
    if not (a.active and b.active and CLEAR<=start<=RANGE and core.signed_gap(a.progress_mm,b.progress_mm,first.length_mm)==start):
        return False
    prior_a,prior_b=a,b; crossed=False
    for i,s in enumerate(samples[1:],1):
        reg.require(s.tick==first.tick+i and s.length_mm==first.length_mm and s.half_width_mm==first.half_width_mm,"nonconsecutive or changed geometry")
        a=s.car(attacker); b=s.car(target)
        if not a.active or not b.active: return False
        if not (0<=a.progress_mm-prior_a.progress_mm<=100000 and 0<=b.progress_mm-prior_b.progress_mm<=100000):
            return False
        old=prior_a.progress_mm-prior_b.progress_mm; new=a.progress_mm-b.progress_mm
        if old<=0<new:
            if min(abs(prior_a.lateral_mm-prior_b.lateral_mm),abs(a.lateral_mm-b.lateral_mm))<=SIDE: return False
            crossed=True
        prior_a,prior_b=a,b
    return crossed and a.progress_mm-b.progress_mm>=CLEAR

def snap(rows,tick=0,width=5000):
    return core.Snapshot.from_rows(tick,5000000,width,rows)

def evaluate(config):
    rows=[]; invalid=0; attacks=holds=0
    for gap in config["gaps_mm"]:
        for closing in config["closing_mm_s"]:
            for lane in config["lane_cases"]:
                rs=[core.row(1,100000,0,40000+closing),core.row(2,100000+gap,0,40000)]
                if lane=="left": rs.append(core.row(3,100000,-3000,40000))
                if lane=="both": rs.extend([core.row(3,100000,-3000),core.row(4,100000,3000)])
                s=snap(rs); r=opportunity(s,1)
                invalid+=r!=opportunity(snap(rs[::-1]),1)
                if r["action"]=="ATTACK_CANDIDATE":
                    attacks+=1
                    invalid+=not (gap>CLEAR and closing>=2000 and r["eta_ms"]<=6000 and space.Awareness(s).clearance(1,r["lateral_mm"])["clear"])
                else: holds+=1
                if lane=="both": invalid+=r["action"]!="HOLD"
                rows.append(dict(gap_mm=gap,closing_mm_s=closing,lane_case=lane,**r))
    def sequence(lane,active=True,teleport=False):
        return [snap([core.row(1,100000,lane),core.row(2,110000)],0),
                snap([core.row(1,120000,lane),core.row(2,120000)],1),
                snap([core.row(1,250000 if teleport else 140000,lane,active=active),core.row(2,132000)],2)]
    outcomes=[observed_crossing(sequence(-3000),1,2),observed_crossing(sequence(0),1,2),
              observed_crossing(sequence(-3000,False),1,2),observed_crossing(sequence(-3000,teleport=True),1,2)]
    return {"metrics":{"invalid_decisions":invalid,"crossing_mismatches":sum(a!=b for a,b in zip(outcomes,[True,False,False,False])),
                       "missing_decision_modes":int(not attacks)+int(not holds)},
            "observations":{"cases":len(rows),"attack_candidates":attacks,"holds":holds,"crossing_cases":len(outcomes),"rows":rows,
             "limitations":"Frozen straight-line estimates and classified crossing on supplied consecutive samples, no continuous collision proof, actual sporting award, real opponent action or calibration."}}

def spec(c):
    return dict(hypothesis="Attack candidates require observed closing and a frozen clear corridor; only observed classified crossing with clearance can be confirmed.",
        sources=["REF-105","IDEA-024","IDEA-025","IDEA-026","IDEA-033","IDEA-040"],
        config={"seed":42,"gaps_mm":[5000,8000,20000,38000],"closing_mm_s":[0,2000,6000,12000],"lane_cases":["free","left","both"]},
        criteria={"invalid_decisions":c("eq",0),"crossing_mismatches":c("eq",0),"missing_decision_modes":c("eq",0)},evaluate=evaluate)
