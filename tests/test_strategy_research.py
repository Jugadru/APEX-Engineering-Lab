import unittest
from engineering_lab import strategy_research as s, experimental as e

class StrategyResearchTests(unittest.TestCase):
    def test_all_dry_cost(self):
        self.assertEqual(s.cost_plan((False,False),"dry",4,0,"dry"),204400)
    def test_weather_boundaries(self):
        import random
        self.assertEqual(s.weather_path(random.Random(1),False,4,0),(False,)*4)
        self.assertEqual(s.weather_path(random.Random(1),False,4,1000),(False,True,False,True))
    def test_forced_final_stop(self):
        for p in s.POLICIES:
            self.assertIn(s.choose(p,7,8,"dry",11,True,42,32,250),s.TYRES)
    def test_future_prefix_causality(self):
        a=(False,False,False,True,True,True,True,True)
        b=(False,False,False,False,False,False,False,False)
        for p in s.POLICIES:
            self.assertEqual(s.episode(p,a,42,16,250)["trace"][:3],
                             s.episode(p,b,42,16,250)["trace"][:3])
    def test_oracle_bound_and_one_stop(self):
        for path in ((False,)*8,(True,)*8,(False,True)*4):
            best=min(s.cost_plan(path,"dry",4,k,c) for k in range(8) for c in s.TYRES)
            for p in s.POLICIES:
                r=s.episode(p,path,42,16,250)
                self.assertGreaterEqual(r["total_ms"],best)
                self.assertEqual(sum(x["action"] is not None for x in r["trace"]),1)
    def test_invalid_forecast_budget(self):
        with self.assertRaises(ValueError):s.choose("monte_carlo",0,8,"dry",4,False,42,129,250)
    def test_registered_fixture(self):
        spec=e.specs()["strategy_weather_decision"]
        r=spec["evaluate"](spec["config"])
        self.assertEqual(r["metrics"],{"invalid_actions":0,"replay_mismatches":0,"negative_regret":0})
        self.assertEqual(r["observations"]["cases"],32)
        self.assertEqual(r,spec["evaluate"](spec["config"]))

    def test_plan_rejects_fractional_boolean_and_outside_stop(self):
        for stop in (.5,True,False,-1,2,"0"):
            with self.subTest(stop=stop):
                with self.assertRaises(ValueError):
                    s.cost_plan((False,False),"dry",4,stop,"dry")
    def test_plan_rejects_invalid_initial_state_even_if_stop_immediate(self):
        for tyre,age in (("invalid",4),("dry",-1),("dry",True),("dry",33)):
            with self.assertRaises(ValueError):
                s.cost_plan((False,False),tyre,age,0,"wet")
    def test_plan_rejects_invalid_weather_or_unrepresentable_stint(self):
        for weather in ((),(False,1),[False]*21):
            with self.assertRaises(ValueError):
                s.cost_plan(weather,"dry",4,0,"dry")
        with self.assertRaises(ValueError):
            s.cost_plan((False,False,False),"dry",32,2,"dry")
    def test_exhaustive_short_episode_accounting_and_prefix_causality(self):
        from itertools import product
        for policy in s.POLICIES:
            for flip in (0,250,1000):
                prefixes={}
                for weather in product((False,True),repeat=4):
                    r=s.episode(policy,weather,17,8,flip)
                    stop=r["stop"]
                    self.assertIs(type(stop),int)
                    self.assertEqual(r["total_ms"],s.cost_plan(weather,"dry",4,stop,r["trace"][stop]["action"]))
                    self.assertEqual(r["total_ms"],s.PIT_MS+sum(x["cost_ms"] for x in r["trace"]))
                    for i,row in enumerate(r["trace"]):
                        prefix=weather[:i+1]
                        self.assertEqual(row,prefixes.setdefault(prefix,row))
    def test_unrepresentable_decision_stint_is_rejected(self):
        with self.assertRaises(ValueError):
            s.choose("monte_carlo",0,20,"dry",32,False,42,8,250)

if __name__=="__main__":unittest.main()
