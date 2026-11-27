import unittest
from engineering_lab import physics_brakes as p, experimental as e
class BrakeTests(unittest.TestCase):
    def test_stop(self):
        r=p.brake_step(600,10,6000,10000,1,2,0.6)
        self.assertEqual(r["speed_mps"],0)
        self.assertAlmostEqual(r["distance_m"],5)
        self.assertAlmostEqual(r["heat_j"],30000)
        self.assertAlmostEqual(r["front_heat_j"],18000)
    def test_cap(self):
        r=p.brake_step(600,10,6000,1000,0.5,1,0.6)
        self.assertEqual(r["brake_force_n"],500)
        self.assertTrue(r["demand_exceeds_grip"])
    def test_no_grip(self):
        r=p.brake_step(600,10,6000,1000,0,1,0.6)
        self.assertEqual(r["speed_mps"],10)
        self.assertEqual(r["heat_j"],0)
        self.assertIsNone(p.stopping_distance(600,10,0))
    def test_at_rest(self):
        self.assertEqual(p.stopping_distance(600,0,0),0)
        self.assertEqual(p.brake_step(600,0,6000,1000,1,1,0.6)["heat_j"],0)
    def test_heat(self):
        self.assertEqual(p.heat_rise(30000,1000),30)
    def test_invalid(self):
        with self.assertRaises(ValueError): p.brake_step(600,10,-1,1000,1,1,0.6)
        with self.assertRaises(ValueError): p.heat_rise(1,0)
    def test_fixture(self):
        r=p.evaluate(e.specs()["physics_brakes"]["config"])
        self.assertEqual(r["observations"]["cases"],54)
        self.assertEqual(r["metrics"]["invalid_states"],0)
        self.assertLessEqual(r["metrics"]["relative_heat_work_error"],1e-10)
if __name__=="__main__": unittest.main()
