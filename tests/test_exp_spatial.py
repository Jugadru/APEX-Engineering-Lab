import unittest
from engineering_lab import exp_spatial as s, experimental as e
class SpatialTests(unittest.TestCase):
    def test_wrap(self):
        rows=[(0,0),(1,99),(2,1),(3,50)]
        self.assertEqual(s.Ring(rows,100).query(rows[0],1)[0],[1,2])
    def test_zero_and_equal(self):
        rows=[(0,0),(1,0),(2,1)]
        self.assertEqual(s.Ring(rows,100).query(rows[0],0)[0],[1])
    def test_half(self):
        rows=[(0,0),(1,50),(2,99)]
        self.assertEqual(s.Ring(rows,100).query(rows[0],50)[0],[1,2])
    def test_odd_length(self):
        rows=[(0,0),(1,2),(2,3),(3,4)]
        self.assertEqual(s.Ring(rows,5).query(rows[0],2)[0],[1,2,3])
    def test_duplicate_id(self):
        with self.assertRaises(ValueError): s.Ring([(0,0),(0,1)],100)
    def test_invalid_radius(self):
        with self.assertRaises(ValueError): s.Ring([(0,0)],100).query((0,0),51)
    def test_full_experiment(self):
        x=s.evaluate(e.specs()["spatial_neighbors"]["config"])
        self.assertEqual(x["metrics"]["neighbor_mismatches"],0)
        self.assertEqual(x["observations"]["queries"],576)
        self.assertLess(x["metrics"]["extra_rows"],0)
    def test_permutation(self):
        rows=[(0,0),(1,0),(2,10)]
        self.assertEqual(s.Ring(rows,100).query(rows[0],10),s.Ring(rows[::-1],100).query(rows[0],10))
if __name__=="__main__": unittest.main()
