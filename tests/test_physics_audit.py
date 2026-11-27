"""Predeclared audit counterexamples and independent bounded seeded regression."""
import math
import random
import unittest
from engineering_lab import physics_core as core, physics_tyre as tyre, physics_load as load
from engineering_lab import physics_brakes as brakes, physics_vehicle as vehicle

class PhysicsAuditTests(unittest.TestCase):
    def test_exact_stop_after_fractional_tick(self):
        r=core.step_force(600,1,-7777,0.2)
        self.assertEqual(r["speed_mps"],0.0)
        self.assertAlmostEqual(r["distance_m"],600/(2*7777),places=14)
        self.assertAlmostEqual(r["net_work_j"],-300,places=10)

    def test_stationary_moving_interval(self):
        r=core.step_force(600,0,0,0.2)
        self.assertEqual(r["moving_interval_s"],0)
        self.assertEqual(r["distance_m"],0)

    def test_thermal_out_of_domain_is_explicit(self):
        # A valid input may predict a state outside the model's declared domain.
        # Reject explicitly rather than return an unusable state or silently clamp.
        with self.assertRaises(ValueError):
            tyre.thermal_step(300,300,100000,1,0,10)

    def test_spring_out_of_domain_is_explicit(self):
        with self.assertRaises(ValueError):
            load.spring_step(1,10000000,0,1,0,0.0005)

    def test_unrepresentable_stop_distance_is_explicit(self):
        with self.assertRaises(ValueError):
            brakes.stopping_distance(600,60,1e-320)

    def test_thermal_valid_boundary(self):
        self.assertAlmostEqual(tyre.thermal_step(1999,300,1000,1000,0,1),2000)

    def test_seeded_vehicle_contracts(self):
        rng=random.Random(20261127)
        for i in range(240):
            state=vehicle.initial(rng.uniform(0,100),rng.choice([0,0.001,5,100]),
                                  rng.choice([0,1000,400000]),rng.choice([0,5000,400000]))
            state["prior_ax_mps2"]=rng.uniform(-30,30)
            cmd=vehicle.control(throttle=rng.random(),brake=rng.choice([0,0,rng.random()]),
                gear=rng.randrange(1,8),cut_s=rng.choice([0,0.06,0.2]),kers_w=rng.uniform(0,60000),
                ay_mps2=rng.uniform(-25,25),grip_factor=rng.random(),
                tyre_temp_k=rng.uniform(260,450),wear=rng.random(),
                drag_loss=rng.random(),load_loss=rng.random())
            dt=rng.choice([0,0.025,0.1,0.2,0.5])
            with self.subTest(case=i):
                r=vehicle.step(state,cmd,dt); s=r["state"]
                self.assertTrue(all(math.isfinite(v) for v in s.values()))
                self.assertGreaterEqual(s["speed_mps"],0)
                self.assertGreaterEqual(r["distance_m"],0)
                for k in ("fuel_kg","store_j","lap_j"):
                    self.assertTrue(0<=s[k]<=state[k],k)
                self.assertLessEqual(r["drive_work_j"],r["available_wheel_j"]+1e-8)
                self.assertLessEqual(r["energy_residual_j"],1e-7)
                self.assertLessEqual(r["relative_work_error"],1e-10)
                self.assertLessEqual(r["max_grip_utilization"],1+1e-12)
                if cmd["brake"]: self.assertEqual(r["drive_n"],0)
                if dt==0: self.assertEqual(s,state)

if __name__=="__main__": unittest.main()
