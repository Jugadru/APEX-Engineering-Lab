import unittest
from copy import deepcopy
from engineering_lab import racecraft_yaw as y, physics_vehicle as v, experimental as e

class YawTests(unittest.TestCase):
    def test_straight(self):
        a=y.step(y.initial(),v.control(),0)
        self.assertEqual(a["status"],"FEASIBLE_YAW_REFERENCE")
        for k in ("y_m","heading_rad","yaw_rad_s","body_vy_mps"):
            self.assertEqual(a["state"][k],0)
        self.assertGreater(a["state"]["x_m"],0)

    def test_steering_rate_and_yaw(self):
        a=y.step(y.initial(),v.control(),.1,1)
        self.assertAlmostEqual(a["state"]["steer_rad"],y.STEER_RATE*y.DT)
        self.assertGreater(a["state"]["yaw_rad_s"],0)
        self.assertGreater(a["trace"][0]["front_n"],0)
        self.assertEqual(a["trace"][0]["rear_n"],0)

    def test_low_speed_atomic(self):
        s=y.initial(5);before=deepcopy(s)
        a=y.step(s,v.control(),.1)
        self.assertEqual(a["status"],"SPEED_DOMAIN")
        self.assertIsNone(a["state"])
        self.assertEqual(s,before)

    def test_axle_grip_shared(self):
        state=v.initial(40)
        a=v.step(state,v.control(brake=1,grip_factor=.4),.01,(0,0))
        b=v.step(state,v.control(brake=1,grip_factor=.4),.01,(8000,8000))
        self.assertLess(b["brake_n"],a["brake_n"])
        self.assertLessEqual(b["max_grip_utilization"],1+1e-12)
        self.assertAlmostEqual(b["lateral_force_n"],b["front_lateral_n"]+b["rear_lateral_n"])

    def test_legacy_result_preserved(self):
        a=v.step(v.initial(),v.control(),.2)
        self.assertNotIn("front_lateral_n",a)

    def test_no_duplicate_lateral_request(self):
        with self.assertRaises(ValueError):
            y.step(y.initial(),v.control(ay_mps2=2),.1)

    def test_fixture(self):
        result=y.evaluate(e.specs()["racecraft_yaw"]["config"])
        self.assertEqual(result["metrics"]["invalid"],0,result)
        self.assertEqual(result["metrics"]["replay_mismatches"],0)
        self.assertLessEqual(result["metrics"]["mirror_error"],1e-9)
        self.assertLessEqual(result["metrics"]["grip_excess"],1e-12)
        self.assertLessEqual(result["metrics"]["forward_work_error"],1e-10)

if __name__=="__main__":unittest.main()
