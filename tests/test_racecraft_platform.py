import unittest
from engineering_lab import racecraft_platform as p

class PlatformReplayTests(unittest.TestCase):
    def test_identical_records(self):
        self.assertEqual(p.compare([{"schema":1},{"schema":1}]),p.reg.digest({"schema":1}))
    def test_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            p.compare([{"digest":"a"},{"digest":"b"}])
    def test_single_record_not_a_comparison(self):
        with self.assertRaises(ValueError):
            p.compare([{"schema":1}])

if __name__=="__main__":unittest.main()
