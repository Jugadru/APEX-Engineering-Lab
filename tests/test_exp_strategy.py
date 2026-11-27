import random
import unittest
from engineering_lab import exp_strategy as s, experimental as e
class StrategyTests(unittest.TestCase):
    def test_costs(self):
        x={"old":[10,20,30],"fresh":[5,6,7],"pit":[100,200,300]}
        self.assertEqual(s.direct(x,[1,2]),[121,235])
        self.assertEqual(s.indexed(x,[1,2]),[121,235])
    def test_tie(self):
        self.assertEqual(s.best([5,5],[2,3]),2)
    def test_random_equivalence(self):
        rng=random.Random(123)
        for _ in range(20):
            x=s.scenario(rng,8)
            self.assertEqual(s.direct(x,list(range(1,8))),s.indexed(x,list(range(1,8))))
    def test_experiment(self):
        config=e.specs()["pit_cost_comparison"]["config"]
        r=s.evaluate(config)
        self.assertEqual(r["observations"]["scenarios"],97)
        self.assertEqual(r["metrics"]["cost_mismatches"],0)
        self.assertEqual(r["metrics"]["invalid_actions"],0)
        self.assertLess(r["metrics"]["extra_additions"],0)
        self.assertEqual(r,s.evaluate(config))
    def test_heldout_not_used_for_choice(self):
        config=e.specs()["pit_cost_comparison"]["config"]
        a=s.evaluate(config)["observations"]
        b=s.evaluate(dict(config,heldout=1))["observations"]
        self.assertEqual((a["nominal_entry"],a["sampled_entry"]),(b["nominal_entry"],b["sampled_entry"]))
    def test_invalid_entries(self):
        config=e.specs()["pit_cost_comparison"]["config"]
        with self.assertRaises(ValueError): s.evaluate(dict(config,entries=[0,8]))
    def test_budget(self):
        config=e.specs()["pit_cost_comparison"]["config"]
        with self.assertRaises(ValueError): s.evaluate(dict(config,heldout=129))
    def test_nonnegative_regret(self):
        r=s.evaluate(e.specs()["pit_cost_comparison"]["config"])["observations"]
        self.assertTrue(all(v>=0 for v in r["nominal_regret_s_by_case"]+r["sampled_regret_s_by_case"]))
if __name__=="__main__": unittest.main()
