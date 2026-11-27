import unittest
from engineering_lab import racecraft_rules_2012 as r,experimental as e
class RulesTests(unittest.TestCase):
    def test_unknown(self):
        self.assertTrue(all(x["status"]=="INCONCLUSIVE" for x in r.review(r.observation())["observations"]))
    def test_multiple(self):
        x=r.review(dict(r.baseline(),defensive_moves=2))
        self.assertEqual(x["observations"][1]["signals"],["MULTIPLE_DEFENSIVE_DIRECTION_CHANGES"])
        self.assertEqual(x["penalty"],"NOT_DECIDED")
    def test_return_room(self):
        x=r.review(dict(r.baseline(),defensive_moves=1,returning_before_corner=True,room_mm=1800,car_width_mm=1800))
        self.assertEqual(x["observations"][1]["status"],"NO_SIGNAL_IN_DECLARED_OBSERVATIONS")
    def test_missing_room(self):
        x=r.review(dict(r.baseline(),defensive_moves=1,returning_before_corner=True))
        self.assertEqual(x["observations"][1]["status"],"INCONCLUSIVE")
    def test_conflicting_input(self):
        with self.assertRaises(ValueError):r.review(dict(r.baseline(),rejoined=True))
        with self.assertRaises(ValueError):r.review(dict(r.baseline(),returning_before_corner=True))
    def test_invalid_types(self):
        with self.assertRaises(ValueError):r.review(dict(r.baseline(),defensive_moves=True))
        with self.assertRaises(ValueError):r.review(dict(r.baseline(),room_mm=-1))
    def test_fixture(self):
        x=r.evaluate(e.specs()["racecraft_rules_2012"]["config"])
        self.assertEqual(x["observations"]["clause_checks"],64)
        self.assertEqual(x["metrics"],{"rule_signal_mismatches":0,"automatic_penalties":0})
if __name__=="__main__":unittest.main()
