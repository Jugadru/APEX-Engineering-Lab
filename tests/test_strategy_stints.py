import unittest
from fractions import Fraction
from itertools import product
from engineering_lab import strategy_stints as s, strategy_weather as w, strategy_research as b

class MultiStintTests(unittest.TestCase):
    def test_service_and_stint_accounting(self):
        self.assertEqual(s.plan_cost((False,True,True,False),[(1,"wet"),(3,"dry")]),409800)
    def test_final_mandatory_stop(self):
        choose=s.controller((100,600),1,3)
        self.assertEqual(choose(1,"dry",4,(True,)),(Fraction(114000),"wet"))
    def test_zero_budget(self):
        choose=s.controller((100,600),0,0)
        r=s.replay((False,True),choose,0,0)
        self.assertEqual(r["stops"],[])
        self.assertEqual(r["total_ms"],s.plan_cost((False,True),[],0,0))
    def test_single_stop_value_compatibility(self):
        old=w.controller((100,600));new=s.controller((100,600),1,1)
        for remaining,wet in product(range(1,7),(False,True)):
            self.assertEqual(old(remaining,"dry",4,(wet,))[0],new(remaining,"dry",4,(wet,))[0])
    def test_complete_plan_oracle_bound(self):
        choose=s.controller((100,600))
        for path in product((False,True),repeat=4):
            r=s.replay(path,choose)
            self.assertGreaterEqual(r["total_ms"],s.hindsight(path))
            self.assertEqual(r["total_ms"],s.plan_cost(path,r["stops"]))
    def test_exact_weighted_comparison(self):
        r=s.exact(4,(100,600))
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
    def test_invalid_plans_and_budgets(self):
        for stops in ([(True,"wet")],[(1,"wet"),(1,"dry")],[(2,"wet")],[(0,"bad")],[]):
            with self.assertRaises(ValueError):s.plan_cost((False,True),stops)
        with self.assertRaises(ValueError):s.controller((100,600),1,4)
        with self.assertRaises(ValueError):s.controller((100,600))(2,"dry",4,(False,),1)
    def test_causality(self):
        choose=s.controller((100,600))
        a=s.replay((False,True,False,False),choose)
        b=s.replay((False,True,True,True),choose)
        self.assertEqual(a["trace"][:2],b["trace"][:2])
    def test_config_replay(self):
        cfg=dict(s.spec(lambda op,t:dict(op=op,threshold=t))["config"],horizon=4,cases_per_regime=4)
        r=s.evaluate(cfg)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
        self.assertEqual(r,s.evaluate(cfg))

if __name__=="__main__":unittest.main()
