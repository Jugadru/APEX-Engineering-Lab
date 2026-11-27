import unittest
from engineering_lab import racecraft_motion as m,racecraft_core as c, experimental as e
class MotionTests(unittest.TestCase):
    def snap(self,rows,width=5000):
        return c.Snapshot.from_rows(0,5000000,width,rows)
    def test_braking_no_freeze(self):
        s=self.snap([c.row(1,100000,0,40000),c.row(2,106000,0,36000)],1500)
        r=m.resolve(s,{1:0,2:0})
        self.assertEqual(r["status"],"FEASIBLE_MODEL_STEP")
        n=r["snapshot"];self.assertGreater(n.car(1).progress_mm,100000)
        self.assertGreaterEqual(n.car(1).speed_mm_s,38400)
    def test_impossible(self):
        s=self.snap([c.row(1,100000,0,60000),c.row(2,106000,0,0)],1500)
        r=m.resolve(s,{1:0,2:0})
        self.assertIsNone(r["snapshot"]);self.assertEqual(r["status"],"NO_FEASIBLE_DISCRETE_OPTION")
    def test_initial_overlap(self):
        s=self.snap([c.row(1,100000),c.row(2,100000)])
        self.assertEqual(m.resolve(s,{1:0,2:0})["status"],"INITIAL_STATE_INVALID")
    def test_budget(self):
        s=self.snap([c.row(1,100000),c.row(2,200000)])
        self.assertEqual(m.resolve(s,{1:0,2:0},1)["status"],"SEARCH_BUDGET")
    def test_lattice(self):
        s=self.snap([c.row(1,100000,speed=40001)])
        with self.assertRaises(ValueError):m.resolve(s,{1:0})
    def test_physics_reference(self):
        s=self.snap([c.row(1,100000,speed=40000)])
        r=m.resolve(s,{1:0})
        self.assertEqual(r["snapshot"].car(1).speed_mm_s,40400)
        self.assertEqual(r["snapshot"].car(1).progress_mm,108040)
        self.assertLessEqual(max(m.check_step(s,r["snapshot"])[1]),1e-9)
    def test_fixture(self):
        r=m.evaluate(e.specs()["racecraft_bounded_motion"]["config"])
        self.assertEqual(r["observations"]["ticks"],48)
        self.assertTrue(all(v==0 for k,v in r["metrics"].items() if k not in ("distance_error_m","speed_error_mps")))
if __name__=="__main__":unittest.main()
