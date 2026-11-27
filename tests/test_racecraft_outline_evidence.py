import unittest
from engineering_lab import racecraft_outline_evidence as o

class OutlineTests(unittest.TestCase):
    def test_length_and_direction(self):
        pts=[0j,1+0j,1+1j,1j,0j]
        for direction in ("CLOCKWISE","ANTI_CLOCKWISE"):
            p=o.reconstruct(pts,400,direction)
            self.assertEqual([x[0] for x in p],[0,100,200,300,400])
            self.assertEqual(p[0][1:],p[-1][1:])
            area=sum(a[1]*b[2]-a[2]*b[1] for a,b in zip(p,p[1:]))
            self.assertEqual(area<0,direction=="CLOCKWISE")
    def test_open_rejected(self):
        with self.assertRaises(ValueError):o.reconstruct([0j,1+0j,1+1j,1j],400,"CLOCKWISE")
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):o.reconstruct([0j,1+0j,1+0j,1+1j,1j,0j],400,"CLOCKWISE")
    def test_offsets_have_sources(self):
        self.assertEqual({k:v["start_finish_offset_m"] for k,v in o.FACTS.items()},{"EUR":0,"KOR":195,"IND":251})
        self.assertTrue(all(v["source"].startswith("https://www.fia.com/") for v in o.FACTS.values()))
if __name__=="__main__":unittest.main()
