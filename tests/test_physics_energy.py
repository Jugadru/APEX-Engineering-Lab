import unittest
from engineering_lab import physics_energy as p, experimental as e
class EnergyTests(unittest.TestCase):
    def settle(self,fuel=1,store=400000,lap=400000,demand=5000,dt=0.2):
        return p.settle(fuel,store,lap,500000,100000,dt,0.3,0.93,0.9,demand)
    def test_accepted_only(self):
        r=self.settle()
        self.assertEqual(r["fuel_burn_kg"],0)
        self.assertAlmostEqual(r["kers_used_j"],5000/0.9)
        self.assertAlmostEqual(r["accepted_wheel_j"],5000)
    def test_empty(self):
        r=self.settle(fuel=0,store=0)
        self.assertEqual(r["accepted_wheel_j"],0)
        self.assertEqual(r["unmet_wheel_j"],5000)
    def test_no_demand(self):
        r=self.settle(demand=0)
        self.assertEqual((r["fuel_burn_kg"],r["kers_used_j"]),(0,0))
    def test_limits(self):
        r=self.settle(lap=1000,demand=200000)
        self.assertAlmostEqual(r["kers_used_j"],1000)
        self.assertEqual(r["lap_remaining_j"],0)
        self.assertLessEqual(r["accepted_wheel_j"],200000)
    def test_power_cap(self):
        r=self.settle(demand=200000)
        self.assertAlmostEqual(r["kers_used_j"],12000)
    def test_zero_time(self):
        r=self.settle(dt=0)
        self.assertEqual(r["accepted_wheel_j"],0)
    def test_fuel(self):
        r=self.settle(fuel=0.001,store=0,demand=200000)
        self.assertAlmostEqual(r["fuel_remaining_kg"],0)
        self.assertAlmostEqual(r["accepted_wheel_j"],0.001*p.LHV_J_KG*0.3*0.93)
    def test_invalid(self):
        with self.assertRaises(ValueError): self.settle(lap=400001)
        with self.assertRaises(ValueError): p.offers(1,1,1,1,1,1,0,1,1)
    def test_fixture(self):
        r=p.evaluate(e.specs()["physics_energy"]["config"])
        self.assertEqual(r["observations"]["cases"],162)
        self.assertEqual(r["metrics"]["invalid_states"],0)
        self.assertLessEqual(r["metrics"]["relative_energy_error"],1e-12)
if __name__=="__main__": unittest.main()
