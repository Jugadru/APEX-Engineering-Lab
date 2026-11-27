"""Documentary 2012 fastest-lap pace proxy, not physical or personality calibration.

Fixed temporal-group holdout before evaluation. Targets are per-race fastest
lap ratios relative to the observed field median, not prospective lap forecasts.
"""
import argparse
import json
from pathlib import Path
import re
from statistics import median
from . import registry as reg, racecraft_historical_reference as hist
from .racecraft_outline_evidence import git, check

HOLDOUT=frozenset((4,8,12,16,20))
FILES={
    "src/data/seasons/2012/races/01-australia/fastest-laps.yml":"e0dae819c8e3ad23b218946935de1437349e4337",
    "src/data/seasons/2012/races/02-malaysia/fastest-laps.yml":"d4ba8f0627f382f1792ade97b07860a33c46f54f",
    "src/data/seasons/2012/races/03-china/fastest-laps.yml":"38deb6404e71c0b2cc143e01335bc8a4520bbaee",
    "src/data/seasons/2012/races/04-bahrain/fastest-laps.yml":"3edf7700a24d05eb13ea7da4f06d9a9bd5974311",
    "src/data/seasons/2012/races/05-spain/fastest-laps.yml":"53f901f00adf2529860be2a6f1e97b0081140340",
    "src/data/seasons/2012/races/06-monaco/fastest-laps.yml":"64db3c1a36c89164d83aab2f3ea3712615881c3b",
    "src/data/seasons/2012/races/07-canada/fastest-laps.yml":"ed30f13a1ac9361ba75941b339f1ba0d4b4b1b00",
    "src/data/seasons/2012/races/08-europe/fastest-laps.yml":"4608a1a692a9d8983d7c5798d37ab043984da05f",
    "src/data/seasons/2012/races/09-great-britain/fastest-laps.yml":"2f46a0ea45df10adaadbcbee5c696171c62a53fa",
    "src/data/seasons/2012/races/10-germany/fastest-laps.yml":"6b89cc2f2bd87e9c2ec53cc4bd9806c902c3a3dc",
    "src/data/seasons/2012/races/11-hungary/fastest-laps.yml":"c216c812073ba116f09ae9929b74cf6bb3bf72ed",
    "src/data/seasons/2012/races/12-belgium/fastest-laps.yml":"80797649144c60cd9b8ebeebb489c820b7e73410",
    "src/data/seasons/2012/races/13-italy/fastest-laps.yml":"eb9f9cffdfaf48b5a6cd62047257ec25822af4ae",
    "src/data/seasons/2012/races/14-singapore/fastest-laps.yml":"c212e045edb3f027619ec06651942be0e60e77a3",
    "src/data/seasons/2012/races/15-japan/fastest-laps.yml":"6b952ee9beb56784d82b3b46c754c0524f6e638d",
    "src/data/seasons/2012/races/16-korea/fastest-laps.yml":"cb5bd540904bbd31026a929c7c8b99ba4bb74e9b",
    "src/data/seasons/2012/races/17-india/fastest-laps.yml":"48f854678267aee3bfa20a01ed7cf949be72541c",
    "src/data/seasons/2012/races/18-abu-dhabi/fastest-laps.yml":"c9a82e8ddaf71b319a33474b5c52729f2d1ac50c",
    "src/data/seasons/2012/races/19-united-states/fastest-laps.yml":"84903444fdf19013568f247f271de842a9436487",
    "src/data/seasons/2012/races/20-brazil/fastest-laps.yml":"5d130817e20cb996d0b31a84e4b5d957eea3050c",
}
ID=re.compile(r"[a-z0-9][a-z0-9-]*")
TIME=re.compile(r'"([0-9]{1,2}:[0-5][0-9]\.[0-9]{3})"')

def parse(raw):
    """Strict subset of pinned F1DB fastest-lap YAML (flat scalar records)."""
    rows=[];current=None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("- "):
            if current is not None:
                rows.append(current)
            current={}
            line=line[2:]
        else:
            reg.require(current is not None and line.startswith("  "),"unexpected row")
            line=line[2:]
        k,sep,val=line.partition(":")
        reg.require(bool(sep) and k not in current,"invalid or duplicate field")
        current[k]=val.strip()
    if current is not None:
        rows.append(current)
    seen=set();out=[]
    for row in rows:
        d=row.get("driverId","");c=row.get("constructorId","")
        reg.require(ID.fullmatch(d) is not None and ID.fullmatch(c) is not None and d not in seen,"driver/constructor identity")
        seen.add(d)
        t=row.get("time","")
        if t in ("","null","~"):
            continue
        match=TIME.fullmatch(t)
        reg.require(match is not None,"unrecognized fastest lap")
        ms=hist.lap_ms(match[1])
        reg.require(30000<=ms<=300000,"lap-time domain")
        out.append((d,c,ms))
    reg.require(len(out)>=10,"insufficient timed drivers")
    return out

def benchmark(rounds):
    reg.require(set(rounds)==set(range(1,21)),"complete calendar required")
    team={};pair={};train=[];test=[]
    for rnd,rows in sorted(rounds.items()):
        base=median(ms for _,_,ms in rows)
        for d,c,ms in rows:
            value=1000*(ms/base-1)
            (test if rnd in HOLDOUT else train).append((rnd,d,c,value))
    for _,d,c,value in train:
        team.setdefault(c,[]).append(value)
        pair.setdefault((d,c),[]).append(value)
    global_base=median(x[3] for x in train)
    errors=[[],[],[]];unseen=0
    for _,d,c,value in test:
        t=median(team[c]) if c in team else global_base
        p=median(pair[d,c]) if (d,c) in pair else t
        unseen+=int((d,c) not in pair)
        for target,pred in zip(errors,(global_base,t,p)):
            target.append(abs(value-pred))
    mae=[sum(x)/len(x) for x in errors]
    return dict(kind="OBSERVATIONAL_PACE_PROXY",training_rounds=sorted(set(rounds)-HOLDOUT),
                holdout_rounds=sorted(HOLDOUT),training_rows=len(train),holdout_rows=len(test),unseen_driver_team_rows=unseen,
                metric="MAE in per mille of observed field median lap time",
                global_mae=mae[0],team_mae=mae[1],driver_team_mae=mae[2],
                driver_team_beats_team=mae[2]<mae[1],
                physical_calibration="NOT_ESTABLISHED",promotion="NOT_AUTHORIZED",
                limitations="Fastest laps reflect car, fuel, tyres, traffic, weather and strategy; no causal driver effects, telemetry or prospective race prediction. Held-out rounds are independent of fitting but not an independent external source.")

def run(root):
    reg.require(git(root,"rev-parse","HEAD")==hist.F1DB_SHA,"pinned source revision")
    reg.require(not git(root,"status","--porcelain","--untracked-files=all"),"clean source")
    check(root,"LICENSE","4ea99c213c5c0c005ae4e80df8e52169d06896ec")
    rounds={}
    for path,blob in FILES.items():
        check(root,path,blob)
        rnd=int(path.split("/")[-2].split("-")[0])
        rounds[rnd]=parse((root/path).read_text(encoding="utf-8"))
    return dict(source_sha=hist.F1DB_SHA,source_repo="https://github.com/f1db/f1db",source_blobs=FILES,
                attribution="F1DB contributors, CC BY 4.0 repository notice; downstream data rights not independently established.",
                **benchmark(rounds))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();result=run(a.source)
    reg.publish_once(a.output,result)
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
