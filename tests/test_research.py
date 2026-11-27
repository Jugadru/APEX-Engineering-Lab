import copy
import tempfile
import unittest
from pathlib import Path
from engineering_lab import registry as reg, research as res

class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.p=reg.read_json(Path("research/portfolio.json"))
        self.pin=reg.read_json(Path("research/foundation-pin.json"))
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder=Path(tmp.name)
        self.catalog={"references":{s["id"]:{"id":s["id"],"name":s["id"],"url":"https://github.com/"+s["repo"]} for s in self.p["sources"]},"possibilities":{}}
        for c in self.p["cards"]:
            for i in c["ideas"]:
                row=self.catalog["possibilities"].setdefault(i,{"id":i,"name":i,"department":c["domain"],"references":[]})
                row["references"]=sorted(set(row["references"]+c["refs"]))
        self.synthetic_pin=copy.deepcopy(self.pin)
        for kind,name in (("references","references.json"),("possibilities","possibilities.json")):
            raw=reg.canonical({"schema":1,"entries":list(self.catalog[kind].values())})
            (self.folder/name).write_bytes(raw)
            self.synthetic_pin["files"][name]=res.git_blob(raw)
            self.synthetic_pin["counts"][kind]=len(self.catalog[kind])
    def test_portfolio(self):
        self.assertEqual(res.validate_portfolio(self.p,self.catalog,self.pin)["foundation_links"],"MATCH")
    def test_no_catalog_claim(self):
        self.assertEqual(res.validate_portfolio(self.p)["foundation_links"],"NOT_RUN")
    def test_blob_pin(self):
        self.assertEqual(res.load_foundation(self.folder,self.synthetic_pin),self.catalog)
    def test_wrong_blob(self):
        with self.assertRaises(ValueError): res.load_foundation(self.folder,self.pin)
    def test_modified_catalog(self):
        (self.folder/"references.json").write_text("{}")
        with self.assertRaises(ValueError): res.load_foundation(self.folder,self.synthetic_pin)
    def test_wrong_revision(self):
        self.p["foundation_commit"]="0"*40
        with self.assertRaises(ValueError): res.validate_portfolio(self.p,self.catalog,self.pin)
    def test_missing_idea(self):
        self.p["cards"][0]["ideas"]=["IDEA-999"]
        with self.assertRaises(ValueError): res.validate_portfolio(self.p,self.catalog,self.pin)
    def test_wrong_domain(self):
        self.p["cards"][0]["domain"]="strategy"
        with self.assertRaises(ValueError): res.validate_portfolio(self.p,self.catalog,self.pin)
    def test_bad_source_link(self):
        self.catalog["references"]["REF-105"]["url"]="https://example.org"
        with self.assertRaises(ValueError): res.validate_portfolio(self.p,self.catalog,self.pin)
    def test_copy_blocked(self):
        self.assertEqual(res.source_gate(self.p["sources"][0])["copy_or_adapt"],"BLOCKED_PENDING_REVIEW")
        self.p["sources"][0]["reuse"]="COPY"
        with self.assertRaises(ValueError): res.validate_portfolio(self.p)
    def test_bad_license_pin(self):
        self.p["sources"][0]["license_blob"]="master"
        with self.assertRaises(ValueError): res.validate_portfolio(self.p)
    def test_rank(self):
        a=res.rank(self.p)
        self.assertEqual(len(a),5)
        self.assertEqual([x["score"] for x in a],sorted([x["score"] for x in a],reverse=True))
        self.assertEqual(a,res.rank(self.p))
    def test_invalid_score(self):
        self.p["cards"][0]["benefit"]=True
        with self.assertRaises(ValueError): res.rank(self.p)
    def test_search(self):
        self.assertEqual(res.search_catalog(self.catalog,"REF-105")[0]["id"],"REF-105")
    def test_proposal_registers_v1(self):
        plan=res.propose(self.p,"RES-001","EXP-RESEARCH-001","example/synthetic","a"*40,"b"*40,"c"*40,self.catalog,self.pin)
        self.assertEqual(plan["kind"],"fixture")
        self.assertEqual(plan["baseline_sha"],"c"*40)
        self.assertEqual(len(reg.register_plan(self.folder,plan)["plan_sha256"]),64)
        self.assertFalse((self.folder/"EXP-RESEARCH-001.result.json").exists())
    def test_proposal_missing_baseline(self):
        with self.assertRaises(ValueError): res.propose(self.p,"RES-001","EXP-RESEARCH-001","example/synthetic","a"*40,"b"*40,None,self.catalog,self.pin)
    def test_proposal_missing_catalog(self):
        with self.assertRaises(ValueError): res.propose(self.p,"RES-001","EXP-RESEARCH-001","example/synthetic","a"*40,"b"*40,"c"*40,None,None)
    def test_discover_github(self):
        def fetch(url):
            self.assertTrue(url.startswith("https://api.github.com/search/repositories?"))
            self.assertIn("q=lap+time",url)
            return {"items":[{"full_name":"example/repo","html_url":"https://github.com/example/repo","license":{"spdx_id":"MIT"}}]*7}
        r=res.public_discover("github","lap time",fetch)
        self.assertEqual(len(r["results"]),5)
        self.assertEqual(r["reuse"],"BLOCKED_PENDING_REVIEW")
    def test_discover_crossref(self):
        def fetch(url):
            self.assertTrue(url.startswith("https://api.crossref.org/works?"))
            return {"message":{"items":[{"title":["Synthetic"],"DOI":"10.0/test","URL":"https://doi.org/10.0/test"}]}}
        self.assertEqual(res.public_discover("crossref","race strategy",fetch)["status"],"DISCOVERY_ONLY")
    def test_discover_reject_provider(self):
        with self.assertRaises(ValueError): res.public_discover("https://bad.example","x")

if __name__=="__main__":
    unittest.main()
