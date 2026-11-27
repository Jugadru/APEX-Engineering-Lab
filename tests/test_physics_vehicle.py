import unittest
from engineering_lab import physics_vehicle as p, experimental as e
class VehicleTests(unittest.TestCase):
    def test_zero_time(self):
        x=p.initial(); r=p.step(x,p.control(throttle=1,kers_w=60000),0)
        self.assertEqual(r["state"],x); self.assertEqual(r["distance_m"],0)
    def test_coast(self):
        r=p.step(p.initial(),p.control(),0.2)
        self.assertLess(r["state"]["speed_mps"],30)
        self.assertEqual(r["drive_work_j"],0)
        self.assertEqual(r["fuel_burn_kg"],0)
    def test_empty_sources(self):
        r=p.step(p.initial(fuel=0,store=0,lap=0),p.control(throttle=1,kers_w=60000),0.2)
        self.assertEqual(r["drive_work_j"],0)
        self.assertEqual(r["accepted_wheel_j"],0)
    def test_kers_without_fuel(self):
        r=p.step(p.initial(fuel=0),p.control(throttle=1,kers_w=60000),0.2)
        self.assertGreater(r["drive_work_j"],0)
        self.assertGreater(r["kers_used_j"],0)
        self.assertEqual(r["fuel_burn_kg"],0)
        self.assertAlmostEqual(r["drive_work_j"],r["accepted_wheel_j"],places=7)
    def test_brake_precedence(self):
        r=p.step(p.initial(),p.control(brake=1,throttle=1,kers_w=60000),0.2)
        self.assertEqual(r["drive_n"],0)
        self.assertGreater(r["brake_n"],0)
        self.assertEqual(r["kers_used_j"],0)
    def test_cut(self):
        r=p.step(p.initial(),p.control(throttle=1,cut_s=0.2,kers_w=60000),0.2)
        self.assertEqual(r["drive_n"],0)
    def test_lateral_limits(self):
        r=p.step(p.initial(),p.control(throttle=1,ay_mps2=30,grip_factor=0.1),0.2)
        self.assertGreater(r["lateral_unmet_n"],0)
        self.assertLessEqual(r["max_grip_utilization"],1+1e-12)
    def test_no_mutation(self):
        state=p.initial(); command=p.control(throttle=1); a=state.copy(); b=command.copy()
        self.assertEqual(p.step(state,command,0.2),p.step(state,command,0.2))
        self.assertEqual(state,a); self.assertEqual(command,b)
    def test_near_rest(self):
        r=p.step(p.initial(speed=1e-12),p.control(throttle=1,kers_w=60000),0.2)
        self.assertLessEqual(r["drive_work_j"],r["available_wheel_j"]+1e-8)
        self.assertGreaterEqual(r["state"]["speed_mps"],0)
    def test_tiny_dt_rejected(self):
        with self.assertRaises(ValueError): p.step(p.initial(),p.control(),1e-300)
    def test_invalid(self):
        with self.assertRaises(ValueError): p.step(p.initial(),p.control(),0.6)
        with self.assertRaises(ValueError): p.step(p.initial(),p.control(gear=8),0.2)
    def test_fixture(self):
        r=p.evaluate(e.specs()["physics_vehicle"]["config"])
        self.assertEqual(r["observations"]["cases"],180)
        self.assertEqual(r["metrics"]["invalid_states"],0)
        self.assertEqual(r["metrics"]["missing_operating_modes"],0)
        self.assertLessEqual(r["metrics"]["energy_residual_j"],1e-7)
if __name__=="__main__": unittest.main()
