import unittest
from engineering_lab import exp_sensitivity as s, experimental as e
class SensitivityTests(unittest.TestCase):
    def test_engine(self):
        self.assertEqual(s.acceleration(800,1.2,3000),(3.75,"engine"))
    def test_grip(self):
        self.assertEqual(s.acceleration(600,0.4,6000),(0.4*9.81,"traction"))
    def test_equal(self):
        self.assertEqual(s.acceleration(100,1,1000,10),(10,"equal"))
    def test_traction_plateau(self):
        self.assertEqual(s.acceleration(600,0.4,6000),s.acceleration(900,0.4,6000))
    def test_invalid(self):
        for args in [(0,1,1),(1,-1,1),(1,1,-1),(1,float("nan"),1)]:
            with self.assertRaises(ValueError): s.acceleration(*args)
    def test_grid(self):
        r=s.evaluate(e.specs()["mass_grip_sensitivity"]["config"])
        self.assertEqual(r["observations"]["cases"],40)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
        self.assertEqual(sum(r["observations"]["regimes"].values()),40)
if __name__=="__main__": unittest.main()
