import unittest
from engineering_lab import racecraft_core as r, racecraft_space as s, experimental as e
class SpaceTests(unittest.TestCase):
    def awareness(self,rows,width=5000):
        return s.Awareness(r.Snapshot.from_rows(0,5000000,width,rows))
    def test_wrap_front(self):
        a=self.awareness([r.row(1,4998000,0,50000),r.row(2,6000,0,40000)])
        front=a.leaders(1,10000)["front"]
        self.assertEqual(front["gap_mm"],8000)
        self.assertEqual(front["ttc_ms"],270)
    def test_no_closing(self):
        a=self.awareness([r.row(1,0,0,40000),r.row(2,8000,0,50000)])
        self.assertIsNone(a.nearby(1,10000)[0]["ttc_ms"])
    def test_lateral_separation(self):
        a=self.awareness([r.row(1,0,0),r.row(2,4000,3000)])
        self.assertIsNone(a.leaders(1,10000)["front"])
        self.assertFalse(a.clearance(1,3000)["clear"])
        self.assertTrue(a.clearance(1,-3000)["clear"])
    def test_exact_contact_is_blocked(self):
        a=self.awareness([r.row(1,0,0),r.row(2,5300,2100)])
        self.assertEqual(a.clearance(1,0)["blockers"],[2])
    def test_edge(self):
        a=self.awareness([r.row(1,0,0)])
        self.assertTrue(a.clearance(1,3800)["clear"])
        self.assertTrue(a.clearance(1,3801)["edge"])
    def test_initial_overlap(self):
        a=self.awareness([r.row(1,0,0),r.row(2,0,0)])
        self.assertEqual(a.leaders(1,0)["coincident"],[2])
        self.assertFalse(a.clearance(1,3000)["clear"])
    def test_inactive(self):
        a=self.awareness([r.row(1,0,0),r.row(2,0,0,active=False)])
        self.assertTrue(a.clearance(1,0)["clear"])
        with self.assertRaises(ValueError): a.nearby(2,1000)
    def test_radius_bounds(self):
        a=self.awareness([r.row(1,0)])
        for rad in (-1,2500001,True):
            with self.assertRaises(ValueError): a.nearby(1,rad)
    def test_fixture(self):
        q=s.evaluate(e.specs()["racecraft_spatial_awareness"]["config"])
        self.assertTrue(all(v==0 for v in q["metrics"].values()))
        self.assertEqual(q["observations"]["queries"],456)
        self.assertEqual(q["observations"]["clearance_cases"],570)
if __name__=="__main__": unittest.main()
