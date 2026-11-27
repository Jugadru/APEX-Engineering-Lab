import math
import unittest
from copy import deepcopy
from engineering_lab import racecraft_oriented as o, racecraft_yaw as y, physics_vehicle as v, experimental as e

class OrientedTests(unittest.TestCase):
    def test_orientation_changes_contact(self):
        self.assertGreater(o.separation((0,0,0),(0,2.5,0)),0)
        self.assertLessEqual(o.separation((0,0,math.pi/2),(0,2.5,0)),0)
    def test_mid_interval_cross(self):
        a,b=(-8,0,0),(8,0,0)
        other=(0,0,0)
        self.assertGreater(o.separation(a,other),0)
        self.assertGreater(o.separation(b,other),0)
        self.assertTrue(o.swept(a,b,other,other))
    def test_rotation_only_sweep(self):
        # A rotating rectangle crosses a nearby rectangle halfway through.
        a=(-0.0,0,-math.pi/4); b=(0,0,math.pi/4)
        other=(4.5,0,math.pi/2)
        self.assertGreater(o.separation(a,other),0)
        self.assertGreater(o.separation(b,other),0)
        # The original center is too far at x=4.5 even when straight.
        self.assertFalse(o.swept(a,b,other,other))
        self.assertTrue(o.swept((0,0,0),(0,0,math.pi/2),(0,3.2,0),(0,3.2,0)))
    def test_separated_parallel(self):
        self.assertFalse(o.swept((0,-2,0),(8,-2,0),(0,2,0),(8,2,0)))
    def test_heading_wrap(self):
        self.assertAlmostEqual(o.angle_delta(math.pi-.01,-math.pi+.01),.02)
    def test_rotated_edge(self):
        self.assertTrue(o.inside((0,3,0),(0,3,0),5))
        self.assertFalse(o.inside((0,3,math.pi/2),(0,3,math.pi/2),5))
    def test_atomic_and_budget(self):
        s={1:y.initial(),2:dict(y.initial(),x_m=30)}
        cmd={i:v.control() for i in s};target={i:0 for i in s};before=deepcopy(s)
        r=o.resolve(s,cmd,target,node_limit=1)
        self.assertEqual(r["status"],"SEARCH_BUDGET")
        self.assertIsNone(r["states"]);self.assertEqual(s,before)
        self.assertEqual(o.resolve({1:s[1],2:s[1]},cmd,target)["status"],"INITIAL_STATE_INVALID")
    def test_yaw_integration_and_order(self):
        s={1:dict(y.initial(),y_m=-2),2:dict(y.initial(),y_m=2)}
        cmd={i:v.control() for i in s};target={1:-.02,2:.02}
        r=o.resolve(s,cmd,target)
        self.assertEqual(r["status"],"FEASIBLE_ORIENTED_STEP")
        self.assertLess(r["states"][1]["heading_rad"],0)
        self.assertGreater(r["states"][2]["heading_rad"],0)
        self.assertFalse(o.collide(r["selected"][1]["poses"],r["selected"][2]["poses"]))
        self.assertEqual(r,o.resolve(dict(reversed(list(s.items()))),cmd,target))
    def test_fixture(self):
        result=o.evaluate(e.specs()["racecraft_oriented_motion"]["config"])
        self.assertEqual(result["metrics"],{"invalid":0,"replay_mismatches":0},result)

if __name__=="__main__": unittest.main()
