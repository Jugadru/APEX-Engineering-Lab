import unittest
from engineering_lab import racecraft_attack as a, racecraft_core as c, experimental as e
class AttackTests(unittest.TestCase):
    def base(self,extra=()):
        return a.snap([c.row(1,100000,0,50000),c.row(2,110000,0,40000),*extra])
    def test_candidate(self):
        self.assertEqual(a.opportunity(self.base(),1)["action"],"ATTACK_CANDIDATE")
    def test_blocked(self):
        r=a.opportunity(self.base([c.row(3,100000,-3000),c.row(4,100000,3000)]),1)
        self.assertEqual(r["reason"],"NO_CLEAR_CORRIDOR")
    def test_one_side(self):
        self.assertEqual(a.opportunity(self.base([c.row(3,100000,-3000)]),1)["lateral_mm"],3000)
    def test_lapped(self):
        s=a.snap([c.row(1,5100000,0,50000),c.row(2,110000,0,40000)])
        self.assertEqual(a.opportunity(s,1)["reason"],"NOT_CLASSIFIED_RIVAL")
    def test_rear_closing(self):
        s=self.base([c.row(3,90000,-3000,70000)])
        self.assertEqual(a.opportunity(s,1)["lateral_mm"],3000)
    def test_narrow(self):
        s=a.snap(self.base().payload()["cars"],width=2500)
        self.assertEqual(a.opportunity(s,1)["action"],"HOLD")
    def test_nonconsecutive(self):
        x=a.snap([c.row(1,100000,-3000),c.row(2,110000)],0)
        y=a.snap([c.row(1,140000,-3000),c.row(2,132000)],2)
        with self.assertRaises(ValueError): a.observed_crossing([x,y],1,2)
    def test_fixture(self):
        r=a.evaluate(e.specs()["racecraft_overtaking"]["config"])
        self.assertEqual(r["observations"]["cases"],48)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
if __name__=="__main__": unittest.main()
