"""Still-air SI force reference; prescribed modifiers, no CFD or wake selection."""
from .physics_core import scalar

def forces(speed_mps,density_kg_m3,cda_m2,cla_m2,drag_loss=0,load_loss=0):
    v=scalar(speed_mps,0,200,"speed_mps"); rho=scalar(density_kg_m3,0,3,"density")
    cd=scalar(cda_m2,0,10,"CdA"); cl=scalar(cla_m2,0,10,"ClA")
    d=scalar(drag_loss,0,1,"drag_loss"); l=scalar(load_loss,0,1,"load_loss")
    q=0.5*rho*v*v
    drag=q*cd*(1-d); load=q*cl*(1-l)
    return {"drag_n":drag,"downforce_n":load,"drag_power_w":drag*v}

def evaluate(config):
    rows=[]; err=0.0; bad=0
    for rho in config["densities"]:
        for v in config["speeds"]:
            base=forces(v,rho,config["cda"],config["cla"])
            for d,l in config["losses"]:
                r=forces(v,rho,config["cda"],config["cla"],d,l)
                bad+=not (0<=r["drag_n"]<=base["drag_n"] and 0<=r["downforce_n"]<=base["downforce_n"])
                err=max(err,abs(r["drag_power_w"]-r["drag_n"]*v))
                rows.append({"density_kg_m3":rho,"speed_mps":v,"drag_loss":d,"load_loss":l,**r})
    scale=forces(60,1.2,0.8,2.5); ref=forces(30,1.2,0.8,2.5)
    scaling=max(abs(scale["drag_n"]/ref["drag_n"]-4),abs(scale["downforce_n"]/ref["downforce_n"]-4),
                abs(scale["drag_power_w"]/ref["drag_power_w"]-8))
    return {"metrics":{"invalid_forces":bad,"power_residual_w":err,"scaling_error":scaling},
            "observations":{"cases":len(rows),"rows":rows,"limitations":"Steady still-air reference, prescribed independent drag/downforce reductions; no CFD, wake geometry, DRS authorization, ground effect or calibration."}}

def spec(c):
    return dict(hypothesis="Nonnegative drag/downforce scale with speed squared, drag power with speed cubed; prescribed losses cannot increase either force.",
                sources=["REF-107","IDEA-010","IDEA-011"],
                config={"seed":42,"densities":[0,1.0,1.2],"speeds":[0,20,60,90],"cda":0.8,"cla":2.5,"losses":[[0,0],[0.15,0],[0,0.2],[0.15,0.2]]},
                criteria={"invalid_forces":c("eq",0),"power_residual_w":c("le",1e-10,"W"),"scaling_error":c("le",1e-12,"ratio")},evaluate=evaluate)
