"""Original circular neighbor query; integer metre fixtures, not live collision resolution."""
from bisect import bisect_left,bisect_right
import random
from . import registry as reg

def scan(rows,own,length,radius):
    ident,p=own
    found=[]
    visits=0
    for other,q in rows:
        if other==ident: continue
        visits+=1
        delta=abs(q-p)
        if min(delta,length-delta)<=radius: found.append(other)
    return sorted(found),visits

class Ring:
    def __init__(self,rows,length):
        reg.require(type(length) is int and length>0 and len(rows)<=256 and
                    len({i for i,_ in rows})==len(rows) and
                    all(type(i) is int and type(p) is int and 0<=p<length for i,p in rows),"ring input")
        self.length=length
        self.rows=sorted((p,i) for i,p in rows)
        self.positions=[p for p,_ in self.rows]
    def query(self,own,radius):
        ident,p=own; length=self.length
        reg.require(type(radius) is int and 0<=radius<=length//2 and type(p) is int and 0<=p<length,"ring query")
        if 2*radius>=length:
            spans=[(0,length-1)]
        else:
            lo,hi=p-radius,p+radius
            spans=[(lo,hi)] if lo>=0 and hi<length else ([(0,hi),(lo+length,length-1)] if lo<0 else [(lo,length-1),(0,hi-length)])
        found=[]
        for low,high in spans:
            a=bisect_left(self.positions,low); b=bisect_right(self.positions,high)
            found.extend(i for _,i in self.rows[a:b] if i!=ident)
        return sorted(found),len(found)

def evaluate(config):
    rng=random.Random(config["seed"]); n=config["cars"]; L=config["length_m"]
    cases={
        "uniform":[rng.randrange(L) for _ in range(n)],
        "grid":[i*10 for i in range(n)],
        "clustered":[200+rng.randrange(50) for _ in range(n)],
        "wrap":[(L-12+i)%L for i in range(n)],
        "coincident":[100]*n,
        "spread":[i*L//n for i in range(n)]}
    total_b=total_c=errors=queries=0; details=[]
    for label,positions in cases.items():
        rows=list(enumerate(positions)); rng.shuffle(rows)
        ring=Ring(rows,L)
        b=c=m=qcount=0
        for radius in config["radii_m"]:
            for own in rows:
                a,av=scan(rows,own,L,radius); z,zv=ring.query(own,radius)
                m+=a!=z; b+=av; c+=zv; qcount+=1
        total_b+=b; total_c+=c; errors+=m; queries+=qcount
        details.append({"scenario":label,"queries":qcount,"scan_other_rows":b,"index_other_rows":c,"mismatches":m})
    return {"metrics":{"neighbor_mismatches":errors,"extra_rows":total_c-total_b},
            "observations":{"queries":queries,"scan_other_rows":total_b,"index_other_rows":total_c,"scenarios":details,
                            "limitations":"Counts returned/inspected other rows only; excludes sorting, bisect comparisons, allocation and timing."}}
