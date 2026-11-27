import unittest
from copy import deepcopy
from engineering_lab import racecraft_unified as u, physics_vehicle as v, racecraft_coupled as c, experimental as e

class UnifiedTests(unittest.TestCase):
    def test_selected_state_is_physical(self):
        s={1:u.initial(100,lateral=-3),2:u.initial(100,lateral=3)}
        cmds={1:v.control(throttle=.5,ay_mps2=2),2:v.control(brake=.5,ay_mps2=-2)}
        before=deepcopy((s,cmds))
        r=u.resolve(s,cmds)
        self.assertEqual(r["status"],"FEASIBLE_COUPLED_STEP")
        for i,item in r["selected"].items():
            self.assertEqual(item["result"],c.step(s[i],item["command"],u.DT,5))
            self.assertEqual(r["states"][i],item["result"]["state"])
        self.assertEqual((s,cmds),before)
        self.assertGreater(r["states"][1]["lateral_m"],s[1]["lateral_m"])

    def test_wet_combined_force(self):
        s={1:u.initial(100)}
        a=u.resolve(s,{1:v.control(brake=1,grip_factor=.3)})
        b=u.resolve(s,{1:v.control(brake=1,grip_factor=.3,ay_mps2=12)})
        fa=a["selected"][1]["result"]["forward"]
        fb=b["selected"][1]["result"]["forward"]
        self.assertLess(fb["brake_n"],fa["brake_n"])
        self.assertLessEqual(fb["max_grip_utilization"],1+1e-12)

    def test_wrap_conflict(self):
        a=u.initial(4990,60); b=u.initial(5005,0)
        ea=u.initial(5002,60); eb=u.initial(5005,0)
        self.assertTrue(u.conflict(a,b,ea,eb,5000))

    def test_lateral_mid_tick_cross(self):
        a=u.initial(100,lateral=-3); b=u.initial(100,lateral=3)
        ea=u.initial(108,lateral=3); eb=u.initial(108,lateral=-3)
        self.assertTrue(u.conflict(a,b,ea,eb,5000))

    def test_infeasible_is_atomic(self):
        s={1:u.initial(100,60),2:u.initial(106,0)}
        before=deepcopy(s)
        r=u.resolve(s,{i:v.control() for i in s},half_width_m=1.5)
        self.assertEqual(r["status"],"NO_FEASIBLE_DISCRETE_OPTION")
        self.assertIsNone(r["states"]);self.assertIsNone(r["selected"])
        self.assertEqual(s,before)

    def test_budget_is_not_physical_impossibility(self):
        s={1:u.initial(100,lateral=-3),2:u.initial(100,lateral=3)}
        r=u.resolve(s,{i:v.control() for i in s},node_limit=1)
        self.assertEqual(r["status"],"SEARCH_BUDGET")
        self.assertIsNone(r["states"])

    def test_initial_overlap(self):
        s={1:u.initial(100),2:u.initial(100)}
        self.assertEqual(u.resolve(s,{i:v.control() for i in s})["status"],"INITIAL_STATE_INVALID")

    def test_boundary_block(self):
        s={1:u.initial(100,lateral=3.79,lateral_speed=1)}
        self.assertIsNone(u.resolve(s,{1:v.control()},half_width_m=5)["states"])

    def test_permutation(self):
        s={1:u.initial(100,lateral=-3),2:u.initial(100,lateral=3)}
        cmds={i:v.control() for i in s}
        self.assertEqual(u.resolve(s,cmds),u.resolve(dict(reversed(list(s.items()))),dict(reversed(list(cmds.items())))))

    def test_registered_fixture(self):
        spec=e.specs()["racecraft_unified_motion"]
        r=u.evaluate(spec["config"])
        self.assertEqual(r["observations"]["ticks"],300)
        self.assertTrue(all(x==0 for x in r["metrics"].values()),r)

if __name__=="__main__":unittest.main()
