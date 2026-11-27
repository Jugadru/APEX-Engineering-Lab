"""Static spatial awareness; frozen rectangular footprints, not a moving solver."""
import random
from types import MappingProxyType
from . import registry as reg, racecraft_core as core, exp_spatial

# Identical synthetic car dimensions; conservative inclusive contact convention.
BODY_MM=5000
WIDTH_MM=1800
BUFFER_MM=300

class Awareness:
    def __init__(self,snapshot):
        self.snapshot=snapshot
        self.cars=MappingProxyType({c.id:c for c in snapshot.cars if c.active})
        self.index=exp_spatial.Ring([(c.id,c.progress_mm%snapshot.length_mm) for c in self.cars.values()],snapshot.length_mm)

    def own(self,ident):
        core.integer(ident,0,255,"observer")
        reg.require(ident in self.cars,"unknown/inactive observer")
        return self.cars[ident]

    def nearby(self,ident,radius_mm):
        a=self.own(ident); L=self.snapshot.length_mm
        core.integer(radius_mm,0,L//2,"radius")
        ids,_=self.index.query((ident,a.progress_mm%L),radius_mm)
        rows=[]
        for i in ids:
            b=self.cars[i]
            gap=core.signed_gap(a.progress_mm,b.progress_mm,L)
            lateral=b.lateral_mm-a.lateral_mm
            closing=a.speed_mm_s-b.speed_mm_s
            same_corridor=abs(lateral)<=WIDTH_MM+BUFFER_MM
            ttc=None
            if gap>0 and same_corridor and closing>0:
                ttc=max(0,gap-BODY_MM-BUFFER_MM)*1000//closing
            rows.append(dict(id=i,gap_mm=gap,lateral_delta_mm=lateral,closing_mm_s=closing,
                             same_corridor=same_corridor,ttc_ms=ttc))
        return tuple(sorted(rows,key=lambda r:(abs(r["gap_mm"]),r["id"])))

    def leaders(self,ident,radius_mm):
        rows=self.nearby(ident,radius_mm)
        front=next((r for r in rows if r["gap_mm"]>0 and r["same_corridor"]),None)
        rear=next((r for r in rows if r["gap_mm"]<0 and r["same_corridor"]),None)
        coincident=[r["id"] for r in rows if r["gap_mm"]==0 and r["same_corridor"]]
        return dict(front=front,rear=rear,coincident=coincident)

    def clearance(self,ident,target_mm):
        a=self.own(ident); limit=self.snapshot.half_width_mm
        core.integer(target_mm,-limit,limit,"target")
        lo,hi=sorted((a.lateral_mm,target_mm))
        edge=lo-WIDTH_MM//2-BUFFER_MM < -limit or hi+WIDTH_MM//2+BUFFER_MM > limit
        blockers=[]
        for r in self.nearby(ident,BODY_MM+BUFFER_MM):
            b=self.cars[r["id"]]
            if lo-WIDTH_MM-BUFFER_MM<=b.lateral_mm<=hi+WIDTH_MM+BUFFER_MM:
                blockers.append(b.id)
        return dict(clear=not edge and not blockers,edge=edge,blockers=sorted(blockers),
                    meaning="STATIC_LATERAL_SWEEP_ONLY")

def oracle_ids(s,ident,radius):
    a=s.car(ident); L=s.length_mm
    return sorted(b.id for b in s.cars if b.active and b.id!=ident and
                  min((b.progress_mm-a.progress_mm)%L,(a.progress_mm-b.progress_mm)%L)<=radius)

def oracle_clearance(s,ident,target):
    a=s.car(ident); lo=min(a.lateral_mm,target); hi=max(a.lateral_mm,target)
    edge=lo < -s.half_width_mm+1200 or hi > s.half_width_mm-1200
    blockers=[]
    for b in s.cars:
        if not b.active or b.id==ident: continue
        d=(b.progress_mm-a.progress_mm)%s.length_mm
        if min(d,s.length_mm-d)>5300: continue
        # Expanded intervals overlap iff rival center lies within this corridor.
        if not (b.lateral_mm+2100<lo or b.lateral_mm-2100>hi): blockers.append(b.id)
    return dict(clear=not edge and not blockers,edge=edge,blockers=sorted(blockers),
                meaning="STATIC_LATERAL_SWEEP_ONLY")

def evaluate(config):
    rng=random.Random(config["seed"]); L=config["length_mm"]; n=config["cars"]
    layouts={
        "uniform":[core.row(i,rng.randrange(L),rng.randrange(-3800,3801),rng.randrange(20000,70001)) for i in range(n)],
        "dense":[core.row(i,100000+i*700,(-1)**i*2100,40000) for i in range(n)],
        "wrap":[core.row(i,(L-4000+i*500)%L,(-1)**i*1800,30000+i*1000) for i in range(n)],
        "inactive":[core.row(i,100000+(i%3)*L+i*500,0,40000,i%4!=0) for i in range(n)],
        "coincident":[core.row(i,100000,0,40000) for i in range(n)]}
    errors=clear_errors=permutation_errors=queries=clear_cases=blocked=free=ttcs=0
    rows=[]
    for label,rs in layouts.items():
        s=core.Snapshot.from_rows(5,L,5000,rs); a=Awareness(s)
        shuffled=rs[:]; rng.shuffle(shuffled)
        alt=Awareness(core.Snapshot.from_rows(5,L,5000,shuffled))
        q=cl=0
        for own in s.cars:
            if not own.active: continue
            for radius in config["radii_mm"]:
                obs=a.nearby(own.id,radius); ids=sorted(r["id"] for r in obs)
                errors+=ids!=oracle_ids(s,own.id,radius)
                permutation_errors+=obs!=alt.nearby(own.id,radius)
                ttcs+=sum(r["ttc_ms"] is not None for r in obs)
                q+=1
            for target in config["targets_mm"]:
                c=a.clearance(own.id,target)
                clear_errors+=c!=oracle_clearance(s,own.id,target)
                permutation_errors+=c!=alt.clearance(own.id,target)
                blocked+=not c["clear"]; free+=c["clear"]; cl+=1
        queries+=q; clear_cases+=cl; rows.append(dict(scenario=label,queries=q,clearance_cases=cl))
    return {"metrics":{"neighbor_mismatches":errors,"clearance_mismatches":clear_errors,
                       "permutation_mismatches":permutation_errors,"missing_clearance_modes":int(not blocked)+int(not free)},
            "observations":{"queries":queries,"clearance_cases":clear_cases,"blocked":blocked,"clear":free,"ttc_observations":ttcs,
                            "rows":rows,"limitations":"Static frozen footprints, constant relative-speed TTC estimate only; not swept time collision, no braking prediction, no actual track geometry or game equivalence."}}

def spec(c):
    return dict(hypothesis="Reused circular index and frozen footprint clearance match exhaustive references independently of input ordering.",
        sources=["REF-105","IDEA-024","IDEA-033","IDEA-034","IDEA-040"],
        config={"seed":42,"cars":24,"length_mm":5000000,"radii_mm":[0,5300,38000,2500000],"targets_mm":[-5000,-3000,0,3000,5000]},
        criteria={"neighbor_mismatches":c("eq",0),"clearance_mismatches":c("eq",0),"permutation_mismatches":c("eq",0),"missing_clearance_modes":c("eq",0)},evaluate=evaluate)
