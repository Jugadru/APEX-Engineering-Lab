"""Narrow-phase continuous contact for the frozen-force strip reference.

Rational quadratic ranges on common time intervals; conservative uncertainty
at a bounded subdivision limit. No oriented-body or curved-track claim.
"""
from fractions import Fraction as Q

EPS=Q(1,100000000)
MAX_DEPTH=16

def path(start,end,dt):
    """Return normalized-time position functions and stop breakpoint.
    Reject inconsistent endpoints so callers retain the broad conservative test.
    """
    dt=Q(dt)
    x0,x1=Q(start["progress_m"]),Q(end["progress_m"])
    y0,y1=Q(start["lateral_m"]),Q(end["lateral_m"])
    v0,v1=Q(start["vehicle"]["speed_mps"]),Q(end["vehicle"]["speed_mps"])
    w0,w1=Q(start["lateral_speed_mps"]),Q(end["lateral_speed_mps"])
    if abs(y1-y0-dt*(w0+w1)/2)>EPS:
        return None
    stop=Q(1)
    if v1==0 and v0>0 and x1-x0<dt*v0/2:
        stop=2*(x1-x0)/(dt*v0)
        if not 0<stop<=1:
            return None
    elif abs(x1-x0-dt*(v0+v1)/2)>EPS:
        return None
    def x(t):
        if t>=stop:
            return x1
        u=t/stop
        return x0+(x1-x0)*u+dt*stop*(v1-v0)*u*(u-1)/2
    def y(t):
        return y0+(y1-y0)*t+dt*(w1-w0)*t*(t-1)/2
    return x,y,stop

def bounds(f,lo,hi):
    """Exact range of a quadratic on one interval, using three evaluations."""
    a=f(lo); b=f(hi); m=f((lo+hi)/2)
    c=2*(a+b-2*m); d=b-a-c
    values=[a,b]
    if c:
        t=-d/(2*c)
        if 0<t<1:
            values.append(a+d*t+c*t*t)
    return min(values),max(values)

def refine(a,b,ea,eb,length,dt,long_limit,lat_limit):
    """Return True for contact/uncertainty, False for certified separation,
    or None when supplied endpoints do not describe supported physical paths.
    """
    p=path(a,ea,dt); q=path(b,eb,dt)
    if p is None or q is None:
        return None
    length=Q(length); lx=Q(long_limit)+2*EPS; ly=Q(lat_limit)+2*EPS
    dx=lambda t:q[0](t)-p[0](t)
    dy=lambda t:q[1](t)-p[1](t)
    def possible(lo,hi,depth):
        ymin,ymax=bounds(dy,lo,hi)
        if ymin>ly or ymax<-ly:
            return False
        xmin,xmax=bounds(dx,lo,hi)
        low=xmin-lx; high=xmax+lx
        images=range(-((-low)//length),high//length+1)
        if not images:
            return False
        if ymin>=-ly and ymax<=ly:
            # Continuity plus intersecting range suffices for contact.
            return True
        for t in (lo,(lo+hi)/2,hi):
            x=dx(t)%length
            if min(x,length-x)<=lx and abs(dy(t))<=ly:
                return True
        if depth==MAX_DEPTH:
            return True
        mid=(lo+hi)/2
        return possible(lo,mid,depth+1) or possible(mid,hi,depth+1)
    cuts=sorted({Q(0),p[2],q[2],Q(1)})
    return any(possible(lo,hi,0) for lo,hi in zip(cuts,cuts[1:]))
