import tempfile
import unittest
from pathlib import Path
from engineering_lab import experimental as e, exp_reports as reports, registry as reg
class ReportTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup); self.root=Path(t.name)
    def create(self,name="ordered_commands",ident="EXP-REPORT-001",sha="a"*40):
        p=self.root/ident; e.run(p,name,ident,sha); return p
    def test_verified(self):
        p=self.create(); r=reports.report(p,"EXP-REPORT-001")
        self.assertEqual(r["reported_status"],"PASS")
        self.assertEqual(r["artifact_bytes"],"MATCH")
        self.assertEqual(r["scientific_validation"],"NOT_PERFORMED")
    def test_missing_result(self):
        p=self.create(); (p/"EXP-REPORT-001.result.json").unlink()
        self.assertEqual(reports.report(p,"EXP-REPORT-001")["reported_status"],"NOT_RUN")
    def test_config_tamper(self):
        p=self.create(); (p/"configuration.json").write_text("{}")
        with self.assertRaises(ValueError): reports.report(p,"EXP-REPORT-001")
    def test_artifact_tamper(self):
        p=self.create(); (p/"artifacts/observations.json").write_text("{}")
        with self.assertRaises(ValueError): reports.report(p,"EXP-REPORT-001")
    def test_observation_binding(self):
        p=self.create(); a=p/"artifacts/observations.json"; x=reg.read_json(a)
        x["revision"]="b"*40; a.write_bytes(reg.canonical(x))
        q=p/"EXP-REPORT-001.result.json"; r=reg.read_json(q); r["evidence"][0]["sha256"]=reg.checksum(a.read_bytes()); q.write_bytes(reg.canonical(r))
        with self.assertRaises(ValueError): reports.report(p,"EXP-REPORT-001")
    def test_mixed_revision(self):
        p=self.create(); q=self.create("spatial_neighbors","EXP-REPORT-002","b"*40)
        with self.assertRaises(ValueError): reports.suite([(p,"EXP-REPORT-001"),(q,"EXP-REPORT-002")])
    def test_duplicates(self):
        p=self.create()
        with self.assertRaises(ValueError): reports.suite([(p,"EXP-REPORT-001"),(p,"EXP-REPORT-001")])
    def test_suite_and_markdown(self):
        p=self.create(); q=self.create("spatial_neighbors","EXP-REPORT-002")
        s=reports.suite([(p,"EXP-REPORT-001"),(q,"EXP-REPORT-002")])
        self.assertEqual(s["counts"]["PASS"],2)
        self.assertIn("neighbor_mismatches",reports.markdown(s))
        self.assertEqual(s["promotion"],"NOT_AUTHORIZED")
    def test_incomplete_suite(self):
        p=self.create(); (p/"EXP-REPORT-001.result.json").unlink()
        self.assertEqual(reports.suite([(p,"EXP-REPORT-001")])["reported_status"],"INCONCLUSIVE")
    def test_exploratory_preserved(self):
        p=self.create("pit_cost_comparison")
        r=reports.report(p,"EXP-REPORT-001")
        self.assertIn("regret_delta_s",r["observations"])
        self.assertNotIn("regret_delta_s",{x["metric"] for x in r["metrics"]})
if __name__=="__main__": unittest.main()
