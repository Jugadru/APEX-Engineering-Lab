"""Exact rational swept rectangle contact in periodic longitudinal toy geometry."""
from fractions import Fraction as Q
import random
from . import registry as reg, racecraft_core as core, racecraft_space as space

LONG=space.BODY_MM+space.BUFFER_MM
LAT=space.WIDTH_MM+space.BUFFER_MM

def motion(s,ident,end):
    a=s.car(ident); reg.require(a.active,"inactive motion")
    reg.exact(end,"progress_mm lateral_mm")
    x=core.integer(end["progress_mm"],a.progress_mm,min(2000000000,a.progress_mm+100000),"forward endpoint")
    y=core.integer(end["lateral_mm"],-s.half_width_mm,s.half_width_mm,"lateral endpoint")
    return a,x,y

def relative(s,aid,bid,ea,eb):
    reg.require(aid!=bid,"distinct pair")
    a,x,y=motion(s,aid,ea); b,u,v=motion(s,bid,eb)
    return b.progress_mm-a.progress_mm,(u-b.progress_mm)-(x-a.progress_mm),b.lateral_mm-a.lateral_mm,(v-b.lateral_mm)-(y-a.lateral_mm)

def interval(x,dx,limit):
    if not dx: return (Q(0),Q(1)) if abs(x)<=limit else None
    a,b=sorted((Q(-limit-x,dx),Q(limit-x,dx)))
    lo=max(a,Q(0)); hi=min(b,Q(1))
    return (lo,hi) if lo<=hi else None

def images(x,dx,length):
    lo=min(x,x+dx)-LONG; hi=max(x,x+dx)+LONG
    return range(-((-lo)//length),hi//length+1)

def contact(s,aid,bid,ea,eb):
    x,dx,y,dy=relative(s,aid,bid,ea,eb)
    ly=interval(y,dy,LAT); first=None
    if ly:
        for k in images(x,dx,s.length_mm):
            lx=interval(x-k*s.length_mm,dx,LONG)
            if lx:
                lo=max(lx[0],ly[0]); hi=min(lx[1],ly[1])
                if lo<=hi and (first is None or lo<first): first=lo
    return {"contact":first is not None,"initial_contact":first==0,
            "first_fraction":[first.numerator,first.denominator] if first is not None else None}

def oracle(s,aid,bid,ea,eb):
    x,dx,y,dy=relative(s,aid,bid,ea,eb); times={Q(0),Q(1)}
    for k in images(x,dx,s.length_mm):
        if dx:
            times.update(Q(k*s.length_mm+sign*LONG-x,dx) for sign in (-1,1))
    if dy: times.update(Q(sign*LAT-y,dy) for sign in (-1,1))
    for t in sorted(t for t in times if 0<=t<=1):
        longitudinal=(x+dx*t)%s.length_mm
        if min(longitudinal,s.length_mm-longitudinal)<=LONG and abs(y+dy*t)<=LAT:
            return {"contact":True,"initial_contact":t==0,"first_fraction":[t.numerator,t.denominator]}
    return {"contact":False,"initial_contact":False,"first_fraction":None}

def endpoint(x,y):
    return dict(progress_mm=x,lateral_mm=y)

def fixture(xa,ya,xb,yb,da,dya,db,dyb,length=5000000):
    s=core.Snapshot.from_rows(0,length,5000,[core.row(1,xa,ya),core.row(2,xb,yb)])
    return s,endpoint(xa+da,dya),endpoint(xb+db,dyb)

def evaluate(config):
    rng=random.Random(config["seed"])
    cases=[
      ("tunneling",fixture(100000,0,120000,0,40000,0,0,0)),
      ("lateral_cross",fixture(100000,-3000,100000,3000,10000,3000,10000,-3000)),
      ("parallel",fixture(100000,-3000,100000,3000,20000,-3000,20000,3000)),
      ("wrap",fixture(4990000,0,5000,0,25000,0,0,0)),
      ("initial",fixture(100000,0,100000,0,0,0,0,0)),
      ("touch",fixture(100000,0,105300,2100,0,0,0,2100)),
      ("separated",fixture(100000,0,105301,2100,0,0,0,2100)),
      ("different_times",fixture(100000,-3000,110000,3000,20000,-3000,0,3000))]
    for i in range(config["random_cases"]):
        L=rng.choice([100000,5000000]); xa=L-10000; xb=(xa+rng.randrange(-40000,40001))%L
        cases.append(("seeded-"+str(i),fixture(xa,rng.randrange(-3800,3801),xb,rng.randrange(-3800,3801),
                     rng.randrange(100001),rng.randrange(-3800,3801),rng.randrange(100001),rng.randrange(-3800,3801),L)))
    mismatches=symmetry=hits=initial=mid=0; rows=[]
    for label,(s,a,b) in cases:
        got=contact(s,1,2,a,b); ref=oracle(s,1,2,a,b)
        mismatches+=got!=ref; symmetry+=got!=contact(s,2,1,b,a)
        hits+=got["contact"]; initial+=got["initial_contact"]
        mid+=got["contact"] and not got["initial_contact"] and got["first_fraction"]!=[1,1]
        rows.append(dict(scenario=label,**got))
    return {"metrics":{"oracle_mismatches":mismatches,"symmetry_mismatches":symmetry,"missing_contact_modes":int(not hits)+int(hits==len(cases))+int(not mid)},
            "observations":{"cases":len(rows),"contacts":hits,"initial_contacts":initial,"interior_first_contacts":mid,"rows":rows,
                "limitations":"Exact contact for linearly interpolated axis-aligned rectangular centers on periodic strip; no yaw, real track geometry, acceleration or collision dynamics."}}

def spec(c):
    return dict(hypothesis="Exact swept contact interval matches boundary-event oracle and is symmetric, including contacts between sampled endpoints.",
        sources=["REF-105","IDEA-033","IDEA-034","IDEA-040"],config={"seed":42,"random_cases":64},
        criteria={"oracle_mismatches":c("eq",0),"symmetry_mismatches":c("eq",0),"missing_contact_modes":c("eq",0)},evaluate=evaluate)
