"""Opt-in GitHub metadata transport using an already managed read credential."""
import json
import os
import re
import time
import urllib.error
import urllib.request
from . import registry as reg
from .provenance import NoRedirect, API, MAX_API

REPOS={"Jugadru/APEX-Engineering-Lab","Jugadru/APEX-Simulation","Jugadru/APEX-Hyper-Engine",
       "Jugadru/apex-godot-simulation-architect","Jugadru/APEX-Foundation",
       "Jugadru/Jugadru-APEX-Lab-Hub","Jugadru/apex-asset-factory"}
PATH=re.compile(r"/repos/([^/]+/[^/]+)/(commits/[0-9a-f]{40}|actions/(?:runs|artifacts)/[1-9][0-9]{0,19})\Z")

MAX_ATTEMPTS=3
TRANSIENT_HTTP={408,429,500,502,503,504}

def managed_get(path):
    match=PATH.fullmatch(path)
    reg.require(match is not None and match[1] in REPOS,"metadata endpoint not allowed")
    token=os.environ.get("APEX_GITHUB_READ_TOKEN","")
    reg.require(0<len(token)<=4096 and not any(c.isspace() for c in token),"managed read credential unavailable")
    request=urllib.request.Request(API+path,headers={"Accept":"application/vnd.github+json",
        "User-Agent":"APEX-Engineering-Lab/0.4.1","X-GitHub-Api-Version":"2022-11-28",
        "Authorization":"Bearer "+token})
    # Bounded retries for transient transport failures; no retry on denied
    # authorization, missing evidence or redirect. Never log secrets or bodies.
    opener=urllib.request.build_opener(NoRedirect())
    for attempt in range(MAX_ATTEMPTS):
        try:
            with opener.open(request,timeout=10) as response:
                raw=response.read(MAX_API+1)
            break
        except urllib.error.HTTPError as error:
            retry=error.code in TRANSIENT_HTTP
            reason="HTTP "+str(error.code)
            error.close()
        except OSError:
            retry=True
            reason="transport"
        if not retry or attempt==MAX_ATTEMPTS-1:
            raise ValueError("managed GitHub metadata request failed ("+reason+", "+path+")") from None
        time.sleep(attempt+1)
    reg.require(len(raw)<=MAX_API,"metadata response too large")
    return json.loads(raw,object_pairs_hook=reg.no_duplicates)

def check(repo,sha,run_id=None,fetch=managed_get):
    reg.require(repo in REPOS and reg.sha40(sha),"repository/revision not allowed")
    prefix="/repos/"+repo
    c=fetch(prefix+"/commits/"+sha)
    reg.require(c.get("sha")==sha,"revision metadata mismatch")
    out={"repository":repo,"sha":sha,"status":"REVISION_METADATA_MATCH","promotion":"NOT_AUTHORIZED",
         "scientific_review":"NOT_PERFORMED"}
    if run_id is not None:
        reg.require(type(run_id) is int and 0<run_id<10**20,"run ID")
        r=fetch(prefix+"/actions/runs/"+str(run_id))
        reg.require(r.get("id")==run_id and r.get("head_sha")==sha and (r.get("repository") or {}).get("full_name")==repo
                    and (r.get("head_repository") or {}).get("full_name")==repo,"run binding mismatch")
        out.update(run_id=run_id,run_status=r.get("status"),run_conclusion=r.get("conclusion"),run_attempt=r.get("run_attempt"))
    return out
