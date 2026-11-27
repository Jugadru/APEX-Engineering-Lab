import unittest
from engineering_lab import racecraft_stability as s, experimental as e
from engineering_lab import racecraft_attack as a, racecraft_core as c
class StabilityTests(unittest.TestCase):
    def test_replay(self):
        _,snapshots=next(s.scenarios(42,6))
        self.assertEqual(s.replay(snapshots)["digest"],s.replay(snapshots,reverse=True,checkpoint=True)["digest"])
    def test_fixture(self):
        r=s.evaluate(e.specs()["racecraft_stability"]["config"])
        self.assertEqual(r["observations"]["decisions_including_replays"],4320)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
    def test_far_rear_horizon(self):
        # Farther than the immediate 38 m observation radius, but catches
        # the proposed left corridor within the predeclared ETA.
        s0=a.snap([c.row(1,100000,0,46000),c.row(2,120000),c.row(3,50000,-3000,80000)])
        r=a.opportunity(s0,1)
        self.assertEqual((r["action"],r["lateral_mm"]),("ATTACK_CANDIDATE",3000))
    def test_periodic_horizon(self):
        s0=c.Snapshot.from_rows(0,100000,5000,[c.row(1,100000,0,50000),c.row(2,112000),c.row(3,150000,-3000,100000)])
        r=a.opportunity(s0,1)
        self.assertEqual((r["action"],r["lateral_mm"]),("ATTACK_CANDIDATE",3000))
    def test_exact_horizon_contact(self):
        s0=a.snap([c.row(1,100000,0,40000),c.row(2,85000,-3000,50000)])
        self.assertFalse(a.destination_conflict(s0,s0.car(1),s0.car(2),-3000,969))
        self.assertTrue(a.destination_conflict(s0,s0.car(1),s0.car(2),-3000,970))
    def test_snapshot_canonical_contract(self):
        with self.assertRaises(ValueError): c.Snapshot(0,5000000,5000,[c.Car(1,0,0,40000)])
        with self.assertRaises(ValueError): c.Snapshot(0,5000000,5000,(c.Car(2,0,0,40000),c.Car(1,1,0,40000)))
        with self.assertRaises(ValueError): c.Snapshot(0,5000000,5000,(c.Car(1,0,5001,40000),))
    def test_direct_invalid_car(self):
        with self.assertRaises(ValueError): c.Car(1,-1,0,40000,True)
    def test_direct_invalid_snapshot(self):
        with self.assertRaises(ValueError): c.Snapshot(0,5000000,5000,(c.Car(1,0,0,40000),c.Car(1,1,0,40000)))
if __name__=="__main__": unittest.main()
