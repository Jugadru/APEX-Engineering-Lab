import unittest
from engineering_lab import physics_load as p, experimental as e
class LoadTests(unittest.TestCase):
    def loads(self,ax=0,ay=0):
        return p.corner_loads(600,ax,ay,1000,0.46,0.43,0.33,3.2,1.45)
    def test_static(self):
        r=self.loads()
        self.assertAlmostEqual(r["fl_n"]+r["fr_n"],600*9.81*0.46+430)
        self.assertEqual(r["fl_n"],r["fr_n"])
    def test_long(self):
        self.assertLess(self.loads(ax=10)["fl_n"],self.loads()["fl_n"])
        self.assertGreater(self.loads(ax=-10)["fl_n"],self.loads()["fl_n"])
    def test_lat(self):
        a=self.loads(ay=10); b=self.loads(ay=-10)
        self.assertAlmostEqual(a["fr_n"],b["fl_n"])
        self.assertAlmostEqual(a["rr_n"],b["rl_n"])
    def test_saturation(self):
        r=self.loads(ay=100)
        self.assertTrue(r["saturated"])
        self.assertEqual(r["fl_n"]+r["rl_n"],0)
    def test_invalid(self):
        with self.assertRaises(ValueError): p.corner_loads(600,0,0,0,0.46,0.43,0.33,0,1.45)
        with self.assertRaises(ValueError): p.spring_step(150,30000,100000,0.02,0,1)
    def test_spring_zero(self):
        r=p.spring_step(150,30000,1000,0.02,0.1,0)
        self.assertEqual((r["x_m"],r["v_mps"]),(0.02,0.1))
    def test_spring_energy(self):
        a=p.spring_step(150,30000,0,0.02,0.1,1)
        b=p.spring_step(150,30000,1000,0.02,0.1,1)
        self.assertAlmostEqual(a["initial_energy_j"],a["energy_j"])
        self.assertLess(b["energy_j"],b["initial_energy_j"])
    def test_fixture(self):
        r=p.evaluate(e.specs()["physics_load"]["config"])
        self.assertEqual(r["observations"]["load_cases"],36)
        self.assertEqual(r["observations"]["spring_cases"],12)
        self.assertEqual(r["metrics"]["negative_loads"],0)
        self.assertEqual(r["metrics"]["missing_saturation_cases"],0)
        self.assertLessEqual(r["metrics"]["partition_position_error_m"],1e-10)
        self.assertLessEqual(r["metrics"]["partition_speed_error_mps"],1e-10)
if __name__=="__main__": unittest.main()
