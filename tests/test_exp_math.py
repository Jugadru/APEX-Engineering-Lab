import unittest
from engineering_lab import exp_math as m, experimental as e
class MathTests(unittest.TestCase):
    def test_exact(self):
        v,x,_=m.integrate(600,6000,20,0.5,4)
        self.assertAlmostEqual(v,40); self.assertAlmostEqual(x,60)
    def test_zero_force(self):
        self.assertEqual(m.integrate(600,0,20,0.5,4),(20,40,40))
    def test_mass(self):
        self.assertLess(m.integrate(800,6000,20,0.5,4)[0],m.integrate(600,6000,20,0.5,4)[0])
    def test_euler_convergence(self):
        coarse=m.integrate(600,6000,20,0.5,4)[2]
        fine=m.integrate(600,6000,20,0.1,20)[2]
        self.assertLess(abs(fine-60),abs(coarse-60))
    def test_invalid(self):
        for a in [(0,1,0,1,1),(1,-1,0,1,1),(1,1,0,0,1),(1,1,0,1,1001)]:
            with self.assertRaises(ValueError): m.integrate(*a)
    def test_experiment(self):
        s=e.specs()["longitudinal_math"]; r=m.evaluate(s["config"])
        self.assertEqual(r["observations"]["cases"],27)
        self.assertEqual(r["metrics"]["monotonic_violations"],0)
        self.assertLessEqual(r["metrics"]["position_error_m"],1e-10)
if __name__=="__main__": unittest.main()
