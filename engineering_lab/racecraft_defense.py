"""Independent defensive commitment memory; no reactive copying of rival goals."""
from . import registry as reg, racecraft_core as core, racecraft_space as space
RANGE=38000
CLEAR=space.BODY_MM+space.BUFFER_MM
RESET_TICKS=5

def decide(snapshot,ident,memory=None):
    a=space.Awareness(snapshot); own=a.own(ident)
    if memory is None:
        memory=dict(owner=ident,tick=snapshot.tick-1,target=None,aim_mm=own.lateral_mm,used=False,clear_ticks=0)
    reg.exact(memory,"owner tick target aim_mm used clear_ticks")
    reg.require(memory["owner"]==ident and type(memory["tick"]) is int and memory["tick"]+1==snapshot.tick,"defense owner/tick")
    reg.require(type(memory["used"]) is bool,"defense used")
    core.integer(memory["aim_mm"],-15000,15000,"aim")
    core.integer(memory["clear_ticks"],0,RESET_TICKS,"clear ticks")
    if memory["target"] is not None:
        core.integer(memory["target"],0,255,"target")
        reg.require(memory["target"]!=ident,"self target")
    reg.require(memory["used"]==(memory["target"] is not None),"commitment memory")
    near=a.nearby(ident,RANGE)
    rear=[o for o in near if -RANGE<=o["gap_mm"]<-CLEAR and o["closing_mm_s"]<-2000
          and a.cars[o["id"]].progress_mm-own.progress_mm==o["gap_mm"]]
    # Any nearby classified rival with overlapping longitudinal footprint
    # prevents a fresh defensive move, independent of its desired line.
    overlap=any(abs(o["gap_mm"])<=CLEAR for o in near)
    next_mem=dict(memory,tick=snapshot.tick)
    mode="HOLD"; aim=own.lateral_mm
    if memory["used"]:
        present=any(o["id"]==memory["target"] for o in near)
        count=0 if present or rear or overlap else min(RESET_TICKS,memory["clear_ticks"]+1)
        next_mem["clear_ticks"]=count
        if count>=RESET_TICKS:
            next_mem.update(target=None,aim_mm=own.lateral_mm,used=False,clear_ticks=0)
            mode="RELEASE"
        else:
            target=memory["aim_mm"]
            if abs(target)<=snapshot.half_width_mm and a.clearance(ident,target)["clear"]:
                aim=target; mode="COMMITTED"
            else: mode="SAFETY_HOLD"
    elif rear and not overlap:
        # Fixed side based solely on own line; not opponent's current/future aim.
        target=-2000 if own.lateral_mm<=0 else 2000
        if abs(target)<=snapshot.half_width_mm and a.clearance(ident,target)["clear"]:
            next_mem.update(target=rear[0]["id"],aim_mm=target,used=True,clear_ticks=0)
            aim=target; mode="COMMIT"
    return dict(mode=mode,aim_mm=aim,memory=next_mem)

def snap(tick,rival_lane=0,gap=-10000,block=False,width=5000):
    rows=[core.row(1,100000,0,40000),core.row(2,100000+gap,rival_lane,48000)]
    if block: rows.append(core.row(3,100000,-3000))
    return core.Snapshot.from_rows(tick,5000000,width,rows)

def evaluate(config):
    m=None; commits=releases=holds=changes=invalid=0; rows=[]; last=None
    for t in range(config["ticks"]):
        # First threat alternates observed lateral position. Temporary
        # obstruction must cause hold, never a switch to opposite lane.
        gap=-10000 if t<20 or t>=28 else -60000
        s=snap(t,(-1)**t*2500,gap,block=t in (5,6))
        r=decide(s,1,m)
        repeat=decide(core.Snapshot.from_rows(t,s.length_mm,s.half_width_mm,s.payload()["cars"][::-1]),1,m)
        invalid+=r!=repeat
        if r["mode"]=="COMMIT": commits+=1
        if r["mode"]=="RELEASE": releases+=1
        if r["mode"]=="SAFETY_HOLD": holds+=1
        if m and m["used"] and r["memory"]["used"]:
            changes+=r["memory"]["aim_mm"]!=m["aim_mm"]
        if r["mode"] in ("COMMIT","COMMITTED"):
            invalid+=not space.Awareness(s).clearance(1,r["aim_mm"])["clear"]
        if r["mode"]=="SAFETY_HOLD": invalid+=r["aim_mm"]!=s.car(1).lateral_mm
        m=r["memory"]; rows.append({"tick":t,"rival_lane_mm":s.car(2).lateral_mm,**r})
    return {"metrics":{"invalid_decisions":invalid,"commitment_switches":changes,
                       "commitment_count_error":abs(commits-2),"release_count_error":abs(releases-1),
                       "missing_safety_hold":int(not holds)},
            "observations":{"ticks":len(rows),"commitments":commits,"releases":releases,"safety_holds":holds,"rows":rows,
              "limitations":"Fixed own-side intent, frozen clearance, five-tick clear hysteresis; no steering motion, continuous collision or FIA defense adjudication."}}

def spec(c):
    return dict(hypothesis="Alternating rival positions and a temporary obstruction cannot flip a defensive commitment; reset only after clear hysteresis.",
        sources=["REF-105","IDEA-028","IDEA-029","IDEA-033","IDEA-034"],config={"seed":42,"ticks":40},
        criteria={"invalid_decisions":c("eq",0),"commitment_switches":c("eq",0),"commitment_count_error":c("eq",0),"release_count_error":c("eq",0),"missing_safety_hold":c("eq",0)},evaluate=evaluate)
