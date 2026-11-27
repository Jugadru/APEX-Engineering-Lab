import unittest
from copy import deepcopy
from engineering_lab import racecraft_control_refine as c, racecraft_oriented as o, racecraft_yaw as y, physics_vehicle as v, experimental as e

class ControlRefinementTests(unittest.TestCase):
    def test_zero_budget_keeps_feasible_base(self):
        s={1:dict(y.initial(),y_m=4.9)};cmd={1:v.control()};target={1:.25}
        base=o.resolve(s,cmd,target)
        r=c.refine(s,cmd,target,eval_limit=0)
        self.assertEqual(r["states"],base["states"])
        self.assertEqual(r["evaluations"],0)
        self.assertEqual(r["initial_loss"],r["final_loss"])
    def test_command_already_feasible(self):
        s={1:y.initial()};r=c.refine(s,{1:v.control()},{1:0})
        self.assertEqual(r["initial_loss"],0)
        self.assertEqual(r["final_loss"],0)
        self.assertEqual(r["evaluations"],0)
    def test_refinement_is_physical_and_atomic(self):
        s={1:dict(y.initial(),y_m=4.8),2:dict(y.initial(),x_m=30,y_m=-2)}
        cmd={i:v.control() for i in s};target={1:.25,2:0};before=deepcopy((s,cmd,target))
        r=c.refine(s,cmd,target)
        self.assertEqual(r["status"],"FEASIBLE_ORIENTED_STEP")
        self.assertLessEqual(r["final_loss"],r["initial_loss"])
        for i,p in r["selected"].items():
            self.assertEqual(p,o.path(s[i],p["command"],p["steer_target"],6))
        self.assertFalse(o.collide(r["selected"][1]["poses"],r["selected"][2]["poses"]))
        self.assertEqual((s,cmd,target),before)
    def test_bad_budget(self):
        with self.assertRaises(ValueError):c.refine({1:y.initial()},{1:v.control()},{1:0},eval_limit=193)
    def test_fixture(self):
        r=c.evaluate(e.specs()["racecraft_control_refinement"]["config"])
        self.assertEqual(r["metrics"],{"invalid":0,"replay_mismatches":0,"missing_improvement":0},r)
if __name__=="__main__":unittest.main()
