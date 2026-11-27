import unittest
from engineering_lab import racecraft_historical_reference as h
def fixture():
    rows=[]
    for c,v in h.FASTEST_MS.items():
        minute,rest=divmod(v,60000);sec,ms=divmod(rest,1000)
        rows.append(dict(code=c,lap_km=(5513 if c=="USA" else h.CALENDAR[c])/1000,
                         fastest_lap_2012=f"{minute}:{sec:02}.{ms:03}",base_lap=(v+500)/1000))
    return rows
class HistoricalReferenceTests(unittest.TestCase):
    def test_match_and_usa_discrepancy(self):
        r=h.compare(fixture())
        self.assertEqual((r["fastest_matches"],r["length_matches"],r["buffer_matches"]),(20,20,20))
        self.assertEqual(r["usa_pre_race_calendar_m"],5516)
        self.assertAlmostEqual(r["usa_race_implied_length_m"],5513,places=1)
        self.assertEqual(r["calibration"],"NOT_PERFORMED")
    def test_mismatch(self):
        r=fixture();r[0]["base_lap"]+=1
        self.assertEqual(h.compare(r)["status"],"FAIL")
    def test_bad_lap(self):
        with self.assertRaises(ValueError):h.lap_ms("1:60.123")
    def test_roster(self):
        r=fixture();r[0]=r[1]
        with self.assertRaises(ValueError):h.compare(r)
    def test_outline_refs_not_imported(self):
        r=h.compare(fixture())["missing_outline_references"]
        self.assertEqual(set(r["layouts"]),{"EUR","KOR","IND"})
        self.assertEqual(r["status"],"DOCUMENTARY_SOURCE_IDENTIFIED_NOT_IMPORTED")
if __name__=="__main__":unittest.main()
