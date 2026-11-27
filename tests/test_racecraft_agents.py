import unittest
from engineering_lab import racecraft_agents as a, racecraft_core as c, racecraft_collision as col, experimental as e
class AgentTests(unittest.TestCase):
    def solve(self,rows,props):
        return a.resolve(c.Snapshot.from_rows(0,5000000,5000,rows),props)
    def test_swap(self):
        r=self.solve([c.row(1,100000,-3000),c.row(2,100000,3000)],{1:col.endpoint(110000,3000),2:col.endpoint(110000,-3000)})
        self.assertEqual(r["vetoed_ids"],[1,2]); self.assertEqual(r["new_contacts"],[])
    def test_chain(self):
        r=self.solve([c.row(1,100000),c.row(2,110000),c.row(3,120000)],{1:col.endpoint(110000,0),2:col.endpoint(120000,0),3:col.endpoint(120000,0)})
        self.assertEqual(r["vetoed_ids"],[1,2,3]); self.assertGreaterEqual(r["rounds"],2)
    def test_parallel(self):
        r=self.solve([c.row(1,100000,-3000),c.row(2,100000,3000)],{1:col.endpoint(110000,-3000),2:col.endpoint(110000,3000)})
        self.assertEqual(r["vetoed_ids"],[])
    def test_initial(self):
        r=self.solve([c.row(1,100000),c.row(2,100000)],{1:col.endpoint(110000,0),2:col.endpoint(120000,0)})
        self.assertEqual(r["status"],"INITIAL_STATE_INVALID")
        self.assertEqual(r["initial_contacts"],[[1,2]])
        self.assertEqual([x["progress_mm"] for x in r["endpoints"]],[100000,100000])
    def test_edge(self):
        r=self.solve([c.row(1,100000)],{1:col.endpoint(110000,4500)})
        self.assertEqual(r["vetoed_ids"],[1]); self.assertEqual(r["status"],"GEOMETRICALLY_FEASIBLE")
    def test_roster(self):
        with self.assertRaises(ValueError): self.solve([c.row(1,0),c.row(2,0,active=False)],{1:col.endpoint(0,0),2:col.endpoint(0,0)})
        with self.assertRaises(ValueError): self.solve([c.row(1,0)],{})
    def test_fixture(self):
        r=a.evaluate(e.specs()["racecraft_multi_agent"]["config"])
        self.assertEqual(r["observations"]["cases"],21)
        self.assertTrue(all(v==0 for v in r["metrics"].values()))
if __name__=="__main__": unittest.main()
