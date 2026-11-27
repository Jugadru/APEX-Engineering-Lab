import unittest
from engineering_lab import racecraft_historical_pace as p

class HistoricalPaceTests(unittest.TestCase):
    def test_parser(self):
        raw="".join(f"- position: {i+1}\n  driverId: driver-{i}\n  constructorId: team\n  time: \"1:30.{i:03d}\"\n" for i in range(10))
        self.assertEqual(len(p.parse(raw)),10)
        with self.assertRaises(ValueError):
            p.parse(raw.replace("driver-1\n","driver-0\n"))
    def test_group_holdout(self):
        rows=[(f"driver-{i}",f"team-{i//2}",90000+i*100) for i in range(24)]
        rounds={i:list(rows) for i in range(1,21)}
        r=p.benchmark(rounds)
        self.assertEqual(r["training_rows"],360)
        self.assertEqual(r["holdout_rows"],120)
        self.assertEqual(r["holdout_rounds"],[4,8,12,16,20])
        self.assertEqual(r["driver_team_mae"],0)
        self.assertGreater(r["team_mae"],0)
        self.assertEqual(r["physical_calibration"],"NOT_ESTABLISHED")
    def test_unseen_pair_fallback(self):
        rows=[(f"driver-{i}",f"team-{i//2}",90000+i*100) for i in range(24)]
        rounds={i:list(rows) for i in range(1,21)}
        rounds[4][0]=("new-driver","team-0",90000)
        self.assertEqual(p.benchmark(rounds)["unseen_driver_team_rows"],1)
    def test_missing_calendar_rejected(self):
        with self.assertRaises(ValueError):p.benchmark({})
if __name__=="__main__":unittest.main()
