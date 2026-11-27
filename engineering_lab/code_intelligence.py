"""Interpret existing diagnostic outputs. No independent dependency parser or runtime gate."""
from collections import Counter, defaultdict, deque
from pathlib import PurePosixPath
from . import registry as reg

RULES={"APX001":"file_size","APX002":"function_size","APX003":"structural_complexity",
       "APX004":"nesting","APX005":"parameters","APX101":"nested_loops",
       "APX102":"loop_progress","APX103":"hot_operation","APX104":"node_lookup"}

def script_path(p):
    return isinstance(p,str) and p.startswith("scripts/") and p.endswith(".gd") and "\\" not in p and all(x not in ("",".","..") for x in p.split("/"))

def graph_check(a):
    reg.require(a.get("schema")==1 and a.get("complete") is True and a.get("scope")=="tracked scripts/**/*.gd" and a.get("errors")==[], "incomplete architecture report")
    g=a["edges"]
    reg.require(isinstance(g,dict) and 0<len(g)<=5000 and a["scripts"]==len(g),"graph size")
    for p,targets in g.items():
        reg.require(script_path(p) and isinstance(targets,list) and all(isinstance(t,str) and t in g for t in targets) and len(targets)==len(set(targets)), "invalid graph edge")
    reg.require(a["edge_count"]==sum(map(len,g.values())),"edge count")
    for component in a["cyclic_components"]:
        reg.require(isinstance(component,list) and bool(component) and len(set(component))==len(component) and all(p in g for p in component),"cycle members")
    reg.require(isinstance(a["coverage"]["registered_fixture_count"],int) and isinstance(a["coverage"]["missing_registered_fixtures"],list),"fixture inventory")
    for x in a["long_function_candidates"]:
        reg.require(x["file"] in g and type(x["line"]) is int and x["line"]>0 and type(x["physical_span"]) is int and x["physical_span"]>0,"function span")
    return g

def analyzer_check(report,sha,n,blob,g):
    reg.require(report.get("schema_version")==1 and report.get("analyzer_version")=="0.2.1" and report.get("complete") is True and report.get("errors")==[] and report.get("symlink_files_skipped")==0,"incomplete analyzer")
    p=report["provenance"]
    reg.require(p["game_sha"]==sha and p["analyzer_blob"]==blob and p["expected_scripts"]==n and p["execution"]=="PASS" and p["scope"]=="scripts/**/*.gd" and report["files_analyzed"]==n,"analyzer provenance mismatch")
    out=defaultdict(list)
    for d in report["diagnostics"]:
        path="scripts/"+d["file"]
        reg.require(path in g and d["certainty"] in {"confirmed","heuristic"} and d["severity"] in {"low","medium","high"} and type(d["line"]) is int and d["line"]>0 and reg.nonempty(d["rule"]),"analyzer diagnostic")
        out[path].append({"rule":d["rule"],"category":RULES.get(d["rule"],"unclassified"),
                          "line":d["line"],"function":d.get("function"),"certainty":d["certainty"],"severity":d["severity"]})
    return out

def reverse_graph(g):
    rev={p:[] for p in g}
    for src,targets in g.items():
        for target in targets: rev[target].append(src)
    return {p:sorted(v) for p,v in rev.items()}

def impact(g,changed):
    reg.require(isinstance(changed,list) and len(changed)<=5000 and all(script_path(p) for p in changed),"changed paths must be tracked script paths")
    rev=reverse_graph(g)
    known=set(changed)&set(g)
    visited=set(known)
    queue=deque(sorted(known))
    while queue:
        for p in rev[queue.popleft()]:
            if p not in visited: visited.add(p); queue.append(p)
    return {"changed":sorted(known),"transitive_dependents":sorted(visited-known),
            "unmapped":sorted(set(changed)-known),"status":"REVIEW_REQUIRED",
            "coverage":"literal reverse edges only; no runtime or scene dependencies"}

def review(bundle,changed=None,analyzer=None):
    reg.exact(bundle,"schema game_sha architecture_blob architecture function_inventory")
    reg.require(bundle["schema"]==1 and reg.sha40(bundle["game_sha"]) and reg.sha40(bundle["architecture_blob"]),"bundle revision")
    a=bundle["architecture"]
    g=graph_check(a)
    inv=bundle["function_inventory"]
    reg.require(inv["scope"]=="top-level lexical candidates" and inv["scripts"]==len(g),"function inventory mismatch")
    for group in inv["duplicate_body_candidates"]:
        reg.require(reg.sha64(group["sha256"]) and len(group["members"])>=2,"duplicate group")
        for x in group["members"]: reg.require(x["file"] in g and reg.nonempty(x["function"]) and type(x["line"]) is int and x["line"]>0,"duplicate member")
    for x in inv["single_mention_candidates"]:
        reg.require(x["file"] in g and reg.nonempty(x["function"]) and type(x["line"]) is int and x["line"]>0,"single mention")
    rev=reverse_graph(g)
    diagnostics=analyzer_check(analyzer,bundle["game_sha"],len(g),"29a9c39e061b89f9e15126b265d880a40f3155a9",g) if analyzer is not None else {}
    cycles={p for group in a["cyclic_components"] for p in group}
    spans=Counter(x["file"] for x in a["long_function_candidates"])
    duplicates=Counter(x["file"] for group in inv["duplicate_body_candidates"] for x in group["members"])
    rows=[]
    for p in g:
        counts=Counter(x["category"] for x in diagnostics.get(p,[]))
        # Scores are triage estimates, not actual latency or confirmed defects.
        structural=sum(counts[k] for k in ("structural_complexity","nesting","function_size","file_size","parameters"))
        hot=sum(counts[k] for k in ("nested_loops","loop_progress","hot_operation","node_lookup"))
        score=len(rev[p])*2+len(g[p])+3*int(p in cycles)+min(spans[p],10)+min(duplicates[p],10)+min(structural,10)+min(hot,10)
        rows.append({"file":p,"score":score,"inbound":len(rev[p]),"outbound":len(g[p]),"cycle_candidate":p in cycles,
                     "large_function_candidates":spans[p],"duplicate_body_candidates":duplicates[p],
                     "complexity_diagnostics":structural,"hot_operation_hypotheses":hot,
                     "native_candidate":"REQUIRES_MEASURED_PROFILE_AND_EQUIVALENCE" if hot or structural or spans[p] else "NO_STATIC_SIGNAL",
                     "regression_priority":"REVIEW_DEPENDENTS_AND_EXISTING_FIXTURES" if score else "REVIEW_RUNTIME_ENTRYPOINTS"})
    rows.sort(key=lambda x:(-x["score"],x["file"]))
    return {"schema":1,"game_sha":bundle["game_sha"],"bundle_sha256":reg.digest(bundle),
            "architecture_blob":bundle["architecture_blob"],"scripts":len(g),"literal_edges":a["edge_count"],
            "cycles":a["cyclic_components"],"zero_inbound_candidates":sorted(p for p in g if not rev[p]),
            "duplicate_body_candidates":inv["duplicate_body_candidates"],"single_mention_candidates":inv["single_mention_candidates"],
            "function_inventory_counts":inv["counts"],"ranked_risks":rows,
            "analyzer_status":"IMPORTED_MATCHING_METADATA" if analyzer is not None else "NOT_RUN",
            "analyzer_rule_counts":dict(sorted(Counter(x["rule"] for ds in diagnostics.values() for x in ds).items())),
            "fixture_inventory":a["coverage"],"impact":impact(g,changed or []),"runtime_profile":"NOT_RUN",
            "native_promotion":"NOT_AUTHORIZED","gameplay_validation":"NOT_RUN","status":"DIAGNOSTIC_ONLY",
            "limitations":["Literal graph omits dynamic/class_name/UID/scene dependencies.",
                           "Exact dedented body similarity and single lexical mentions are not semantic duplication or dead code.",
                           "Static metrics are not CPU measurements; no automatic deletion, patch, or C++ migration.",
                           "Imported report binding is local metadata, not authenticated authorship."]}

def compare(before,after):
    b=review(before); a=review(after)
    reg.require(b["architecture_blob"]==a["architecture_blob"],"different graph producer; no comparable diff")
    gb=before["architecture"]["edges"]; ga=after["architecture"]["edges"]
    eb={(p,t) for p,ts in gb.items() for t in ts}; ea={(p,t) for p,ts in ga.items() for t in ts}
    return {"baseline_sha":b["game_sha"],"candidate_sha":a["game_sha"],"added_scripts":sorted(set(ga)-set(gb)),
            "removed_scripts":sorted(set(gb)-set(ga)),"added_literal_edges":sorted(ea-eb),"removed_literal_edges":sorted(eb-ea),
            "baseline_cycles":b["cycles"],"candidate_cycles":a["cycles"],"status":"REVIEW_REQUIRED",
            "regression":"NOT_ESTABLISHED","promotion":"NOT_AUTHORIZED"}
