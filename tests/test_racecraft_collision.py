import unittest
from engineering_lab import racecraft_collision as c, experimental as e
class CollisionTests(unittest.TestCase):
    def check_case(self,*args):
        s,a,b=c.fixture(*args)
        return c.contact(s,1,2,a,b)
    def test_tunnel(self):
        r=self.check_case(100000,0,120000,0,40000,0,0,0)
        self.assertEqual(r["first_fraction"],[147,400])
    def test_lateral_swap(self):
        r=self.check_case(100000,-3000,100000,3000,10000,3000,10000,-3000)
        self.assertTrue(r["contact"]); self.assertFalse(r["initial_contact"])
    def test_parallel(self):
        self.assertFalse(self.check_case(100000,-3000,100000,3000,10000,-3000,10000,3000)["contact"])
    def test_wrap(self):
        self.assertTrue(self.check_case(4990000,0,5000,0,25000,0,0,0)["contact"])
    def test_exact_touch(self):
        self.assertTrue(self.check_case(100000,0,105300,2100,0,0,0,2100)["initial_contact"])
        self.assertFalse(self.check_case(100000,0,105301,2100,0,0,0,2100)["contact"])
    def test_disjoint_time_intervals(self):
        # Longitudinal contact during middle of tick, lateral contact only near end.
        self.assertFalse(self.check_case(100000,-4000,110000,4000,40000,-4000,0,-4000)["contact"])
    def test_invalid_endpoint(self):
        s,a,b=c.fixture(100000,0,120000,0,0,0,0,0)
        with self.assertRaises(ValueError): c.contact(s,1,2,c.endpoint(99999,0),b)
    def test_fixture(self):
        r=c.evaluate(e.specs()["racecraft_collision"]["config"])
        self.assertEqual(r["observations"]["cases"],72)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
if __name__=="__main__": unittest.main()
