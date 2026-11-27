"""Join existing evidence without claiming scientific or runtime approval."""
from . import registry as reg
from . import code_intelligence as ci

def summary_check(s,game_sha,n,blob):
    reg.exact(s,"game_sha analyzer_blob status scripts expected_scripts rules certainty error_count")
    reg.require(s["game_sha"]==game_sha and s["analyzer_blob"]==blob and s["status"]=="PASS"
                and s["scripts"]==n and s["expected_scripts"]==n and s["error_count"]==0,"analyzer summary binding")
    rules=s["rules"]; certainty=s["certainty"]
    reg.require(isinstance(rules,dict) and isinstance(certainty,dict) and set(certainty)<={"confirmed","heuristic"}
                and all(type(v) is int and v>=0 for v in list(rules.values())+list(certainty.values()))
                and all(reg.match(k,r"APX[0-9]{3}") for k in rules)
                and sum(rules.values())==sum(certainty.values()),"summary counts")
    return {"scope":"AGGREGATE_ONLY","status":"IMPORTED_SUMMARY_METADATA_MATCH","rules":rules,"certainty":certainty,
            "diagnostic_count":sum(rules.values()),"per_file_attribution":"NOT_AVAILABLE"}

def profile_check(envelope,sha):
    reg.exact(envelope,"schema game_sha report")
    reg.require(envelope["schema"]==1 and envelope["game_sha"]==sha,"profile revision")
    p=envelope["report"]
    reg.require(p.get("status")=="PASS" and p.get("track")=="LAB" and p.get("cases")==4
                and type(p.get("ticks_per_run")) is int and p["ticks_per_run"]>0
                and p.get("total_ticks")==4*p["ticks_per_run"],"profile workload")
    obs=p["observations"]
    reg.require(isinstance(obs,list) and len(obs)==4,"profile observations")
    weather=set()
    for r in obs:
        reg.require(reg.nonempty(r["weather"]) and type(r["repeat"]) is int and r["repeat"] in (1,2),"profile case")
        weather.add((r["weather"],r["repeat"]))
        for k in ("mean_us","p95_us","end_over_start_ratio","simulated_seconds_per_wall_second"):
            reg.require(reg.numeric(r[k]) and r[k]>0,"profile metric")
        reg.require(type(r["peak_static_bytes"]) is int and r["peak_static_bytes"]>=0,"memory")
    reg.require(len(weather)==4 and len({x[0] for x in weather})==2 and all({(w,1),(w,2)}<=weather for w,_ in weather),"profile coverage")
    h=p["weather_hashes"]
    reg.require(isinstance(h,dict) and set(h)=={w for w,_ in weather} and all(reg.sha64(v) for v in h.values()),"profile hashes")
    return {"status":"IMPORTED_HEADLESS_AGGREGATE","observations":obs,"function_profile":"NOT_RUN","fps":"NOT_RUN",
            "limitations":"Producer report imported; no measured per-function attribution or paired comparison."}

def correlation_check(c,sha):
    reg.require(c.get("schema")==1 and c.get("head")==sha and reg.sha40(c.get("base")),"correlation revision")
    reg.require(c.get("state") in {"FAILURE_EVIDENCE","NO_CASE_FAILURE_OBSERVED"} and isinstance(c.get("failures"),list)
                and isinstance(c.get("planned_not_executed"),list),"correlation format")
    reg.require(bool(c["failures"])==(c["state"]=="FAILURE_EVIDENCE"),"correlation state")
    for r in c["failures"]:
        reg.require(r.get("status") in {"FAIL","BLOCKED"} and r.get("root_cause")=="NOT_ESTABLISHED"
                    and reg.nonempty(r.get("case")) and isinstance(r.get("candidates"),list),"failure observation")
    return {"status":"IMPORTED_CORRELATION","failures":[{"case":r["case"],"status":r["status"],"candidate_count":r.get("candidate_count"),
              "root_cause":"NOT_ESTABLISHED"} for r in c["failures"]],
            "planned_not_executed":c["planned_not_executed"],"gameplay_validation":"NOT_RUN"}

def join(bundle,summary=None,profile=None,correlation=None):
    base=ci.review(bundle)
    sha=base["game_sha"]
    return {"game_sha":sha,"bundle_sha256":base["bundle_sha256"],"architecture":base["status"],
            "analyzer":summary_check(summary,sha,base["scripts"],"29a9c39e061b89f9e15126b265d880a40f3155a9") if summary is not None else {"status":"NOT_RUN"},
            "profile":profile_check(profile,sha) if profile is not None else {"status":"NOT_RUN"},
            "correlation":correlation_check(correlation,sha) if correlation is not None else {"status":"NOT_RUN"},
            "function_profile":"NOT_RUN","native_promotion":"NOT_AUTHORIZED","gameplay_validation":"NOT_RUN",
            "authenticity":"LOCAL_IMPORTED_METADATA_ONLY"}
