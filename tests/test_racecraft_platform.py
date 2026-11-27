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

    def test_steering_numeric_and_discrete_contract(self):
        a={"schema":2,"legacy":{"schema":1,"digest":"same"},"steering":{"status":"PASS","nodes":1,"x":1.0}}
        b={"schema":2,"legacy":a["legacy"],"steering":{"status":"PASS","nodes":1,"x":1.0+1e-11}}
        self.assertEqual(p.compare([a,b]),p.reg.digest(a["legacy"]))
        for key,value in (("nodes",2),("status","FAIL"),("x",1.01),("x",float("nan"))):
            bad={**b,"steering":{**b["steering"],key:value}}
            with self.assertRaises(ValueError): p.compare([a,bad])
        with self.assertRaises(ValueError): p.compare([a,a["legacy"]])
    def test_actual_steering_records(self):
        data=p.steering_records()
        self.assertEqual(len(data["oriented"]),2)
        self.assertTrue(all(len(x["frames"])==4 for x in data["oriented"]))
        self.assertLess(data["refined_edge"]["final_loss"],data["refined_edge"]["initial_loss"])

if __name__=="__main__":unittest.main()
