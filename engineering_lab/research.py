"""Research triage: no execution, ingestion, or authorization of external code."""
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import date
from . import registry as reg
from .provenance import NoRedirect

DOMAINS={"physics","racecraft","strategy","soul","factory","universe","quality","hyper_engine"}

def git_blob(data):
    return hashlib.sha1(("blob %d\0"%len(data)).encode()+data).hexdigest()

def load_foundation(folder,pin):
    reg.exact(pin,"schema repository commit files counts")
    reg.require(pin["schema"]==1 and pin["repository"]=="Jugadru/APEX-Foundation" and reg.sha40(pin["commit"]),"Foundation pin")
    reg.exact(pin["files"],"references.json possibilities.json")
    reg.exact(pin["counts"],"references possibilities")
    output={}
    for name,prefix,kind in (("references.json","REF","references"),("possibilities.json","IDEA","possibilities")):
        raw=reg.bounded_bytes(folder/name)
        reg.require(reg.sha40(pin["files"][name]) and git_blob(raw)==pin["files"][name],"Foundation blob mismatch: "+name)
        data=json.loads(raw,object_pairs_hook=reg.no_duplicates)
        reg.require(data.get("schema")==1 and isinstance(data.get("entries"),list),"catalog schema")
        rows=data["entries"]
        reg.require(type(pin["counts"][kind]) is int and len(rows)==pin["counts"][kind],"catalog count")
        index={}
        for row in rows:
            ident=row["id"]
            reg.require(reg.match(ident,prefix+r"-[0-9]{3,}") and ident not in index and reg.nonempty(row["name"]),"catalog row")
            index[ident]=row
        output[kind]=index
    for idea in output["possibilities"].values():
        reg.require(isinstance(idea["references"],list) and bool(idea["references"]) and set(idea["references"])<=set(output["references"]),"catalog cross-link")
    return output

def source_gate(s):
    reg.exact(s,"id repo sha license license_blob license_url checked_on method limits papers reuse")
    reg.require(reg.match(s["id"],r"REF-[0-9]{3,}") and reg.match(s["repo"],r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"),"source identity")
    reg.require(reg.sha40(s["sha"]) and reg.sha40(s["license_blob"]),"source revision")
    reg.require(s["license_url"]=="https://github.com/"+s["repo"]+"/blob/"+s["sha"]+"/LICENSE","license URL")
    date.fromisoformat(s["checked_on"])
    reg.require(all(reg.nonempty(s[k]) for k in ("license","method","limits")),"source description")
    reg.require(isinstance(s["papers"],list) and all(reg.match(x,r"https://doi\.org/[^\s]+") for x in s["papers"]),"DOI")
    reg.require(s["reuse"]=="CONCEPT_ONLY","copy/adapt not authorized")
    return {"source":s["id"],"license":s["license"],"copy_or_adapt":"BLOCKED_PENDING_REVIEW","license_authenticity":"DECLARED_PINNED_REVIEW"}

def build_plan(c,ident,repository,candidate,lab,baseline):
    reg.require(reg.sha40(baseline),"exact baseline required")
    plan=dict(schema=1,id=ident,peer="foundation",hypothesis=c["hypothesis"],
              scope=c["id"]+"; "+c["title"]+"; proposed fixture; audit existing first; "+c["gap"],
              sources=c["refs"]+c["ideas"],repository=repository,candidate_sha=candidate,lab_sha=lab,baseline_sha=baseline,
              kind="fixture",workload=dict(environment="isolated offline fixture; fix parameters before execution",
              scenario=c["scenario"],seed=42,ticks=None,command_hash=None,authorization="offline_only"),criteria=c["criteria"])
    reg.validate_plan(plan)
    return plan

def validate_portfolio(p,catalog=None,pin=None):
    reg.exact(p,"schema foundation_commit game_commit sources cards")
    reg.require(p["schema"]==1 and reg.sha40(p["foundation_commit"]) and reg.sha40(p["game_commit"]),"portfolio revision")
    if pin is not None:
        reg.require(p["foundation_commit"]==pin["commit"],"Foundation revision mismatch")
    reg.require(isinstance(p["sources"],list) and 0<len(p["sources"])<=200,"sources")
    reg.require(isinstance(p["cards"],list) and 0<len(p["cards"])<=200,"cards")
    refs={}
    for s in p["sources"]:
        source_gate(s)
        reg.require(s["id"] not in refs,"duplicate source")
        refs[s["id"]]=s
        if catalog is not None:
            row=catalog["references"].get(s["id"],{})
            reg.require(row.get("url","").rstrip("/")=="https://github.com/"+s["repo"],"source catalog link")
    ids=set()
    for c in p["cards"]:
        reg.exact(c,"id title refs ideas domain method complexity benefit cost risk coverage existing gap hypothesis scenario criteria reuse")
        reg.require(reg.match(c["id"],r"RES-[0-9]{3,}") and c["id"] not in ids,"card ID")
        ids.add(c["id"])
        reg.require(c["domain"] in DOMAINS and c["coverage"] in {"UNKNOWN","PARTIAL","CANDIDATE_GAP"},"domain/coverage")
        reg.require(c["reuse"]=="CONCEPT_ONLY","copy/adapt blocked")
        reg.require(all(reg.nonempty(c[k]) for k in ("title","method","complexity","existing","gap","hypothesis","scenario")),"card text")
        for k in ("benefit","cost","risk"):
            reg.require(type(c[k]) is int and 1<=c[k]<=5,"ordinal estimate")
        reg.require(isinstance(c["refs"],list) and bool(c["refs"]) and len(set(c["refs"]))==len(c["refs"]) and set(c["refs"])<=set(refs),"card sources")
        reg.require(isinstance(c["ideas"],list) and bool(c["ideas"]) and len(set(c["ideas"]))==len(c["ideas"]) and all(reg.match(i,r"IDEA-[0-9]{3,}") for i in c["ideas"]),"idea IDs")
        if catalog is not None:
            for i in c["ideas"]:
                row=catalog["possibilities"].get(i,{})
                reg.require(row.get("department")==c["domain"] and bool(set(c["refs"])&set(row.get("references",[]))),"idea/source/domain link")
        build_plan(c,"EXP-VALIDATE-001","example/synthetic","a"*40,"b"*40,"c"*40)
    return {"cards":len(ids),"sources":len(refs),"foundation_links":"MATCH" if catalog is not None else "NOT_RUN","research_status":"PROPOSED","promotion":"NOT_AUTHORIZED"}

def propose(p,card_id,ident,repository,candidate,lab,baseline,catalog,pin):
    reg.require(catalog is not None and pin is not None,"Foundation snapshot required")
    validate_portfolio(p,catalog,pin)
    c=next((x for x in p["cards"] if x["id"]==card_id),None)
    reg.require(c is not None,"unknown card")
    return build_plan(c,ident,repository,candidate,lab,baseline)

def rank(p):
    validate_portfolio(p)
    return sorted([{"id":c["id"],"title":c["title"],"domain":c["domain"],"score":2*c["benefit"]-c["cost"]-c["risk"],
                    "benefit":c["benefit"],"cost":c["cost"],"risk":c["risk"],"coverage":c["coverage"],"complexity":c["complexity"],
                    "status":"AUDIT_EXISTING_FIRST"} for c in p["cards"]],key=lambda x:(-x["score"],x["id"]))

def search_catalog(catalog,query):
    reg.require(reg.nonempty(query) and len(query)<=200,"query length")
    tokens=query.casefold().split()
    return [{"type":kind,"id":i,"name":row["name"]} for kind,rows in catalog.items()
            for i,row in rows.items() if all(t in (i+" "+json.dumps(row,ensure_ascii=False)).casefold() for t in tokens)]

def public_discover(provider,query,fetch=None):
    reg.require(provider in {"github","crossref"} and reg.nonempty(query) and len(query)<=200,"public query")
    params=urllib.parse.urlencode({"q":query,"per_page":5} if provider=="github" else {"query.bibliographic":query,"rows":5})
    url=("https://api.github.com/search/repositories?" if provider=="github" else "https://api.crossref.org/works?")+params
    if fetch is None:
        def fetch(url):
            req=urllib.request.Request(url,headers={"User-Agent":"APEX-Engineering-Lab/0.3","Accept":"application/json"})
            with urllib.request.build_opener(NoRedirect()).open(req,timeout=10) as response:
                raw=response.read(reg.LIMIT+1)
            reg.require(len(raw)<=reg.LIMIT,"response too large")
            return json.loads(raw,object_pairs_hook=reg.no_duplicates)
    data=fetch(url)
    if provider=="github":
        rows=[{"name":x.get("full_name"),"url":x.get("html_url"),"license_hint":(x.get("license") or {}).get("spdx_id")} for x in data["items"][:5]]
    else:
        rows=[{"title":(x.get("title") or [""])[0],"doi":x.get("DOI"),"url":x.get("URL")} for x in data["message"]["items"][:5]]
    return {"provider":provider,"results":rows,"status":"DISCOVERY_ONLY","reuse":"BLOCKED_PENDING_REVIEW"}
