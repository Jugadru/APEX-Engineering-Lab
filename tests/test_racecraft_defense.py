import unittest
from engineering_lab import racecraft_defense as d, experimental as e
class DefenseTests(unittest.TestCase):
    def test_commit(self):
        r=d.decide(d.snap(0),1)
        self.assertEqual((r["mode"],r["aim_mm"]),("COMMIT",-2000))
    def test_not_chase(self):
        m=d.decide(d.snap(0,-2500),1)["memory"]
        r=d.decide(d.snap(1,2500),1,m)
        self.assertEqual((r["mode"],r["aim_mm"]),("COMMITTED",-2000))
    def test_safety_hold(self):
        m=d.decide(d.snap(0),1)["memory"]
        r=d.decide(d.snap(1,block=True),1,m)
        self.assertEqual((r["mode"],r["aim_mm"]),("SAFETY_HOLD",0))
        self.assertEqual(r["memory"]["aim_mm"],-2000)
    def test_overlap(self):
        self.assertEqual(d.decide(d.snap(0,gap=-1000),1)["mode"],"HOLD")
    def test_no_reset_early(self):
        m=d.decide(d.snap(0),1)["memory"]
        for t in range(1,5):
            r=d.decide(d.snap(t,gap=-60000),1,m); m=r["memory"]
            self.assertTrue(m["used"])
        self.assertEqual(d.decide(d.snap(5,gap=-60000),1,m)["mode"],"RELEASE")
    def test_tick(self):
        m=d.decide(d.snap(0),1)["memory"]
        with self.assertRaises(ValueError): d.decide(d.snap(2),1,m)
    def test_fixture(self):
        r=d.evaluate(e.specs()["racecraft_defensive"]["config"])
        self.assertEqual(r["observations"]["ticks"],40)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
if __name__=="__main__": unittest.main()
