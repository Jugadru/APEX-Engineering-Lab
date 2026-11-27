"""Evidence flags for selected 2012 FIA driving clauses, never automatic penalties."""
from . import registry as reg, racecraft_core as core

SOURCE="https://argent.fia.com/web/fia-public.nsf/A0C5392CB79B3323C1257A85004FFAA9/$FILE/2012%20SPORTING%20REGULATIONS%2009-03-2012.pdf"
BOOL_FIELDS=("off_track","deliberate_exit","justified_exit","rejoined","safe_rejoin","advantage_gained",
             "returning_before_corner","deliberate_crowding","abnormal_direction_change",
             "being_lapped","first_available_opportunity","yielded")
INT_FIELDS=("defensive_moves","room_mm","car_width_mm")

def validate(o):
    reg.exact(o," ".join(BOOL_FIELDS+INT_FIELDS))
    for k in BOOL_FIELDS:
        reg.require(o[k] is None or type(o[k]) is bool,"invalid observation "+k)
    for k in INT_FIELDS:
        if o[k] is not None:
            core.integer(o[k],1 if k=="car_width_mm" else 0,100 if k=="defensive_moves" else 30000,k)
    reg.require(not (o["off_track"] is False and (o["rejoined"] is True or o["deliberate_exit"] is True)),"contradictory track observation")
    reg.require(not (o["defensive_moves"]==0 and o["returning_before_corner"] is True),"contradictory defense observation")

def result(article,signals,unknown):
    return dict(article=article,status="REVIEW_REQUIRED" if signals else "INCONCLUSIVE" if unknown else "NO_SIGNAL_IN_DECLARED_OBSERVATIONS",
                signals=signals,missing=unknown)

def review(o):
    validate(o)
    signals=[];unknown=[]
    def need(*keys):
        unknown.extend(k for k in keys if o[k] is None)
    need("off_track")
    if o["off_track"] is True:
        need("deliberate_exit","rejoined")
        if o["deliberate_exit"] is True:
            need("justified_exit")
            if o["justified_exit"] is False:signals.append("UNJUSTIFIED_DELIBERATE_EXIT")
        if o["rejoined"] is True:
            need("safe_rejoin","advantage_gained")
            if o["safe_rejoin"] is False:signals.append("UNSAFE_REJOIN")
            if o["advantage_gained"] is True:signals.append("REJOIN_ADVANTAGE")
    rows=[result("20.2",signals,unknown)]
    signals=[];unknown=[]
    need("defensive_moves","returning_before_corner")
    if o["defensive_moves"] is not None and o["defensive_moves"]>1:signals.append("MULTIPLE_DEFENSIVE_DIRECTION_CHANGES")
    if o["returning_before_corner"] is True:
        need("room_mm","car_width_mm")
        if o["room_mm"] is not None and o["car_width_mm"] is not None and o["room_mm"]<o["car_width_mm"]:
            signals.append("INSUFFICIENT_RETURN_ROOM")
    rows.append(result("20.3",signals,unknown))
    signals=[];unknown=[]
    need("deliberate_crowding","abnormal_direction_change")
    if o["deliberate_crowding"] is True:signals.append("DELIBERATE_CROWDING")
    if o["abnormal_direction_change"] is True:signals.append("ABNORMAL_DIRECTION_CHANGE")
    rows.append(result("20.4",signals,unknown))
    signals=[];unknown=[]
    need("being_lapped")
    if o["being_lapped"] is True:
        need("first_available_opportunity")
        if o["first_available_opportunity"] is True:
            need("yielded")
            if o["yielded"] is False:signals.append("LAPPED_CAR_DID_NOT_YIELD")
    rows.append(result("20.5",signals,unknown))
    return dict(ruleset="FIA_2012_2012-03-09_SELECTED_CLAUSES",source=SOURCE,observations=rows,
                penalty="NOT_DECIDED",meaning="DECLARED_EVENT_REVIEW_NOT_STEWARD_ADJUDICATION")

def observation(**kw):
    return {**dict.fromkeys(BOOL_FIELDS,None),**dict.fromkeys(INT_FIELDS,None),**kw}

def baseline(**kw):
    return observation(off_track=False,defensive_moves=0,returning_before_corner=False,
                       deliberate_crowding=False,abnormal_direction_change=False,being_lapped=False,**kw)

def evaluate(config):
    # Fixed case matrix, expectations written independently of review output.
    cases=[
      ("normal",baseline(),{}),
      ("unknown",observation(),{"20.2":"INCONCLUSIVE","20.3":"INCONCLUSIVE","20.4":"INCONCLUSIVE","20.5":"INCONCLUSIVE"}),
      ("defense_once",dict(baseline(),defensive_moves=1),{}),
      ("defense_twice",dict(baseline(),defensive_moves=2),{"20.3":"REVIEW_REQUIRED"}),
      ("room_exact",dict(baseline(),defensive_moves=1,returning_before_corner=True,room_mm=1800,car_width_mm=1800),{}),
      ("room_short",dict(baseline(),defensive_moves=1,returning_before_corner=True,room_mm=1799,car_width_mm=1800),{"20.3":"REVIEW_REQUIRED"}),
      ("room_missing",dict(baseline(),defensive_moves=1,returning_before_corner=True,car_width_mm=1800),{"20.3":"INCONCLUSIVE"}),
      ("exit",dict(baseline(),off_track=True,deliberate_exit=True,justified_exit=False,rejoined=False),{"20.2":"REVIEW_REQUIRED"}),
      ("safe_return",dict(baseline(),off_track=True,deliberate_exit=False,rejoined=True,safe_rejoin=True,advantage_gained=False),{}),
      ("unsafe_return",dict(baseline(),off_track=True,deliberate_exit=False,rejoined=True,safe_rejoin=False,advantage_gained=True),{"20.2":"REVIEW_REQUIRED"}),
      ("crowding",dict(baseline(),deliberate_crowding=True),{"20.4":"REVIEW_REQUIRED"}),
      ("abnormal",dict(baseline(),abnormal_direction_change=True),{"20.4":"REVIEW_REQUIRED"}),
      ("no_opportunity",dict(baseline(),being_lapped=True,first_available_opportunity=False),{}),
      ("yielded",dict(baseline(),being_lapped=True,first_available_opportunity=True,yielded=True),{}),
      ("not_yielded",dict(baseline(),being_lapped=True,first_available_opportunity=True,yielded=False),{"20.5":"REVIEW_REQUIRED"}),
      ("unknown_yield",dict(baseline(),being_lapped=True,first_available_opportunity=True),{"20.5":"INCONCLUSIVE"})]
    mismatches=penalties=0;rows=[]
    for name,o,want in cases:
        r=review(o)
        mismatches+=sum(row["status"]!=want.get(row["article"],"NO_SIGNAL_IN_DECLARED_OBSERVATIONS") for row in r["observations"])
        penalties+=r["penalty"]!="NOT_DECIDED"
        rows.append(dict(case=name,observations=r["observations"]))
    return {"metrics":{"rule_signal_mismatches":mismatches,"automatic_penalties":penalties},
            "observations":{"cases":len(cases),"clause_checks":4*len(cases),"source":SOURCE,"rows":rows,
                            "limitations":"Selected clauses only. Human-labelled event evidence, no inference of intent, track width, opportunity or fault; no certification, steward decision or game integration."}}

def spec(c):
    return dict(hypothesis="Selected March 2012 driving clause review flags distinguish known counterexamples from missing observations without awarding penalties.",
         sources=["REF-168","IDEA-028","IDEA-029","IDEA-031","IDEA-034","IDEA-040"],config={"seed":42},
         criteria={"rule_signal_mismatches":c("eq",0),"automatic_penalties":c("eq",0)},evaluate=evaluate)
