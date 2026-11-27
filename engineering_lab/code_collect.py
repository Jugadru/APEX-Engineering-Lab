"""Explicit collector: reuse reviewed existing public architecture tool, plus narrow lexical inventory."""
import bisect
from collections import Counter, defaultdict
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import textwrap
from . import registry as reg
from .research import git_blob
from .code_intelligence import script_path

def git(root,*args):
    return subprocess.check_output(["git","-C",str(root),*args],timeout=30)

def function_inventory(sources,tokens):
    mentions=Counter()
    functions=[]
    groups=defaultdict(list)
    for path,source in sorted(sources.items()):
        starts=[0]+[m.end() for m in re.finditer("\n",source)]
        first={}
        for kind,value,offset in tokens(source):
            if kind=="word": mentions[value]+=1
            line=bisect.bisect_right(starts,offset)
            first.setdefault(line,(kind,value,offset))
        top=[]
        for line,(_,_,offset) in sorted(first.items()):
            if offset==starts[line-1]:
                match=re.match(r"(?:static\s+)?func\s+([A-Za-z_]\w*)\s*\(",source[offset:])
                top.append((line,match[1] if match else None))
        for i,(line,name) in enumerate(top):
            if name is None: continue
            end=top[i+1][0] if i+1<len(top) else len(starts)+1
            row={"file":path,"function":name,"line":line}
            functions.append(row)
            # Only single-line signatures with a colon; skip multiline signatures and small bodies.
            if not source[starts[line-1]:starts[line] if line<len(starts) else len(source)].rstrip().endswith(":"): continue
            body=textwrap.dedent("".join(source.splitlines(keepends=True)[line:end-1])).strip()
            if len([s for s in body.splitlines() if s.strip() and not s.lstrip().startswith("#")])>=5:
                groups[reg.checksum(body.encode())].append(row)
    duplicates=[{"sha256":h,"members":rows} for h,rows in sorted(groups.items()) if len(rows)>1]
    single=[r for r in functions if not r["function"].startswith("_") and mentions[r["function"]]==1]
    return {"scope":"top-level lexical candidates","scripts":len(sources),
            "duplicate_body_candidates":duplicates[:200],"single_mention_candidates":single[:200],
            "counts":{"functions":len(functions),"duplicate_groups":len(duplicates),"single_mentions":len(single),
                      "duplicate_groups_truncated":len(duplicates)>200,"single_mentions_truncated":len(single)>200}}

def collect(root,pin):
    root=root.resolve()
    game=pin["game"]
    sha=game["commit"]
    reg.require(reg.sha40(sha) and git(root,"rev-parse","HEAD").decode().strip()==sha,"wrong game checkout")
    reg.require(not git(root,"status","--porcelain","--untracked-files=all"),"checkout must be clean")
    path=root/"tools/apex_lab_architecture.py"
    reg.require(git_blob(reg.bounded_bytes(path))==game["architecture_blob"],"architecture tool blob mismatch")
    spec=importlib.util.spec_from_file_location("apex_reviewed_architecture",path)
    tool=importlib.util.module_from_spec(spec)
    sys.path.insert(0,str(root/"tools"))
    try:
        spec.loader.exec_module(tool)
        names=sorted(p.decode() for p in git(root,"ls-files","-z","--","scripts").split(b"\0") if p and script_path(p.decode()))
        reg.require(len(names)==game["scripts"],"script count mismatch")
        architecture=tool.scan(root,names)
        architecture["coverage"]=tool.coverage(root)
        reg.require(architecture["complete"] is True,"upstream scan incomplete")
        sources={p:reg.bounded_bytes(root/p).decode("utf-8-sig") for p in names}
        inv=function_inventory(sources,tool.tokens)
    finally:
        sys.path.pop(0)
    return {"schema":1,"game_sha":sha,"architecture_blob":game["architecture_blob"],"architecture":architecture,"function_inventory":inv}
