import unittest
from itertools import product
from engineering_lab import strategy_adaptive as a, strategy_research as b

class AdaptiveStrategyTests(unittest.TestCase):
    def test_final_mandatory_stop_and_spent(self):
        for wet in (False,True):
            solve=a.controller(250)
            r=solve(1,"dry",4,wet)
            self.assertEqual(r["action"],"wet" if wet else "dry")
            self.assertEqual(r["numerator_ms"],114000)
            self.assertEqual(r["denominator"],1)
            r=solve(1,"dry",4,wet,True)
            self.assertIsNone(r["action"])
            self.assertEqual(r["numerator_ms"],b.lap_cost("dry",4,wet))
    def test_independent_two_lap_optimality(self):
        # Explicit first action and independent optimal terminal action.
        for flip,wet,age in product((0,250,500,1000),(False,True),(0,4,12)):
            candidates=[]
            for action in a.ACTIONS:
                first=b.lap_cost("dry" if action is None else action,age if action is None else 0,wet)
                if action is not None:
                    first+=b.PIT_MS
                def second(next_wet):
                    if action is None:
                        return b.PIT_MS+min(b.lap_cost(t,0,next_wet) for t in b.TYRES)
                    return b.lap_cost(action,1,next_wet)
                candidates.append((1000*first+(1000-flip)*second(wet)+flip*second(not wet),a.ACTIONS.index(action),action))
            want=min(candidates)
            got=a.controller(flip)(2,"dry",age,wet)
            self.assertEqual((got["numerator_ms"],got["action"]),(want[0],want[2]))
    def test_exact_weighted_comparison(self):
        for flip in (0,250,500,1000):
            r=a.exact_comparison(4,flip,42,8)
            for key in ("weight_mismatches","bellman_mismatches","dominance_violations","invalid_actions","causality_violations"):
                self.assertEqual(r[key],0)
    def test_baseline_replay_unchanged(self):
        for p in b.POLICIES:
            choose=a.decision_policy(p,250,42,8)
            for path in product((False,True),repeat=4):
                ref=b.episode(p,path,42,8,250)
                out=a.replay(path,choose)
                self.assertEqual({k:out[k] for k in ref},ref)
    def test_no_future_access(self):
        choose=a.decision_policy("adaptive",250,42,8)
        p=a.replay((False,False,True,True),choose)
        q=a.replay((False,False,False,False),choose)
        self.assertEqual(p["trace"][:2],q["trace"][:2])
    def test_bounded_domains(self):
        for flip in (-1,1001,True,0.5):
            with self.assertRaises(ValueError):a.controller(flip)
        solve=a.controller(250)
        for args in ((0,"dry",4,False),(21,"dry",4,False),(20,"dry",20,False),(4,"dry",4,1),(4,"dry",4,False,1)):
            with self.assertRaises(ValueError):solve(*args)
        with self.assertRaises(ValueError):a.exact_comparison(9,250,42,8)
    def test_long_controller_replay(self):
        path=(False,True)*10
        out=a.replay(path,a.decision_policy("adaptive",250,42,8))
        self.assertEqual(out["total_ms"],b.cost_plan(path,"dry",4,out["stop"],out["compound"]))
    def test_small_experiment_replay(self):
        spec=a.spec(lambda op,threshold:dict(op=op,threshold=threshold))
        config=dict(spec["config"],horizon=4,heldout=8,samples=8)
        r=a.evaluate(config)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
        self.assertEqual(r,a.evaluate(config))
        self.assertEqual(len(r["observations"]["rows"]),8)

if __name__=="__main__":unittest.main()
