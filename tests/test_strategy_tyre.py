import unittest
from itertools import product,combinations
from engineering_lab import strategy_tyre as t

class StrategyTyreTests(unittest.TestCase):
    def test_fresh_and_cliff(self):
        self.assertEqual(t.lap_cost("soft",0,False),90000)
        self.assertEqual(t.lap_cost("soft",5,False),91100)
        self.assertEqual(t.lap_cost("soft",6,False),92070)
        self.assertEqual(t.lap_cost("soft",7,False),94540)
    def test_compound_tradeoff(self):
        self.assertLess(t.lap_cost("soft",0,False),t.lap_cost("hard",0,False))
        self.assertGreater(t.lap_cost("soft",12,False),t.lap_cost("hard",12,False))
        self.assertLess(t.lap_cost("wet",0,True),t.lap_cost("soft",0,True))
    def test_service_accounting(self):
        self.assertEqual(t.plan_cost((False,True),[(1,"wet")]),205450)
    def test_independent_oracle_matches_brute(self):
        for path in product((False,True),repeat=4):
            for cap in (1,3):
                want=min(t.plan_cost(path,list(zip(laps,types)),cap)
                         for n in range(1,cap+1)
                         for laps in combinations(range(4),n)
                         for types in product(t.PROFILES,repeat=n))
                self.assertEqual(t.hindsight(path,cap),want)
    def test_weighted_reference(self):
        r=t.exact(4,(100,600))
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
    def test_prefix_and_budget(self):
        choose=t.controller((100,600),3)
        a=t.replay((False,True,True,True),choose)
        b=t.replay((False,True,False,False),choose)
        self.assertEqual(a["trace"][:2],b["trace"][:2])
        self.assertTrue(1<=len(a["stops"])<=3)
    def test_long_replay(self):
        path=(False,)*6+(True,)*6
        for cap in (1,3):
            r=t.replay(path,t.controller((100,600),cap),cap)
            self.assertEqual(r["total_ms"],t.plan_cost(path,r["stops"],cap))
            self.assertGreaterEqual(r["total_ms"],t.hindsight(path,cap))
    def test_invalid_state_and_plan(self):
        for tyre,age,wet in (("bad",0,False),("soft",-1,False),("hard",True,False),("wet",1,1)):
            with self.assertRaises(ValueError):t.lap_cost(tyre,age,wet)
        for stops in ([],[(True,"soft")],[(0,"bad")],[(1,"hard"),(1,"wet")]):
            with self.assertRaises(ValueError):t.plan_cost((False,True),stops)
        with self.assertRaises(ValueError):t.controller((100,600))(13,"medium",4,(False,))
    def test_registered_experiment(self):
        cfg=dict(t.spec(lambda op,x:dict(op=op,threshold=x))["config"],horizon=4,exact_horizon=4,cases_per_regime=2)
        r=t.evaluate(cfg)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
        self.assertEqual(r,t.evaluate(cfg))

if __name__=="__main__":unittest.main()
