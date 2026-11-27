import unittest
from engineering_lab import racecraft_personality as p, racecraft_attack as a, racecraft_core as c, experimental as e
class PersonalityTests(unittest.TestCase):
    def snapshot(self,blocked=False):
        rows=[c.row(1,100000,0,46000),c.row(2,120000)]
        if blocked: rows.extend([c.row(3,100000,-3000),c.row(4,100000,3000)])
        return a.snap(rows)
    def test_distinct(self):
        s=self.snapshot()
        self.assertEqual(p.decide(s,1,p.PROFILES["patient"],p.context())["action"],"HOLD")
        self.assertEqual(p.decide(s,1,p.PROFILES["assertive"],p.context())["action"],"ATTACK_CANDIDATE")
    def test_safety(self):
        for profile in p.PROFILES.values():
            r=p.decide(self.snapshot(True),1,profile,p.context())
            self.assertEqual(r["action"],"HOLD"); self.assertEqual(r["feasibility"],"VETOED")
    def test_wet(self):
        for profile in p.PROFILES.values():
            self.assertLessEqual(p.budget(profile,p.context(1000)),p.budget(profile,p.context()))
    def test_bounds(self):
        for profile in p.PROFILES.values():
            self.assertTrue(500<=p.budget(profile,p.context(1000,1000,1000))<=6000)
    def test_invalid(self):
        with self.assertRaises(ValueError): p.budget(dict(p.PROFILES["patient"],aggression=True),p.context())
        with self.assertRaises(ValueError): p.budget(p.PROFILES["patient"],p.context(1001))
    def test_fixture(self):
        r=p.evaluate(e.specs()["racecraft_personality"]["config"])
        self.assertEqual(r["observations"]["cases"],162)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
if __name__=="__main__": unittest.main()
