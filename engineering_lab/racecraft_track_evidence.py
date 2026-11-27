"""Read-only pinned game data audit; not a second track geometry engine."""
import argparse
import json
import math
from pathlib import Path
import subprocess
from decimal import Decimal
from . import registry as reg

GAME_SHA="2171247db6824331b714dc2588cda15b4b60a496"
FILES={"data/season_2012.json":"23f40c722b691048f512580fd784543c34b5f7ff",
       "data/track_physics_2012.json":"f467b14def47090f4df5b57c70cb33fc7af15551",
       "data/tyres_2012.json":"51220782982b4e6ac14f6db0b5004d43fd2db2b3",
       "data/LICENSE-f1-circuits-MIT.txt":"0dea871a7a99f3a22b2d6c4e7dd0666f82956065"}
CODES=set("AUS MAL CHN BHR ESP MON CAN EUR GBR GER HUN BEL ITA SIN JPN KOR IND UAE USA BRA".split())
QUALITIES={"licensed_geojson_reference","schematic_not_historical"}

def track_summary(t):
    reg.require(isinstance(t,dict) and t.get("code") in CODES,"track code")
    km=t.get("lap_km");reg.require(reg.numeric(km) and 1<=km<=20,"lap length")
    length=Decimal(str(km))*1000000
    reg.require(length==int(length),"lap length not integral mm")
    quality=t.get("geometry_quality")
    reg.require(quality in QUALITIES and reg.nonempty(t.get("geometry_source")),"geometry provenance")
    points=t.get("points")
    reg.require(isinstance(points,list) and 4<=len(points)<=10000,"point count")
    for p in points:
        reg.require(isinstance(p,list) and len(p)==2 and all(reg.numeric(x) and 0<=x<=1 for x in p),"normalized point")
    reg.require(points[0]==points[-1] and len({tuple(x) for x in points})>=3,"closed nondegenerate path")
    distances=[math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(points,points[1:])]
    reg.require(all(x>0 for x in distances),"zero length segment")
    return {"code":t["code"],"lap_length_mm":int(length),"geometry_quality":quality,
            "geometry_source":t["geometry_source"],"source_id":t.get("geometry_source_id"),
            "segments":len(distances),"normalized_path_length":sum(distances),
            "base_lap_method":t.get("base_lap_method"),
            "metric_width":"NOT_ESTABLISHED","elevation":"NOT_ESTABLISHED",
            "historical_layout_verified":False,"real_telemetry":False}

def audit(season,physics,tyres):
    reg.require(all(isinstance(x,dict) and type(x.get("season")) is int and x["season"]==2012 for x in (season,physics,tyres)),"season")
    tracks=season.get("tracks")
    reg.require(isinstance(tracks,list) and len(tracks)==20,"track roster")
    rows=sorted((track_summary(t) for t in tracks),key=lambda x:x["code"])
    reg.require({r["code"] for r in rows}==CODES,"unique complete track roster")
    reg.require(isinstance(physics.get("tracks"),dict) and set(physics["tracks"])==CODES,"physics track coverage")
    reg.require(isinstance(tyres.get("tracks"),dict) and set(tyres["tracks"])==CODES,"tyre track coverage")
    reg.require(reg.nonempty(physics.get("note")) and reg.nonempty(tyres.get("note")),"tuning provenance")
    refs=[r["code"] for r in rows if r["geometry_quality"]=="licensed_geojson_reference"]
    placeholders=[r["code"] for r in rows if r["geometry_quality"]=="schematic_not_historical"]
    return {"schema":1,"status":"PASS","evidence_kind":"PINNED_GAME_DATA_AUDIT",
            "tracks":rows,"licensed_reference_codes":refs,"schematic_placeholder_codes":placeholders,
            "source_notes":{"physics":physics["note"],"tyres":tyres["note"]},
            "historical_calibration":"BLOCKED_NO_INDEPENDENT_MEASUREMENTS",
            "metric_geometry":"BLOCKED_NO_WIDTH_ELEVATION_OR_HISTORICAL_LAYOUT_VALIDATION",
            "game_equivalence":"NOT_RUN","promotion":"NOT_AUTHORIZED"}

def git(root,*args):
    return subprocess.check_output(["git","-C",str(root),*args],text=True,timeout=10).strip()

def run(root):
    reg.require(git(root,"rev-parse","HEAD")==GAME_SHA,"exact game revision")
    reg.require(not git(root,"status","--porcelain","--untracked-files=all"),"clean game checkout")
    for path,blob in FILES.items():
        reg.require(git(root,"rev-parse","HEAD:"+path)==blob,"pinned tree blob")
        reg.require(git(root,"hash-object","--no-filters","--",path)==blob,"working file blob")
    result=audit(*(reg.read_json(root/p) for p in list(FILES)[:3]))
    result.update(game_sha=GAME_SHA,source_blobs=FILES,license_notice="MIT attribution present in game source; no geometry points copied into Lab")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--game",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();r=run(a.game)
    reg.publish_once(a.output,r)
    print(json.dumps({k:v for k,v in r.items() if k!="tracks"},sort_keys=True))
if __name__=="__main__":main()
