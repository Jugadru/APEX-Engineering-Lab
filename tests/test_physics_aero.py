import unittest
from engineering_lab import physics_aero as p, experimental as e
class AeroTests(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(p.forces(0,1.2,0.8,2.5),{"drag_n":0,"downforce_n":0,"drag_power_w":0})
        self.assertEqual(p.forces(90,0,0.8,2.5)["drag_n"],0)
    def test_known(self):
        a=p.forces(50,1.2,0.8,2.5)
        self.assertAlmostEqual(a["drag_n"],1200)
        self.assertAlmostEqual(a["downforce_n"],3750)
        self.assertAlmostEqual(a["drag_power_w"],60000)
    def test_decoupled(self):
        a=p.forces(50,1.2,0.8,2.5)
        b=p.forces(50,1.2,0.8,2.5,0.15,0)
        self.assertAlmostEqual(b["drag_n"],0.85*a["drag_n"])
        self.assertEqual(b["downforce_n"],a["downforce_n"])
    def test_loss_full(self):
        self.assertEqual(p.forces(50,1.2,0.8,2.5,1,1)["downforce_n"],0)
    def test_invalid(self):
        for args in [(-1,1,1,1),(1,-1,1,1),(1,1,-1,1),(1,1,1,1,1.1,0)]:
            with self.assertRaises(ValueError): p.forces(*args)
    def test_fixture(self):
        r=p.evaluate(e.specs()["physics_aero"]["config"])
        self.assertEqual(r["observations"]["cases"],48)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
if __name__=="__main__": unittest.main()
