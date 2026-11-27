import math
import unittest
from engineering_lab import physics_powertrain as p, experimental as e
class PowertrainTests(unittest.TestCase):
    def test_curve(self):
        self.assertEqual(p.torque_nm(0),0)
        self.assertEqual(p.torque_nm(12000),300)
        self.assertEqual(p.torque_nm(18000),290)
        self.assertEqual(p.torque_nm(18001),0)
    def test_rpm_and_power(self):
        v=14000*2*math.pi/60*0.33/p.RATIOS[2]
        r=p.output(v,3,0.33,1,0.93,0.2)
        self.assertAlmostEqual(r["rpm"],14000)
        self.assertAlmostEqual(r["torque_nm"],320)
        self.assertAlmostEqual(r["wheel_power_w"],r["crank_power_w"]*0.93)
    def test_shift_cut(self):
        a=p.output(30,3,0.33,1,0.93,0.2)
        b=p.output(30,3,0.33,1,0.93,0.2,0.06)
        self.assertAlmostEqual(b["wheel_force_n"],0.7*a["wheel_force_n"])
        self.assertEqual(p.output(30,3,0.33,1,0.93,0.2,0.2)["wheel_power_w"],0)
    def test_dt_zero(self):
        self.assertEqual(p.output(30,3,0.33,1,0.93,0)["wheel_force_n"],0)
    def test_no_launch_model(self):
        self.assertEqual(p.output(0,1,0.33,1,1,0.2)["wheel_force_n"],0)
    def test_overrev(self):
        self.assertEqual(p.output(100,1,0.33,1,1,0.2)["wheel_force_n"],0)
    def test_invalid(self):
        for gear in (0,8,True):
            with self.assertRaises(ValueError): p.output(30,gear,0.33,1,1,0.2)
        with self.assertRaises(ValueError): p.output(30,1,0,1,1,0.2)
    def test_fixture(self):
        r=p.evaluate(e.specs()["physics_powertrain"]["config"])
        self.assertEqual(r["observations"]["cases"],210)
        self.assertEqual(r["metrics"]["invalid_states"],0)
        self.assertLessEqual(r["metrics"]["relative_power_error"],1e-12)
if __name__=="__main__": unittest.main()
