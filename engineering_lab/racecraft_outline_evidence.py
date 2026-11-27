"""Read-only 2012 outline reconstruction. Scaled drawing, never survey geometry."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from . import registry as reg, racecraft_historical_reference as historical

N=1024
FACTS={
 "EUR":{"direction":"CLOCKWISE","start_finish_offset_m":0,"source":"https://www.fia.com/race-preview-6"},
 "KOR":{"direction":"ANTI_CLOCKWISE","start_finish_offset_m":195,"source":"https://www.fia.com/news/f1-korean-gp-race-preview"},
 "IND":{"direction":"CLOCKWISE","start_finish_offset_m":251,"source":"https://www.fia.com/news/indian-gp-race-preview"}}

def reconstruct(points,length_m,direction):
    reg.require(len(points)>=4 and points[0]==points[-1],"closed drawing")
    reg.require(all(math.isfinite(p.real) and math.isfinite(p.imag) for p in points),"finite drawing")
    reg.require(direction in ("CLOCKWISE","ANTI_CLOCKWISE") and reg.numeric(length_m) and length_m>0,"length/direction")
    # SVG y increases downward. Use a right-handed local planar frame.
    pts=[complex(p.real,-p.imag) for p in points]
    area=sum(a.real*b.imag-a.imag*b.real for a,b in zip(pts,pts[1:]))
    reg.require(abs(area)>1e-9,"nondegenerate orientation")
    if (area<0)!=(direction=="CLOCKWISE"):
        pts=pts[::-1]
    distances=[abs(b-a) for a,b in zip(pts,pts[1:])]
    reg.require(all(d>0 for d in distances),"zero-length drawing edge")
    total=math.fsum(distances);scale=length_m/total
    origin=pts[0]; result=[]; station=0.0
    for i,p in enumerate(pts):
        result.append([station*scale,(p.real-origin.real)*scale,(p.imag-origin.imag)*scale])
        if i<len(distances):
            station+=distances[i]
    result[-1][0]=float(length_m)
    return result

def git(root,*args):
    return subprocess.check_output(["git","-C",str(root),*args],text=True,timeout=15).strip()

def check(root,path,blob):
    reg.require(git(root,"rev-parse","HEAD:"+path)==blob,"source tree blob mismatch")
    reg.require(git(root,"hash-object","--no-filters","--",path)==blob,"working blob mismatch")

def run(root):
    from svgpathtools import parse_path
    reg.require(git(root,"rev-parse","HEAD")==historical.F1DB_SHA,"exact outline revision")
    reg.require(not git(root,"status","--porcelain","--untracked-files=all"),"clean outline checkout")
    check(root,"LICENSE","4ea99c213c5c0c005ae4e80df8e52169d06896ec")
    rows=[]
    for code,m in sorted(historical.LAYOUTS.items()):
        svg="src/assets/circuits/black-outline/"+m["id"]+".svg"
        race="src/data/seasons/2012/races/"+m["race"]+"/race.yml"
        check(root,svg,m["svg_blob"]);check(root,race,m["race_blob"])
        metadata=dict(line.split(": ",1) for line in (root/race).read_text(encoding="utf-8").splitlines() if ": " in line)
        facts=FACTS[code]
        reg.require(metadata["circuitLayoutId"]==m["id"] and metadata["direction"]==facts["direction"] and
                    abs(float(metadata["courseLength"])*1000-m["length_m"])<1e-9,"historical source identity")
        doc=ET.parse(root/svg).getroot()
        paths=doc.findall("{http://www.w3.org/2000/svg}path")
        reg.require(paths and not paths[0].get("transform") and not doc.get("transform"),"unsupported SVG transform")
        reg.require("stroke: #000" in paths[0].get("style",""),"expected black center path")
        path=parse_path(paths[0].get("d"))
        reg.require(path.iscontinuous() and path.isclosed(),"single closed path")
        points=[path.point(i/N) for i in range(N)]
        points.append(points[0])
        stations=reconstruct(points,m["length_m"],facts["direction"])
        actual=math.fsum(math.hypot(b[1]-a[1],b[2]-a[2]) for a,b in zip(stations,stations[1:]))
        reg.require(abs(actual-m["length_m"])<1e-6,"scaled polyline length")
        rows.append(dict(code=code,layout=m["id"],source_svg=svg,source_blob=m["svg_blob"],
                         race_blob=m["race_blob"],points_sxy_m=stations,scaled_length_m=actual,
                         direction=facts["direction"],start_finish_offset_m=facts["start_finish_offset_m"],
                         official_reference=facts["source"],station_origin="DRAWING_PATH_START_NOT_HISTORICAL_START_LINE",
                         width_m=None,elevation_m=None,curvature_calibration="NOT_ESTABLISHED",
                         quality="LENGTH_SCALED_ILLUSTRATION_NOT_METRIC_SURVEY"))
    return dict(status="PASS",kind="DOCUMENTARY_OUTLINE_RECONSTRUCTION",source_repo="https://github.com/f1db/f1db",
                source_sha=historical.F1DB_SHA,attribution="F1DB contributors; derived by path sampling, coordinate inversion and uniform scale; repository CC BY 4.0 notice; https://creativecommons.org/licenses/by/4.0/; downstream asset rights not independently established.",
                rows=rows,metric_geometry="BLOCKED_NO_SURVEY_WIDTH_ELEVATION_OR_COORDINATE_CONTROL",
                promotion="NOT_AUTHORIZED")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();r=run(a.source)
    reg.publish_once(a.output,r)
    print(json.dumps({**r,"rows":[{k:v for k,v in x.items() if k!="points_sxy_m"} for x in r["rows"]]},sort_keys=True))
if __name__=="__main__":main()
