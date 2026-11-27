import unittest
from engineering_lab import racecraft_coupled as c, physics_vehicle as v, experimental as e
class CoupledTests(unittest.TestCase):
    def test_actual_lateral_force(self):
        r=c.step(c.initial(),v.control(ay_mps2=2),0.2)
        self.assertEqual(r["status"],"FEASIBLE_REFERENCE_STEP")
        self.assertAlmostEqual(r["state"]["lateral_speed_mps"],0.4)
        self.assertAlmostEqual(r["state"]["lateral_m"],0.04)
    def test_wet_saturation(self):
        a=c.step(c.initial(),v.control(ay_mps2=20,grip_factor=1),0.2)
        b=c.step(c.initial(),v.control(ay_mps2=20,grip_factor=0.2),0.2)
        self.assertLess(b["lateral_accel_mps2"],a["lateral_accel_mps2"])
    def test_combined_brake(self):
        a=c.step(c.initial(),v.control(brake=1,ay_mps2=0,grip_factor=0.5),0.2)
        b=c.step(c.initial(),v.control(brake=1,ay_mps2=12,grip_factor=0.5),0.2)
        self.assertLess(b["forward"]["brake_n"],a["forward"]["brake_n"])
        self.assertLessEqual(b["forward"]["max_grip_utilization"],1+1e-12)
    def test_internal_extremum(self):
        end,vy,lo,hi=c.lateral_path(3.79,0.4,-4,0.2)
        self.assertAlmostEqual(end,3.79);self.assertGreater(hi,3.8)
    def test_boundary_no_state(self):
        s=c.initial(y=3.79,vy=1)
        r=c.step(s,v.control(),0.2)
        self.assertIsNone(r["state"]);self.assertEqual(r["status"],"BOUNDARY_BLOCKED")
    def test_zero_tick(self):
        s=c.initial()
        self.assertEqual(c.step(s,v.control(ay_mps2=10),0)["state"],s)
    def test_low_speed(self):
        r=c.step(c.initial(speed=0),v.control(ay_mps2=2),0.2)
        self.assertEqual(r["status"],"LOW_SPEED_LATERAL_NOT_MODELLED")
    def test_fixture(self):
        r=c.evaluate(e.specs()["racecraft_coupled_motion"]["config"])
        self.assertEqual(r["observations"]["force_cases"],24)
        self.assertEqual(r["metrics"]["invalid_states"],0)
        self.assertEqual(r["metrics"]["boundary_count_error"],0)
if __name__=="__main__":unittest.main()
