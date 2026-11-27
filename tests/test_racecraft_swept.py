import unittest
from fractions import Fraction as Q
from engineering_lab import racecraft_unified as u, racecraft_swept as s, racecraft_coupled as c, physics_vehicle as v

class SweptTests(unittest.TestCase):
    def test_equal_lateral_acceleration_releases_false_veto(self):
        a=u.initial(100,lateral=-float(u.LAT)/2-.025)
        b=u.initial(100,lateral=float(u.LAT)/2+.025)
        ea=c.step(a,v.control(ay_mps2=4),u.DT)["state"]
        eb=c.step(b,v.control(ay_mps2=4),u.DT)["state"]
        self.assertTrue(u.broad_conflict(a,b,ea,eb,5000))
        self.assertFalse(u.conflict(a,b,ea,eb,5000))
        r=u.resolve({1:a,2:b},{1:v.control(ay_mps2=4),2:v.control(ay_mps2=4)})
        self.assertEqual(r["states"],{1:ea,2:eb})

    def test_contact_between_endpoints(self):
        # Relative lateral parabola dips below the limit at mid-tick.
        a=u.initial(100,lateral=0)
        b=u.initial(100,lateral=float(u.LAT)+.05,lateral_speed=-2)
        ea=c.step(a,v.control(),u.DT)["state"]
        eb=c.step(b,v.control(ay_mps2=20),u.DT)["state"]
        self.assertGreater(eb["lateral_m"],float(u.LAT))
        self.assertTrue(u.conflict(a,b,ea,eb,5000))

    def test_stop_breakpoint(self):
        a=u.initial(100,speed=1)
        ea=c.step(a,v.control(brake=1),u.DT)["state"]
        self.assertEqual(ea["vehicle"]["speed_mps"],0)
        p=s.path(a,ea,u.DT)
        self.assertIsNotNone(p)
        self.assertLess(p[2],1)
        self.assertEqual(p[0](p[2]),p[0](Q(1)))

    def test_quadratic_extremum(self):
        self.assertEqual(s.bounds(lambda t:(t-Q(1,3))**2,Q(0),Q(1)),(0,Q(4,9)))

    def test_wrap_and_symmetry(self):
        a=u.initial(4999,40); b=u.initial(4,40)
        ea=c.step(a,v.control(),u.DT)["state"]
        eb=c.step(b,v.control(),u.DT)["state"]
        self.assertTrue(u.conflict(a,b,ea,eb,5000))
        self.assertTrue(u.conflict(b,a,eb,ea,5000))

    def test_inconsistent_endpoint_preserves_veto(self):
        a=u.initial(100);b=u.initial(100)
        self.assertIsNone(s.refine(a,b,a,b,5000,u.DT,u.LONG,u.LAT))
        self.assertTrue(u.conflict(a,b,a,b,5000))

if __name__=="__main__":unittest.main()
