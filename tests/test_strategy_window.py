import unittest
from dataclasses import replace
from engineering_lab import strategy_window as w, strategy_duel as d

class WindowTests(unittest.TestCase):
    def state(self,**kw):
        return replace(w.State(d.Snapshot(0,4,4,()),"medium",(False,),False),**kw)

    def test_no_stop_and_required(self):
        s=self.state()
        self.assertIn(w.NONE,w.plans(s))
        self.assertNotIn(w.NONE,w.plans(replace(s,required=True)))
        self.assertEqual(w.recommend(s)["plan"],w.NONE)
        self.assertIsNone(w.recommend(s)["first"])

    def test_manual_lock(self):
        s=self.state(manual=2)
        self.assertEqual(len(w.plans(s)),4)
        r=w.recommend(s)
        self.assertEqual((r["first"],r["ideal"],r["last"],r["action"]),(2,2,2,"wait"))

    def test_bounds(self):
        s=self.state(required=True,earliest=1,latest=2)
        self.assertEqual(len(w.plans(s)),8)
        for bad in (replace(s,manual=0),replace(s,earliest=True),replace(s,latest=4)):
            with self.assertRaises(ValueError):w.plans(bad)

    def test_weather_posterior(self):
        calm=self.state(prefix=(False,False,False))
        volatile=self.state(prefix=(False,True,False))
        def flip_prob(s):
            f=w.forecasts(s)
            return sum(v for p,r,v in f if p[1]!=p[0])/sum(v for p,r,v in f)
        self.assertGreater(flip_prob(volatile),flip_prob(calm))

    def test_traffic_and_reference(self):
        s=self.state(duel_state=d.Snapshot(0,4,4,(24000,24000)),required=True)
        path=(False,)*4
        for p in w.plans(s):
            for rival in d.FORECAST:
                self.assertEqual(w.outcome(s,p,path,rival),w.reference(s,p,path,rival))
        self.assertEqual(w.outcome(s,(0,"soft"),path,(1,500))[2],1500)

    def test_worn_tyre_and_window(self):
        s=self.state(duel_state=d.Snapshot(0,20,4,()),required=True)
        r=w.recommend(s)
        self.assertEqual(r["ideal"],0)
        self.assertIn(0,r["eligible"])
        self.assertEqual(r["action"],"pit_now")

    def test_unexpected_weather_no_hindsight(self):
        s=self.state(required=True)
        before=w.recommend(s)
        for path in ((False,)*4,(False,True,True,True)):
            for rival in d.FORECAST:
                self.assertEqual(w.outcome(s,before["plan"],path,rival),w.reference(s,before["plan"],path,rival))
        self.assertEqual(w.recommend(s),before)

    def test_fixture(self):
        cfg=dict(w.spec(lambda op,t:dict(op=op,threshold=t))["config"],cases=4)
        r=w.evaluate(cfg)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
        self.assertEqual(r,w.evaluate(cfg))
