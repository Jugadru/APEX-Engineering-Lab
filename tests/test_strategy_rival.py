import unittest
from dataclasses import replace
from engineering_lab import strategy_rival as r, strategy_window as w, strategy_traffic as t, strategy_duel as d

class RivalTests(unittest.TestCase):
    def state(self,**kw):
        ws=w.State(d.Snapshot(0,4,4,()),"medium",(False,),True)
        return t.State(replace(ws,**kw),())

    def test_cover_only_after_observed_pit(self):
        s=self.state()
        x=r.outcome(s,(0,"soft"),(False,)*4,(2,500),"cover")
        self.assertIsNone(x["trace"][0]["rival_action"])
        self.assertEqual(x["trace"][1]["reason"],"cover")
        self.assertEqual(x["rival_stop"],1)

    def test_same_lap_hidden_action(self):
        s=self.state()
        a=r.outcome(s,(1,"soft"),(False,)*4,(2,500),"cover")
        b=r.outcome(s,(2,"soft"),(False,)*4,(2,500),"cover")
        self.assertEqual([(z["rival_action"],z["reason"]) for z in a["trace"][:2]],
                         [(z["rival_action"],z["reason"]) for z in b["trace"][:2]])

    def test_extend_once(self):
        x=r.outcome(self.state(),(3,"soft"),(False,)*4,(1,-500),"extend")
        self.assertEqual(x["trace"][1]["reason"],"extend")
        self.assertEqual(x["rival_stop"],2)
        self.assertEqual(sum(z["reason"]=="extend" for z in x["trace"]),1)

    def test_weather_and_wear(self):
        s=self.state(prefix=(True,))
        x=r.outcome(s,(2,"wet"),(True,)*4,(2,500),"cover")
        self.assertEqual((x["rival_stop"],x["rival_compound"],x["trace"][0]["reason"]),(0,"wet","weather"))
        s=self.state(duel_state=d.Snapshot(0,4,20,()))
        x=r.outcome(s,(2,"soft"),(False,)*4,(2,500),"cover")
        self.assertEqual((x["rival_stop"],x["trace"][0]["reason"]),(0,"wear"))

    def test_future_weather_not_visible(self):
        s=self.state()
        a=r.outcome(s,(0,"soft"),(False,False,False,False),(2,500),"cover")
        b=r.outcome(s,(0,"soft"),(False,False,True,True),(2,500),"cover")
        self.assertEqual(a["trace"][:2],b["trace"][:2])

    def test_manual_and_no_stop(self):
        s=self.state(manual=2)
        self.assertEqual(r.choose(s)["plan"][0],2)
        with self.assertRaises(ValueError):r.outcome(s,(1,"soft"),(False,)*4,(2,500),"cover")
        s=self.state(required=False)
        x=r.outcome(s,w.NONE,(False,)*4,(2,500),"cover")
        self.assertTrue(all(z["own_action"] is None for z in x["trace"]))
        self.assertIsNotNone(x["rival_stop"])

    def test_input_validation(self):
        s=self.state()
        for p in ((True,"soft"),(1.0,"soft"),w.NONE):
            with self.assertRaises(ValueError):r.outcome(s,p,(False,)*4,(2,500),"cover")
        with self.assertRaises(ValueError):r.outcome(s,(1,"soft"),(False,)*4,(2,500),"unknown")

    def test_fixture(self):
        cfg=dict(r.spec(lambda op,v:dict(op=op,threshold=v))["config"],cases=3)
        x=r.evaluate(cfg)
        self.assertTrue(all(v==0 for v in x["metrics"].values()))
        self.assertGreater(x["observations"]["grid_reasons"]["cover"],0)
        self.assertGreater(x["observations"]["grid_reasons"]["extend"],0)
        self.assertEqual(x,r.evaluate(cfg))
