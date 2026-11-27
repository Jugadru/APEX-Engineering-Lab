import unittest
from engineering_lab import physics_tyre as p, experimental as e
class TyreTests(unittest.TestCase):
    def test_zero_normal(self):
        self.assertEqual(p.combined(0,1,1,100,-100),{"fx_n":0,"fy_n":0,"utilization":0})
    def test_zero_axis(self):
        self.assertEqual(p.combined(100,0,1,50,50)["fy_n"],50)
        self.assertEqual(p.combined(100,0,1,50,50)["fx_n"],0)
    def test_ellipse(self):
        x=p.combined(100,1,2,-100,200)
        self.assertAlmostEqual(x["utilization"],1)
        self.assertAlmostEqual(x["fx_n"],-100/2**0.5)
    def test_thermal_equilibrium(self):
        self.assertEqual(p.thermal_step(350,300,5000,1000,100,2),350)
    def test_adiabatic(self):
        self.assertEqual(p.thermal_step(300,300,1000,1000,0,2),302)
    def test_cooling(self):
        self.assertGreater(p.thermal_step(350,300,0,1000,100,2),300)
        self.assertLess(p.thermal_step(350,300,0,1000,100,2),350)
    def test_wear(self):
        self.assertEqual(p.wear_step(0.5,10000,10000),1)
        self.assertEqual(p.wear_step(0.5,0,10000),0.5)
    def test_mu(self):
        self.assertAlmostEqual(p.effective_mu(1.5,360,360,30,0),1.5)
        self.assertLess(p.effective_mu(1.5,380,360,30,0.5),1.5)
    def test_invalid(self):
        with self.assertRaises(ValueError): p.combined(-1,1,1,1,1)
        with self.assertRaises(ValueError): p.thermal_step(300,300,0,0,1,1)
        with self.assertRaises(ValueError): p.wear_step(0,-1,1)
    def test_suite(self):
        r=p.evaluate(e.specs()["physics_tyre"]["config"])
        self.assertEqual(r["observations"]["grip_cases"],45)
        self.assertEqual(r["observations"]["thermal_cases"],18)
        self.assertEqual(r["observations"]["wear_cases"],9)
        self.assertLessEqual(r["metrics"]["ellipse_excess"],1e-12)
        self.assertEqual(r["metrics"]["wear_violations"],0)
if __name__=="__main__": unittest.main()
