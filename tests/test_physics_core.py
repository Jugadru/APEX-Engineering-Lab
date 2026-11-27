import unittest
from engineering_lab import physics_core as p, experimental as e
class PhysicsCoreTests(unittest.TestCase):
    def test_accelerate(self):
        r=p.step_force(600,20,6000,2)
        self.assertAlmostEqual(r["speed_mps"],40)
        self.assertAlmostEqual(r["distance_m"],60)
        self.assertAlmostEqual(r["net_work_j"],360000)
    def test_stop_inside_tick(self):
        r=p.step_force(600,5,-6000,2)
        self.assertEqual(r["speed_mps"],0)
        self.assertAlmostEqual(r["distance_m"],1.25)
        self.assertAlmostEqual(r["moving_interval_s"],0.5)
        self.assertAlmostEqual(r["net_work_j"],-7500)
    def test_stop_at_rest(self):
        r=p.step_force(600,0,-6000,2)
        self.assertEqual((r["distance_m"],r["speed_mps"],r["net_work_j"]),(0,0,0))
    def test_dt_zero(self):
        r=p.step_force(600,40,6000,0)
        self.assertEqual((r["speed_mps"],r["distance_m"]),(40,0))
    def test_coast(self):
        r=p.step_force(600,40,0,0.2)
        self.assertEqual(r["speed_mps"],40)
        self.assertAlmostEqual(r["distance_m"],8)
    def test_invalid(self):
        for args in [(0,1,1,1),(True,1,1,1),(600,-1,1,1),(600,1,float("nan"),1),(600,1,1,-1),(600,1,1,11)]:
            with self.assertRaises(ValueError): p.step_force(*args)
    def test_suite(self):
        s=e.specs()["physics_foundation"]; r=p.evaluate(s["config"])
        self.assertEqual(r["observations"]["cases"],54)
        self.assertLessEqual(r["metrics"]["relative_work_error"],1e-10)
        self.assertEqual(r["metrics"]["invalid_states"],0)
if __name__=="__main__": unittest.main()
