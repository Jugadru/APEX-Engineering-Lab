import unittest
from dataclasses import FrozenInstanceError
from engineering_lab import racecraft_core as r, experimental as e
class CoreTests(unittest.TestCase):
    def snapshot(self,rows):
        return r.Snapshot.from_rows(0,5000000,5000,rows)
    def test_wrap(self):
        self.assertEqual(r.signed_gap(4999000,1000,5000000),2000)
        self.assertEqual(r.signed_gap(1000,4999000,5000000),-2000)
    def test_half(self):
        self.assertEqual(r.signed_gap(0,2500000,5000000),-2500000)
        self.assertEqual(r.signed_gap(0,2500000,5000001),2500000)
    def test_lapped(self):
        s=self.snapshot([r.row(2,5001000),r.row(1,2000)])
        self.assertEqual(s.classification(),(2,1))
        o=s.observations(2)[0]
        self.assertEqual(o["gap_mm"],1000)
        self.assertEqual(o["classified_delta_mm"],-4999000)
    def test_inactive(self):
        s=self.snapshot([r.row(2,6000,active=False),r.row(1,2000)])
        self.assertEqual(s.classification(),(1,))
        self.assertEqual(s.observations(1),())
        with self.assertRaises(ValueError): s.observations(2)
    def test_equal(self):
        s=self.snapshot([r.row(2,0),r.row(1,0)])
        self.assertEqual(s.classification(),(1,2))
        self.assertEqual(s.observations(1)[0]["gap_mm"],0)
    def test_frozen(self):
        rows=[r.row(1,0)]; s=self.snapshot(rows)
        rows[0]["progress_mm"]=99; s.payload()["cars"][0]["progress_mm"]=100
        self.assertEqual(s.cars[0].progress_mm,0)
        with self.assertRaises(FrozenInstanceError): s.cars[0].progress_mm=2
    def test_invalid(self):
        for rows in [[],[r.row(1,0),r.row(1,1)],[r.row(True,0)],[r.row(1,-1)],[r.row(1,0,5001)],[r.row(1,0,active=1)],[dict(r.row(1,0),intent="attack")]]:
            with self.assertRaises(ValueError): self.snapshot(rows)
    def test_no_future_fields(self):
        with self.assertRaises(ValueError): self.snapshot([dict(r.row(1,0),next_lane_mm=0)])
    def test_fixture(self):
        x=r.evaluate(e.specs()["racecraft_foundation"]["config"])
        self.assertEqual(x["observations"]["permutations"],128)
        self.assertEqual(x["metrics"],{"permutation_mismatches":0,"invalid_observations":0})
    def test_closing_sign(self):
        s=self.snapshot([r.row(1,0,speed=50000),r.row(2,8000,speed=40000)])
        self.assertEqual(s.observations(1)[0]["closing_mm_s"],10000)
if __name__=="__main__": unittest.main()
