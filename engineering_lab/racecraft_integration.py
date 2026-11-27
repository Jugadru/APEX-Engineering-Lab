"""Compose frozen tactical proposals; never apply endpoints to sporting state."""
from . import registry as reg, racecraft_core as core, racecraft_space as space
from . import racecraft_attack as attack, racecraft_defense as defense, racecraft_personality as personality
from . import racecraft_agents as agents, racecraft_collision as collision

LATCH_TICKS=6
COOLDOWN=5
STEP_MM=500

def approach(value,target):
    return value+max(-STEP_MM,min(STEP_MM,target-value))

def attack_memory(snapshot,own,prior):
    if prior is None:
        return dict(owner=own.id,tick=snapshot.tick,target=None,aim_mm=own.lateral_mm,until=0,cooldown=0)
    reg.exact(prior,"owner tick target aim_mm until cooldown")
    reg.require(type(prior["owner"]) is int and prior["owner"]==own.id and type(prior["tick"]) is int
                and prior["tick"]+1==snapshot.tick,"attack memory binding")
    core.integer(prior["aim_mm"],-15000,15000,"attack aim")
    core.integer(prior["until"],0,1000000+LATCH_TICKS,"attack expiry")
    core.integer(prior["cooldown"],0,1000000+COOLDOWN,"attack cooldown")
    if prior["target"] is not None:
        core.integer(prior["target"],0,255,"attack target")
        reg.require(prior["target"]!=own.id,"self target")
    return dict(prior,tick=snapshot.tick)

def release(m,own,tick):
    m.update(target=None,aim_mm=own.lateral_mm,until=0,cooldown=tick+COOLDOWN)

def plan(snapshot,profiles,contexts,memories=None):
    a=space.Awareness(snapshot)
    ids=tuple(a.cars)
    reg.require(isinstance(profiles,dict) and isinstance(contexts,dict) and set(profiles)==set(contexts)==set(ids),"profile/context roster")
    memories={} if memories is None else memories
    reg.require(isinstance(memories,dict) and set(memories)<=set(ids),"memory roster")
    proposals={}; next_mem={}; decisions=[]
    for ident in ids:
        own=a.cars[ident]; prior=memories.get(ident)
        if prior is not None: reg.exact(prior,"attack defense")
        d=defense.decide(snapshot,ident,prior["defense"] if prior else None)
        m=attack_memory(snapshot,own,prior["attack"] if prior else None)
        p=personality.decide(snapshot,ident,profiles[ident],contexts[ident])
        aim=own.lateral_mm; mode="HOLD"; reason=p["reason"]
        if d["mode"] in ("COMMIT","COMMITTED","SAFETY_HOLD","RELEASE"):
            if m["target"] is not None: release(m,own,snapshot.tick)
            aim=d["aim_mm"]; mode="DEFENSE"; reason=d["mode"]
        elif m["target"] is not None:
            target=a.cars.get(m["target"])
            gap=core.signed_gap(own.progress_mm,target.progress_mm,snapshot.length_mm) if target else None
            if target is None or snapshot.tick>=m["until"] or gap < -attack.CLEAR or abs(gap)>attack.RANGE:
                release(m,own,snapshot.tick); reason="ATTACK_RELEASE"
            elif abs(m["aim_mm"])<=snapshot.half_width_mm and a.clearance(ident,m["aim_mm"])["clear"]:
                aim=m["aim_mm"]; mode="ATTACK"; reason="COMMITTED"
            else: mode="ATTACK_HOLD"; reason="SAFETY_VETO"
        elif snapshot.tick>=m["cooldown"] and p["action"]=="ATTACK_CANDIDATE":
            m.update(target=p["target_id"],aim_mm=p["lateral_mm"],until=snapshot.tick+LATCH_TICKS)
            aim=p["lateral_mm"]; mode="ATTACK"; reason="NEW_COMMITMENT"
        # Guard even previously committed aims after narrowing.
        if abs(aim)>snapshot.half_width_mm or not a.clearance(ident,aim)["clear"]:
            aim=own.lateral_mm
            if mode=="ATTACK": mode="ATTACK_HOLD"
            reason="STATIC_VETO"
        lateral=approach(own.lateral_mm,aim)
        # Artificial constant observed-speed advance at 0.2 s; no acceleration or application.
        x=min(2000000000,own.progress_mm+own.speed_mm_s//5)
        proposals[ident]=collision.endpoint(x,lateral)
        next_mem[ident]={"attack":m,"defense":d["memory"]}
        decisions.append(dict(id=ident,mode=mode,reason=reason,aim_mm=aim,
                              attack_target=m["target"],attack_locked_aim_mm=m["aim_mm"],defense_mode=d["mode"],
                              preference=p["preference"]))
    feasibility=agents.resolve(snapshot,proposals)
    return {"tick":snapshot.tick,"decisions":decisions,"proposals":[dict(id=i,**proposals[i]) for i in ids],
            "memory":next_mem,"feasibility":feasibility,"meaning":"DIAGNOSTIC_ONLY_NOT_A_MOTION_COMMAND"}

def scripted(tick,blocked=False,n=24):
    rs=[core.row(1,100000,0,50000),core.row(2,112000,0,40000),
        core.row(3,100000 if blocked else 180000,-3000,40000)]
    rs.extend(core.row(i,300000+i*100000,(-1)**i*2500,40000) for i in range(4,n+1))
    return core.Snapshot.from_rows(tick,5000000,5000,rs)

def inputs(s):
    profiles={c.id:dict(personality.PROFILES["assertive" if c.id==1 else "balanced"]) for c in s.cars if c.active}
    contexts={i:personality.context() for i in profiles}
    return profiles,contexts

def evaluate(config):
    memory=None; invalid=repeat_bad=lock_switches=0; modes={}; rows=[]
    for t in range(config["ticks"]):
        s=scripted(t,blocked=t in (2,3,8))
        profiles,contexts=inputs(s)
        prior_hash=reg.digest(memory) if memory is not None else None
        x=plan(s,profiles,contexts,memory)
        alt=plan(core.Snapshot.from_rows(t,s.length_mm,s.half_width_mm,s.payload()["cars"][::-1]),
                 dict(reversed(list(profiles.items()))),dict(reversed(list(contexts.items()))),memory)
        repeat_bad+=x!=alt
        invalid+=prior_hash!=(reg.digest(memory) if memory is not None else None)
        invalid+=bool(x["feasibility"]["new_contacts"])
        for r,p in zip(x["decisions"],x["proposals"]):
            i=r["id"]; own=s.car(i)
            modes[r["mode"]]=modes.get(r["mode"],0)+1
            invalid+=abs(p["lateral_mm"]-own.lateral_mm)>STEP_MM or p["progress_mm"]<own.progress_mm
            if r["defense_mode"] in ("COMMIT","COMMITTED","SAFETY_HOLD","RELEASE"):
                invalid+=r["mode"]!="DEFENSE"
            if memory and memory[i]["attack"]["target"] is not None and x["memory"][i]["attack"]["target"] is not None:
                old=memory[i]["attack"]; new=x["memory"][i]["attack"]
                lock_switches+=old["target"]!=new["target"] or old["aim_mm"]!=new["aim_mm"]
        memory=x["memory"]
        rows.append({"tick":t,"decisions_sha256":reg.digest(x["decisions"]),"result_sha256":reg.digest(x),
                     "vetoed":len(x["feasibility"]["vetoed_ids"]),"lead_decision":x["decisions"][0]})
    return {"metrics":{"invalid_proposals":invalid,"permutation_mismatches":repeat_bad,"lock_switches":lock_switches,
                       "missing_modes":sum(modes.get(k,0)==0 for k in ("ATTACK","DEFENSE","ATTACK_HOLD","HOLD"))},
            "observations":{"ticks":len(rows),"decisions":len(rows)*24,"modes":modes,"rows":rows,
                            "limitations":"Scripted observations only, no application of geometric endpoints, 0.2 s constant-speed proposals and 500 mm lateral step are artificial. No game motion or race result."}}

def spec(c):
    return dict(hypothesis="Composed tactical proposals preserve defense precedence, fixed attack commitment and geometric veto under reordered snapshots.",
        sources=["REF-105","IDEA-024","IDEA-029","IDEA-030","IDEA-033","IDEA-035"],config={"seed":42,"ticks":12},
        criteria={"invalid_proposals":c("eq",0),"permutation_mismatches":c("eq",0),"lock_switches":c("eq",0),"missing_modes":c("eq",0)},evaluate=evaluate)
