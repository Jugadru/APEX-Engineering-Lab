import unittest
from engineering_lab import racecraft_integration as r, experimental as e
class IntegrationTests(unittest.TestCase):
    def run_plan(self,t,blocked=False,prior=None):
        s=r.scripted(t,blocked); p,c=r.inputs(s)
        return r.plan(s,p,c,prior)
    def test_attack_latch(self):
        a=self.run_plan(0)
        self.assertEqual(a["decisions"][0]["mode"],"ATTACK")
        b=self.run_plan(1,True,a["memory"])
        self.assertEqual(b["decisions"][0]["mode"],"ATTACK_HOLD")
        self.assertEqual(b["memory"][1]["attack"]["aim_mm"],a["memory"][1]["attack"]["aim_mm"])
    def test_defense_precedence(self):
        x=self.run_plan(0)
        self.assertEqual(x["decisions"][1]["mode"],"DEFENSE")
        self.assertIsNone(x["memory"][2]["attack"]["target"])
    def test_not_application(self):
        x=self.run_plan(0)
        self.assertEqual(x["meaning"],"DIAGNOSTIC_ONLY_NOT_A_MOTION_COMMAND")
        self.assertEqual(x["feasibility"]["new_contacts"],[])
    def test_repeat(self):
        self.assertEqual(self.run_plan(0),self.run_plan(0))
    def test_missing_profile(self):
        s=r.scripted(0); p,c=r.inputs(s); del p[1]
        with self.assertRaises(ValueError): r.plan(s,p,c)
    def test_tick_binding(self):
        x=self.run_plan(0)
        with self.assertRaises(ValueError): self.run_plan(2,prior=x["memory"])
    def test_fixture(self):
        r0=r.evaluate(e.specs()["racecraft_integration"]["config"])
        self.assertEqual(r0["observations"]["decisions"],288)
        self.assertTrue(all(v==0 for v in r0["metrics"].values()))
if __name__=="__main__": unittest.main()
