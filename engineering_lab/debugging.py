"""Investigation records: immutable local inputs, explicit next actions, no execution."""
from . import registry as reg
from .private_metadata import REPOS

DOMAINS={"physics","racecraft","strategy","simulation","performance","quality","architecture","presentation","infrastructure","career"}
KINDS={"observed_failure","static_signal","user_report","synthetic"}
def case_id(value):
    reg.require(reg.match(value,r"BUG-[A-Z0-9-]{1,60}"),"invalid investigation ID")
    return value
def validate_case(c):
    reg.exact(c,"schema id repository sha domain kind title symptom expected observed evidence limitations")
    reg.require(type(c["schema"]) is int and c["schema"]==1,"schema")
    case_id(c["id"])
    reg.require((c["repository"] in REPOS or c["repository"]=="example/synthetic" and c["kind"]=="synthetic") and reg.sha40(c["sha"]),"target revision")
    reg.require(c["domain"] in DOMAINS and c["kind"] in KINDS,"classification")
    for k in ("title","symptom","expected","observed","limitations"): reg.require(reg.nonempty(c[k]),"case text")
    reg.require(isinstance(c["evidence"],list) and len(c["evidence"])<=20,"evidence list")
    if c["kind"]=="observed_failure": reg.require(bool(c["evidence"]),"observed failure needs evidence")
    for e in c["evidence"]:
        reg.exact(e,"file sha256")
        reg.require(reg.match(e["file"],r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}") and reg.sha64(e["sha256"]),"evidence locator")
    reg.require(len({e["file"] for e in c["evidence"]})==len(c["evidence"]),"duplicate evidence")
    return reg.digest(c)
def verify_bytes(root,items):
    if items:
        folder=root/"artifacts"
        reg.require(folder.is_dir() and not folder.is_symlink(),"artifact directory")
        for e in items:
            reg.require(reg.checksum(reg.bounded_bytes(folder/e["file"]))==e["sha256"],"evidence bytes mismatch")
def open_case(root,c):
    reg.valid_root(root)
    validate_case(c); verify_bytes(root,c["evidence"])
    reg.publish_once(root/(c["id"]+".case.json"),c)
    return inspect_case(root,c["id"])
def load_case(root,ident):
    reg.valid_root(root); case_id(ident)
    c=reg.read_json(root/(ident+".case.json"))
    reg.require(c["id"]==ident,"case filename mismatch")
    validate_case(c); verify_bytes(root,c["evidence"])
    return c
def inspect_case(root,ident):
    c=load_case(root,ident)
    return {"id":ident,"case_sha256":reg.digest(c),"sha":c["sha"],"kind":c["kind"],"domain":c["domain"],
            "state":"OPEN","root_cause":"NOT_ESTABLISHED","reproduction":"NOT_RUN",
            "hypothesis_budget":2,"candidate_attempt_budget":1,"execution_budget_minutes":15,
            "next_action":"Review original evidence and locate existing fixture before proposing a fix.",
            "authenticity":"NOT_VERIFIED","promotion":"NOT_AUTHORIZED"}
