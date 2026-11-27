import unittest
from copy import deepcopy
from engineering_lab import racecraft_yaw as y, racecraft_oriented as o, racecraft_control_refine as c, physics_vehicle as v

class ShiftCutTests(unittest.TestCase):
    def test_partial_cut_recovers_power_after_sixty_ms(self):
        s=y.initial();cmd=v.control(throttle=1,cut_s=.06)
        before=deepcopy((s,cmd))
        r=y.step(s,cmd,0)
        self.assertEqual(r["status"],"FEASIBLE_YAW_REFERENCE")
        self.assertTrue(all(t["drive_work_j"]<=1e-9 for t in r["trace"][:6]))
        self.assertTrue(all(t["drive_work_j"]>0 for t in r["trace"][6:]))
        self.assertEqual((s,cmd),before)
    def test_full_cut_and_zero_cut(self):
        s=y.initial()
        a=y.step(s,v.control(throttle=1,cut_s=.2),0)
        b=y.step(s,v.control(throttle=1,cut_s=0),0)
        self.assertTrue(all(t["drive_work_j"]<=1e-9 for t in a["trace"]))
        self.assertTrue(all(t["drive_work_j"]>0 for t in b["trace"]))
    def test_fractional_cut_is_not_restarted(self):
        cmd=v.control(throttle=1,cut_s=.025)
        cuts=[y.substep_command(cmd,i)["cut_s"] for i in range(20)]
        self.assertAlmostEqual(sum(cuts),.025)
        self.assertAlmostEqual(cuts[2],.005)
        self.assertTrue(all(t==0 for t in cuts[3:]))
    def test_oriented_path_matches_single_yaw_call(self):
        s=y.initial();cmd=v.control(throttle=1,cut_s=.06)
        direct=y.step(s,cmd,.02)
        selected=o.path(s,cmd,.02,6)
        self.assertIsNotNone(selected)
        self.assertEqual(selected["state"],direct["state"])
        r=c.refine({1:s},{1:cmd},{1:.02})
        self.assertEqual(r["states"][1],direct["state"])
if __name__=="__main__":unittest.main()
