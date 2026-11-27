import unittest
from engineering_lab import strategy_duel as d, strategy_tyre as t, strategy_research as b

class DuelTests(unittest.TestCase):
    def test_timeline_service_and_age(self):
        rows=d.timeline(1000,4,(1,"soft"))
        self.assertEqual(rows[0]["end_ms"],1000+t.lap_cost("medium",4,False))
        self.assertEqual(rows[1]["departure_ms"],rows[0]["end_ms"]+b.PIT_MS)
        self.assertEqual([r["age"] for r in rows],[4,0,1,2])
    def test_traffic_boundaries(self):
        for gap in (0,1,2000):
            self.assertEqual(d.traffic_delay(10000,[10000-gap]),1500)
        for gap in (-1,2001):
            self.assertEqual(d.traffic_delay(10000,[10000-gap]),0)
    def test_tactics_and_tie(self):
        s=d.Snapshot(0,4,4,())
        for stop,tactic in ((0,"undercut"),(1,"same_lap"),(2,"overcut")):
            self.assertEqual(d.simulate(s,(stop,"soft"),(1,500))["tactic"],tactic)
        r=d.simulate(s,(1,"soft"),(1,500))
        self.assertEqual(r["gap_ms"],-2000)
        self.assertTrue(r["ahead"])
    def test_exit_rank_and_delay(self):
        s=d.Snapshot(0,4,4,(23000,26000))
        r=d.simulate(s,(0,"soft"),(1,500))
        self.assertEqual(r["exit_rank"],3)
        self.assertEqual(r["traffic_ms"],1500)
    def test_traffic_avoidance(self):
        s=d.Snapshot(0,4,4,(24000,))
        a=d.simulate(s,(0,"soft"),(1,500))
        self.assertEqual(a["traffic_ms"],1500)
        z=d.simulate(d.Snapshot(0,4,4,()),(0,"soft"),(1,500))
        self.assertEqual(a["own_finish_ms"]-z["own_finish_ms"],1500)
    def test_forecast_optimization(self):
        s=d.Snapshot(1500,10,7,(24000,27000))
        plans=d.choose(s)
        self.assertEqual(d.score(s,plans["duel"]),min(d.score(s,p) for p in d.PLANS))
        self.assertLessEqual(d.score(s,plans["duel"]),d.score(s,plans["solo"]))
        self.assertEqual(plans,d.choose(s))
    def test_invalid_inputs(self):
        s=d.Snapshot(0,4,4,())
        for p in ((True,"soft"),(4,"soft"),(0,"wet")):
            with self.assertRaises(ValueError):d.simulate(s,p,(1,500))
        with self.assertRaises(ValueError):d.simulate(s,(0,"soft"),(0,500))
        with self.assertRaises(ValueError):d.choose(d.Snapshot(0,4,4,(1000,1000)))
    def test_registered_fixture(self):
        cfg=dict(d.spec(lambda op,t:dict(op=op,threshold=t))["config"],cases=8)
        x=d.evaluate(cfg)
        self.assertTrue(all(v==0 for v in x["metrics"].values()))
        self.assertEqual(x,d.evaluate(cfg))

if __name__=="__main__":unittest.main()
