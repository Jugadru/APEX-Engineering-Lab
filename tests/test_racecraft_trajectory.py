import unittest
from engineering_lab import racecraft_trajectory as t, experimental as e
class TrajectoryTests(unittest.TestCase):
    def test_straight(self):
        r=t.optimize([[-2000,0,2000]]*5,[0]*5,2000)
        self.assertEqual(r["path_mm"],[0]*5); self.assertEqual(r["cost_mm2"],0)
    def test_infeasible(self):
        self.assertIsNone(t.optimize([[-2000],[2000]],[0,0],2000)["path_mm"])
        self.assertIsNone(t.optimize([[0],[],[0]],[0]*3,2000)["path_mm"])
    def test_lexicographic(self):
        self.assertEqual(t.optimize([[1,-1],[1,-1]],[0,0],0)["path_mm"],[-1,-1])
    def test_cost(self):
        self.assertEqual(t.score([0,1,0],[0,0,0]),11)
    def test_forced(self):
        self.assertEqual(t.optimize([[-2000],[0],[2000]],[0]*3,2000)["path_mm"],[-2000,0,2000])
    def test_invalid(self):
        for a,b,c in [([[0],[0,0]],[0,0],1),([[0],[0]],[0],1),([[0],[1]],[0,0],True),([[0]]*8,[0]*8,1)]:
            with self.assertRaises(ValueError): t.optimize(a,b,c)
    def test_fixture(self):
        r=t.evaluate(e.specs()["racecraft_trajectory"]["config"])
        self.assertEqual(r["observations"]["cases"],29)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
if __name__=="__main__": unittest.main()
