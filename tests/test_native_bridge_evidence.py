import unittest
import json
from pathlib import Path
from copy import deepcopy
from engineering_lab import native_bridge_evidence as n

def record(engine):
    rows=[]
    for track,weather in n.CASES:
        initial=[dict(id=i,name=str(i),team="fixture",grid=i,tire="Macio",progress_units=-i) for i in range(24)]
        rows.append(dict(track=track,weather=weather,seed=2026,ticks=100,elapsed_sim_ms=20000,commands=[],
                    initial=initial,length_mm=5000000,final=[dict(id=i,progress_units=1000-i) for i in range(24)],
                    hash="a"*64,elapsed_cpu_usec=1000))
    return dict(engine=engine,rows=rows)

class BridgeTests(unittest.TestCase):
    def test_match_is_not_equivalence(self):
        a,b=record("Core2"),record("Hyper301")
        b["rows"][0]["final"][0]["progress_units"]+=30
        result=n.compare(a,b)
        self.assertEqual(result["rows"][0]["max_abs_progress_delta_units"],30)
        self.assertEqual(result["model_equivalence"],"NOT_ESTABLISHED")
    def test_mismatched_grid(self):
        a,b=record("Core2"),record("Hyper301")
        b["rows"][0]["initial"][0]["progress_units"]+=1
        with self.assertRaises(ValueError): n.compare(a,b)
    def test_mismatched_clock(self):
        a,b=record("Core2"),record("Hyper301")
        b["rows"][0]["elapsed_sim_ms"]=19999
        with self.assertRaises(ValueError): n.compare(a,b)
    def test_mismatched_commands(self):
        a,b=record("Core2"),record("Hyper301")
        b["rows"][0]["commands"]=["pace"]
        with self.assertRaises(ValueError): n.compare(a,b)
    def test_preserved_real_native_records(self):
        data=json.loads((Path(__file__).resolve().parents[1]/"audit/native_bridge_matched_grid_2012.json").read_text(encoding="utf-8"))
        r=n.verify_archive(data,data["core"])
        self.assertEqual(r["hyper_evidence"],"PINNED_PREVIOUS_NATIVE_RUN")
        self.assertEqual([x["max_abs_progress_delta_units"] for x in r["rows"]],[74156,26195])
        self.assertEqual(r["model_equivalence"],"NOT_ESTABLISHED")
        altered=deepcopy(data["core"])
        altered["rows"][0]["hash"]="f"*64
        with self.assertRaises(ValueError): n.verify_archive(data,altered)
        altered=deepcopy(data)
        altered["source_runs"]["hyper"]+=1
        with self.assertRaises(ValueError): n.verify_archive(altered,data["core"])

if __name__=="__main__": unittest.main()
