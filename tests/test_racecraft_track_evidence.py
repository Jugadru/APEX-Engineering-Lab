import unittest
from engineering_lab import racecraft_track_evidence as t
def track(code="MON"):
    return dict(code=code,lap_km=3.34,geometry_quality="licensed_geojson_reference",geometry_source="synthetic test reference",
                points=[[0,0],[1,0],[1,1],[0,0]])
class TrackEvidenceTests(unittest.TestCase):
    def test_units_and_no_certification(self):
        r=t.track_summary(track())
        self.assertEqual(r["lap_length_mm"],3340000)
        self.assertFalse(r["historical_layout_verified"]);self.assertFalse(r["real_telemetry"])
    def test_open(self):
        with self.assertRaises(ValueError):t.track_summary(dict(track(),points=[[0,0],[1,0],[1,1],[0,1]]))
    def test_duplicate_segment(self):
        with self.assertRaises(ValueError):t.track_summary(dict(track(),points=[[0,0],[1,0],[1,0],[1,1],[0,0]]))
    def test_quality(self):
        with self.assertRaises(ValueError):t.track_summary(dict(track(),geometry_quality="official"))
    def test_roster(self):
        s=dict(season=2012,tracks=[track(x) for x in sorted(t.CODES)])
        p=dict(season=2012,tracks={x:{} for x in t.CODES},note="synthetic")
        r=t.audit(s,p,p)
        self.assertEqual(len(r["tracks"]),20)
        self.assertEqual(r["historical_calibration"],"BLOCKED_NO_INDEPENDENT_MEASUREMENTS")
        s["tracks"][0]=s["tracks"][1]
        with self.assertRaises(ValueError):t.audit(s,p,p)
if __name__=="__main__":unittest.main()
