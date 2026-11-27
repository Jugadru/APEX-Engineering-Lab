import unittest
from fractions import Fraction
from itertools import product
from engineering_lab import strategy_weather as w, strategy_research as b

class WeatherPredictionTests(unittest.TestCase):
    def test_prior_and_bayes_update(self):
        self.assertEqual(w.posterior((100,600),0,0),(Fraction(1,2),Fraction(1,2)))
        self.assertEqual(w.posterior((100,600),1,0),(Fraction(1,7),Fraction(6,7)))
        self.assertEqual(w.posterior((100,600),0,1),(Fraction(9,13),Fraction(4,13)))
        self.assertEqual(w.forecast((100,600),0,0),Fraction(7,20))
        self.assertGreater(w.forecast((100,600),1,0),Fraction(7,20))
        self.assertLess(w.forecast((100,600),0,1),Fraction(7,20))
    def test_counts(self):
        self.assertEqual(w.counts((False,True,True,False)),(2,1))
        with self.assertRaises(ValueError):w.counts((False,1))
    def test_final_stop(self):
        solve=w.controller((100,600))
        for wet in (False,True):
            cost,action=solve(1,"dry",4,(wet,))
            self.assertEqual((cost,action),(114000,"wet" if wet else "dry"))
    def test_causal_replay(self):
        policies=w.policy_set((100,600))
        for p in policies.values():
            a=w.replay((False,True,False,False),p)
            c=w.replay((False,True,True,True),p)
            self.assertEqual(a["trace"][:2],c["trace"][:2])
    def test_exact_weighted_value_and_forecast(self):
        for rates in ((100,600),(250,750)):
            out=w.exact(4,rates)
            self.assertTrue(all(v==0 for v in out["metrics"].values()))
            self.assertLessEqual(out["brier"]["bayesian"],out["brier"]["fixed"])
    def test_cost_reconciliation(self):
        for path in product((False,True),repeat=4):
            for p in w.policy_set((100,600)).values():
                r=w.replay(path,p)
                self.assertEqual(r["total_ms"],b.cost_plan(path,"dry",4,r["stop"],r["compound"]))
    def test_bounds(self):
        for rates in ((0,600),(100,100),(600,100),(True,600),(100,601)):
            with self.assertRaises(ValueError):w.controller(rates)
        with self.assertRaises(ValueError):w.posterior((100,600),-1,1)
        with self.assertRaises(ValueError):w.controller((100,600))(8,"dry",4,(False,True))
    def test_registry_config_and_misspecification(self):
        spec=w.spec(lambda op,t:dict(op=op,threshold=t))
        config=dict(spec["config"],horizon=4,cases_per_regime=4)
        r=w.evaluate(config)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
        self.assertEqual(r,w.evaluate(config))
        self.assertEqual([x["in_prior"] for x in r["observations"]["holdout"]],[True,True,False])

if __name__=="__main__":unittest.main()
