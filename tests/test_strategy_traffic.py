import unittest
from dataclasses import replace
from engineering_lab import strategy_traffic as t, strategy_window as w, strategy_duel as d

class TrafficTests(unittest.TestCase):
    def state(self):
        return t.State(w.State(d.Snapshot(0,4,4,(24000,24000)),"medium",(False,),True),
            (t.Car("medium",8),t.Car("hard",12,500)))

    def test_clear_and_faster_field(self):
        for field in ([],[(-1,93000)],[(0,89000)],[(0,90000)],[(5000,91000)]):
            self.assertEqual(t.loss(90000,field),dict(loss_ms=0,affected=0,clear=True))

    def test_gap_gradient_and_catch_boundary(self):
        vals=[t.loss(90000,[(g,91000)])["loss_ms"] for g in (0,1000,2000,2999,3000)]
        self.assertEqual(vals,[1000,1000,500,0,0])
        self.assertFalse(t.loss(90000,[(2999,91000)])["clear"])
        self.assertTrue(t.loss(90000,[(3000,91000)])["clear"])

    def test_density_and_cap(self):
        one=t.loss(90000,[(2000,91000)])
        two=t.loss(90000,[(2000,91000),(2000,91000)])
        self.assertGreater(two["loss_ms"],one["loss_ms"])
        self.assertEqual(t.loss(90000,[(0,150000)]*5)["loss_ms"],3000)

    def test_permutation_and_reference(self):
        field=[(2400,92000),(0,91000),(-1,99000)]
        a=t.loss(90000,field)
        self.assertEqual(a,t.loss(90000,list(reversed(field))))
        self.assertEqual(tuple(a[k] for k in ("loss_ms","affected","clear")),t.reference_loss(90000,field))

    def test_invalid_inputs(self):
        for own,field in ((True,[]),(90000,[(False,92000)]),(90000,[(0,-1)]),(90000,[(0,92000)]*6)):
            with self.assertRaises(ValueError):t.loss(own,field)
        with self.assertRaises(ValueError):t.validate(replace(self.state(),background=()))
        with self.assertRaises(ValueError):t.outcome(self.state(),(True,"soft"),(False,)*4,(1,500))

    def test_ledger(self):
        s=self.state();p=(0,"soft");path=(False,)*4;rival=(1,500)
        x=t.outcome(s,p,path,rival)
        m=dict(step_mismatches=0,bound_violations=0,order_violations=0,accounting_mismatches=0)
        t.audit(s,p,path,rival,x,m)
        self.assertTrue(all(v==0 for v in m.values()))
        self.assertGreater(x["traffic_ms"],0)
        self.assertFalse(x["exit_clear"])

    def test_manual_and_optional(self):
        s=self.state()
        locked=replace(s,window_state=replace(s.window_state,manual=2))
        self.assertEqual(t.choose(locked)["plan"][0],2)
        optional=replace(s,window_state=replace(s.window_state,required=False))
        self.assertIn(w.NONE,t.validate(optional))
        self.assertIsNone(t.outcome(optional,w.NONE,(False,)*4,(1,500))["exit_clear"])

    def test_fixture(self):
        cfg=dict(t.spec(lambda op,v:dict(op=op,threshold=v))["config"],cases=3)
        result=t.evaluate(cfg)
        self.assertTrue(all(v==0 for v in result["metrics"].values()))
        self.assertEqual(result,t.evaluate(cfg))
