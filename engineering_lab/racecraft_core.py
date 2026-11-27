"""Original frozen racecraft observation contract in integer SI subunits."""
from dataclasses import dataclass, asdict
import random
from . import registry as reg

def integer(x,lo,hi,name):
    reg.require(type(x) is int and lo<=x<=hi,"invalid "+name)
    return x

@dataclass(frozen=True)
class Car:
    id: int
    progress_mm: int
    lateral_mm: int
    speed_mm_s: int
    active: bool=True

    def __post_init__(self):
        integer(self.id,0,255,"id")
        integer(self.progress_mm,0,2000000000,"progress")
        integer(self.lateral_mm,-15000,15000,"lateral")
        integer(self.speed_mm_s,0,200000,"speed")
        reg.require(type(self.active) is bool,"active")

@dataclass(frozen=True)
class Snapshot:
    tick: int
    length_mm: int
    half_width_mm: int
    cars: tuple

    def __post_init__(self):
        integer(self.tick,0,1000000,"tick")
        integer(self.length_mm,100000,20000000,"track length")
        integer(self.half_width_mm,1000,15000,"half width")
        reg.require(type(self.cars) is tuple and 1<=len(self.cars)<=24 and all(type(c) is Car for c in self.cars),"immutable roster")
        ids=tuple(c.id for c in self.cars)
        reg.require(ids==tuple(sorted(set(ids))),"unique canonical car IDs")
        reg.require(all(abs(c.lateral_mm)<=self.half_width_mm for c in self.cars),"lateral outside track")

    @classmethod
    def from_rows(cls,tick,length_mm,half_width_mm,rows):
        reg.require(isinstance(rows,(list,tuple)) and 1<=len(rows)<=24,"roster size")
        cars=[]
        for row in rows:
            reg.exact(row,"id progress_mm lateral_mm speed_mm_s active")
            cars.append(Car(**row))
        return cls(tick,length_mm,half_width_mm,tuple(sorted(cars,key=lambda c:c.id)))

    def payload(self):
        return {"tick":self.tick,"length_mm":self.length_mm,"half_width_mm":self.half_width_mm,
                "cars":[asdict(c) for c in self.cars]}

    def classification(self):
        return tuple(c.id for c in sorted((c for c in self.cars if c.active),key=lambda c:(-c.progress_mm,c.id)))

    def car(self,ident):
        integer(ident,0,255,"id")
        for c in self.cars:
            if c.id==ident: return c
        raise ValueError("unknown car ID")

    def observations(self,ident):
        own=self.car(ident)
        reg.require(own.active,"inactive observer")
        result=[]
        for c in self.cars:
            if c.id==ident or not c.active: continue
            result.append({"id":c.id,"gap_mm":signed_gap(own.progress_mm,c.progress_mm,self.length_mm),
                           "lateral_delta_mm":c.lateral_mm-own.lateral_mm,
                           "closing_mm_s":own.speed_mm_s-c.speed_mm_s,
                           "classified_delta_mm":c.progress_mm-own.progress_mm})
        return tuple(sorted(result,key=lambda r:(abs(r["gap_mm"]),r["id"])))

def signed_gap(own_mm,rival_mm,length_mm):
    integer(own_mm,0,2000000000,"own progress")
    integer(rival_mm,0,2000000000,"rival progress")
    integer(length_mm,100000,20000000,"track length")
    d=(rival_mm-own_mm)%length_mm
    # Exactly opposite is consistently negative, not interpreted as a nearby leader.
    return d-length_mm if 2*d>=length_mm else d

def row(ident,progress,lateral=0,speed=40000,active=True):
    return dict(id=ident,progress_mm=progress,lateral_mm=lateral,speed_mm_s=speed,active=active)

def evaluate(config):
    rng=random.Random(config["seed"]); n=config["cars"]; L=config["length_mm"]
    layouts={
        "grid":[row(i,(n-i)*7000,(-1)**i*1800) for i in range(n)],
        "wrap":[row(i,(L-5000+i*1000)%L,0,40000+i*100) for i in range(n)],
        "lapped":[row(i,(i%3)*L+10000+(i%4)*1000,(-1)**i*1500) for i in range(n)],
        "ties":[row(i,50000,0,40000,i%5!=0) for i in range(n)]}
    mismatch=invalid=0; queries=0; details=[]
    for name,rows in layouts.items():
        s=Snapshot.from_rows(1,L,5000,rows)
        expected=s.classification()
        # Oracle independent of the canonical observation sort.
        ranks=tuple(r["id"] for r in sorted((r for r in rows if r["active"]),key=lambda r:(-r["progress_mm"],r["id"])))
        invalid+=expected!=ranks
        obs={c.id:s.observations(c.id) for c in s.cars if c.active}
        for own in s.cars:
            if not own.active: continue
            for o in obs[own.id]:
                rival=s.car(o["id"]); gap=o["gap_mm"]
                invalid+=not (-L<=2*gap<L and (own.progress_mm+gap-rival.progress_mm)%L==0 and rival.active and own.id!=rival.id)
                queries+=1
        fingerprint=reg.digest(s.payload())
        for _ in range(config["permutations"]):
            perm=rows[:]; rng.shuffle(perm); p=Snapshot.from_rows(1,L,5000,perm)
            mismatch+=reg.digest(p.payload())!=fingerprint or p.classification()!=expected or any(p.observations(i)!=o for i,o in obs.items())
        details.append({"scenario":name,"active_cars":len(expected),"state_sha256":fingerprint})
    return {"metrics":{"permutation_mismatches":mismatch,"invalid_observations":invalid},
            "observations":{"layouts":len(layouts),"permutations":len(layouts)*config["permutations"],"pair_observations":queries,"rows":details,
              "limitations":"Frozen synthetic observations, active subset classification only, not sporting positions including pit/finished cars; no motion, tactical intent, collision or real-track geometry."}}

def spec(c):
    return dict(hypothesis="Frozen active-car snapshots and physical gap observations are permutation invariant, distinct from classified progress.",
        sources=["REF-105","IDEA-031","IDEA-033","IDEA-034"],config={"seed":42,"cars":24,"length_mm":5000000,"permutations":32},
        criteria={"permutation_mismatches":c("eq",0),"invalid_observations":c("eq",0)},evaluate=evaluate)
