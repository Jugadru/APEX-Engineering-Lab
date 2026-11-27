import copy
import re
import unittest
from engineering_lab import code_intelligence as ci, code_collect as co
A="scripts/a.gd"; B="scripts/b.gd"; C="scripts/c.gd"
def fixture():
    return {"schema":1,"game_sha":"a"*40,"architecture_blob":"b"*40,
            "architecture":{"schema":1,"complete":True,"scope":"tracked scripts/**/*.gd","scripts":3,
                "edges":{A:[B],B:[C],C:[]},"edge_count":2,"cyclic_components":[],"errors":[],
                "long_function_candidates":[{"file":B,"function":"f","line":2,"physical_span":90}],
                "coverage":{"registered_fixture_count":2,"missing_registered_fixtures":[]}},
            "function_inventory":{"scope":"top-level lexical candidates","scripts":3,
                "duplicate_body_candidates":[],"single_mention_candidates":[],"counts":{}}}
def analyzer():
    return {"schema_version":1,"analyzer_version":"0.2.1","complete":True,"errors":[],"symlink_files_skipped":0,
            "files_analyzed":3,"provenance":{"game_sha":"a"*40,"analyzer_blob":"29a9c39e061b89f9e15126b265d880a40f3155a9",
            "expected_scripts":3,"scope":"scripts/**/*.gd","execution":"PASS"},
            "diagnostics":[{"file":"b.gd","line":2,"function":"f","rule":"APX101","certainty":"heuristic","severity":"medium"}]}
class CodeTests(unittest.TestCase):
    def test_review(self):
        r=ci.review(fixture())
        self.assertEqual(r["literal_edges"],2)
        self.assertEqual(r["zero_inbound_candidates"],[A])
        self.assertEqual(r["analyzer_status"],"NOT_RUN")
        self.assertEqual(r["native_promotion"],"NOT_AUTHORIZED")
    def test_transitive(self):
        self.assertEqual(ci.review(fixture(),[C])["impact"]["transitive_dependents"],[A,B])
    def test_unknown(self):
        self.assertEqual(ci.review(fixture(),["scripts/unknown.gd"])["impact"]["unmapped"],["scripts/unknown.gd"])
    def test_cycle_terminates(self):
        f=fixture(); f["architecture"]["edges"][C]=[A]; f["architecture"]["edge_count"]=3
        f["architecture"]["cyclic_components"]=[[A,B,C]]
        self.assertEqual(ci.review(f,[C])["impact"]["transitive_dependents"],[A,B])
    def test_incomplete(self):
        f=fixture(); f["architecture"]["complete"]=False
        with self.assertRaises(ValueError): ci.review(f)
    def test_invalid_edge(self):
        f=fixture(); f["architecture"]["edges"][A]=["scripts/../bad.gd"]
        with self.assertRaises(ValueError): ci.review(f)
    def test_wrong_count(self):
        f=fixture(); f["architecture"]["edge_count"]=99
        with self.assertRaises(ValueError): ci.review(f)
    def test_analyzer(self):
        r=ci.review(fixture(),analyzer=analyzer())
        self.assertEqual(r["analyzer_rule_counts"],{"APX101":1})
        self.assertEqual(r["runtime_profile"],"NOT_RUN")
        self.assertEqual(r["analyzer_status"],"IMPORTED_MATCHING_METADATA")
    def test_wrong_analyzer_sha(self):
        a=analyzer(); a["provenance"]["game_sha"]="c"*40
        with self.assertRaises(ValueError): ci.review(fixture(),analyzer=a)
    def test_wrong_analyzer_blob(self):
        a=analyzer(); a["provenance"]["analyzer_blob"]="c"*40
        with self.assertRaises(ValueError): ci.review(fixture(),analyzer=a)
    def test_analyzer_incomplete(self):
        a=analyzer(); a["complete"]=False
        with self.assertRaises(ValueError): ci.review(fixture(),analyzer=a)
    def test_diff(self):
        b=fixture(); a=copy.deepcopy(b); a["game_sha"]="d"*40
        a["architecture"]["edges"][A]=[C]
        r=ci.compare(b,a)
        self.assertEqual(r["added_literal_edges"],[(A,C)])
        self.assertEqual(r["regression"],"NOT_ESTABLISHED")
    def test_diff_producer(self):
        a=fixture(); a["architecture_blob"]="c"*40
        with self.assertRaises(ValueError): ci.compare(fixture(),a)
    def test_duplicate_and_single(self):
        # Mock lexical tokenizer, not a replacement for upstream tokenizer.
        def tokens(s):
            for m in re.finditer(r"[A-Za-z_]\w*|[^\s]",s):
                yield ("word" if m.group()[0].isalpha() or m.group()[0]=="_" else "other",m.group(),m.start())
        body=":\n    x = 1\n    y = 2\n    z = 3\n    w = 4\n    return x+y+z+w\n"
        out=co.function_inventory({A:"func alpha()"+body,B:"func beta()"+body},tokens)
        self.assertEqual(out["counts"]["duplicate_groups"],1)
        self.assertEqual(out["counts"]["single_mentions"],2)
    def test_ranking_deterministic(self):
        self.assertEqual(ci.review(fixture()),ci.review(fixture()))
if __name__=="__main__": unittest.main()
