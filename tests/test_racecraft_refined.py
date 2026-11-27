import unittest
from copy import deepcopy
from engineering_lab import racecraft_unified as u, racecraft_coupled as c, physics_vehicle as v

class RefinementTests(unittest.TestCase):
    def test_edge_recovery_not_in_original_control_set(self):
        car=u.initial(100,lateral=3.73,lateral_speed=1)
        cmd=v.control()
        old=u.alternatives(car,cmd,False)
        self.assertTrue(all(c.step(car,x,u.DT)["state"] is None for x in old))
        before=deepcopy(car)
        r=u.resolve({1:car},{1:cmd})
        self.assertEqual(r["status"],"FEASIBLE_COUPLED_STEP")
        self.assertEqual(r["search_stage"],"REFINED")
        self.assertLessEqual(r["selected"][1]["result"]["lateral_max_m"],3.8)
        self.assertEqual(r["states"][1],c.step(car,r["selected"][1]["command"],u.DT)["state"])
        self.assertEqual(car,before)

    def test_primary_path_unchanged(self):
        r=u.resolve({1:u.initial(100)},{1:v.control()})
        self.assertEqual(r["search_stage"],"PRIMARY")
        self.assertEqual(r["nodes"],1)

    def test_preserve_environment_and_ranges(self):
        cmd=v.control(throttle=.6,kers_w=1000,grip_factor=.4,wear=.2,tyre_temp_k=350,drag_loss=.1,load_loss=.1)
        opts=list(u.refined_alternatives(u.initial(100,lateral_speed=8),cmd))
        self.assertLessEqual(len(opts),53)
        for option in opts:
            for k in ("gear","cut_s","grip_factor","wear","tyre_temp_k","drag_loss","load_loss"):
                self.assertEqual(option[k],cmd[k])
            self.assertTrue(-30<=option["ay_mps2"]<=30)
            self.assertTrue(0<=option["brake"]<=1 and 0<=option["throttle"]<=1)

    def test_no_budget_reset(self):
        s={1:u.initial(100,lateral=-3),2:u.initial(100,lateral=3)}
        r=u.resolve(s,{i:v.control() for i in s},node_limit=1)
        self.assertEqual(r["status"],"SEARCH_BUDGET")
        self.assertEqual(r["nodes"],1)
        self.assertIsNone(r["states"])

    def test_refined_replay(self):
        s={1:u.initial(100,lateral=3.73,lateral_speed=1)}
        self.assertEqual(u.resolve(s,{1:v.control()}),u.resolve(s,{1:v.control()}))

if __name__=="__main__":unittest.main()
