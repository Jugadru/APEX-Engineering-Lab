import unittest
from engineering_lab import physics_stability as p, physics_vehicle as v, experimental as e
class StabilityTests(unittest.TestCase):
    def test_zero_time(self):
        self.assertEqual(p.exact_coast(60,647,0),{"speed_mps":60,"distance_m":0})
    def test_stop(self):
        r=p.exact_coast(0.5,647,4)
        self.assertEqual(r["speed_mps"],0)
        self.assertGreater(r["distance_m"],0)
        self.assertLess(r["distance_m"],2)
    def test_reference_derivative(self):
        dt=1e-5; speed=60; mass=647
        r=p.exact_coast(speed,mass,dt)
        self.assertAlmostEqual((r["speed_mps"]-speed)/dt,-(150+0.48*speed**2)/mass,places=5)
    def test_convergence(self):
        oracle=p.exact_coast(60,647,4)
        coarse=p.coast(60,20); fine=p.coast(60,160)
        self.assertLess(abs(fine["speed_mps"]-oracle["speed_mps"]),abs(coarse["speed_mps"]-oracle["speed_mps"]))
        self.assertLess(abs(fine["distance_m"]-oracle["distance_m"]),abs(coarse["distance_m"]-oracle["distance_m"]))
    def test_sequence_repeat(self):
        initial=v.initial(); self.assertEqual(p.sequence(initial),p.sequence(initial))
        self.assertEqual(initial,v.initial())
    def test_accumulated_balance(self):
        r=p.sequence(v.initial())
        self.assertEqual(r["ticks"],120)
        self.assertLessEqual(r["relative_work_error"],1e-8)
        self.assertLessEqual(r["fuel_residual_kg"],1e-10)
        self.assertEqual(r["invalid_ticks"],0)
    def test_empty_energy(self):
        r=p.sequence(v.initial(fuel=0,store=0,lap=0))
        self.assertEqual(r["final_state"]["fuel_kg"],0)
        self.assertEqual(r["final_state"]["store_j"],0)
        self.assertEqual(r["final_state"]["lap_j"],0)
    def test_invalid(self):
        with self.assertRaises(ValueError): p.coast(60,1001)
        with self.assertRaises(ValueError): p.exact_coast(-1,647,1)
    def test_fixture(self):
        spec=e.specs()["physics_stability"]; r=p.evaluate(spec["config"])
        self.assertEqual(r["observations"]["coast_cases"],12)
        self.assertEqual(r["observations"]["sequence_ticks_including_repeat"],720)
        for metric,rule in spec["criteria"].items():
            from engineering_lab.registry import check
            self.assertTrue(check(rule,r["metrics"][metric]),metric)
if __name__=="__main__": unittest.main()
