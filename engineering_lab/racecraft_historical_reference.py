"""Minimal manually cross-checked factual references; not telemetry or a dataset scraper."""
from decimal import Decimal
from . import registry as reg

SOURCES={
    "calendar":"https://www.fia.com/news/2012-fia-formula-one-world-championship",
    "fastest_laps":"https://www.formula1.com/en/results/2012/awards/fastest-laps",
    "usa_race":"https://www.formula1.com/en/results/2012/races/26/united-states/fastest-laps",
    "usa_later_fia":"https://api.fia.com/news/2013-united-states-grand-prix-preview"}
# FIA February media calendar; code aliases aligned with Core 2; metres.
CALENDAR={"AUS":5303,"MAL":5543,"CHN":5451,"BHR":5412,"ESP":4655,"MON":3340,"CAN":4361,
          "EUR":5419,"GBR":5891,"GER":4574,"HUN":4381,"BEL":7004,"ITA":5793,"SIN":5073,
          "JPN":5807,"KOR":5615,"IND":5125,"UAE":5554,"USA":5516,"BRA":4309}
# F1 official season fastest lap results, expressed as integer milliseconds.
FASTEST_MS={"AUS":89187,"MAL":100722,"CHN":99960,"BHR":96379,"ESP":86250,"MON":77296,
            "CAN":75752,"EUR":102163,"GBR":94661,"GER":78725,"HUN":84136,"BEL":112822,
            "ITA":87239,"SIN":111033,"JPN":95774,"KOR":102037,"IND":88203,"UAE":103964,
            "USA":99347,"BRA":78069}
F1DB_SHA="9dbbb9f67dc5fa3d499061efb56d24aa4f1e261d"
LAYOUTS={
 "EUR":dict(id="valencia-1",race="08-europe",race_blob="640bd717c51b46586e6dbe3dfddd6a5b5fd6a7ef",svg_blob="915aa81f13d666db138e3916f87a18607ef6ea53",length_m=5419),
 "KOR":dict(id="yeongam-1",race="16-korea",race_blob="8d7b84363e17a85b0b62247ac6b19cd7722302ed",svg_blob="3ffb699af7c01382f856b56a86e9306b06c9f156",length_m=5615),
 "IND":dict(id="buddh-1",race="17-india",race_blob="fb0b7aab4450360ae4350cf5bca6908d50d2db52",svg_blob="bb34432ab66ff486b70ba15a691530d6af3cf5fb",length_m=5125)}

def lap_ms(s):
    reg.require(reg.match(s,r"[0-9]{1,2}:[0-5][0-9]\.[0-9]{3}"),"invalid lap time")
    m,rest=s.split(":");sec,ms=rest.split(".")
    return int(m)*60000+int(sec)*1000+int(ms)

def exact_scaled(v,scale):
    reg.require(reg.numeric(v),"invalid numeric reference")
    x=Decimal(str(v))*scale
    reg.require(x==int(x),"unexpected precision")
    return int(x)

def compare(tracks):
    reg.require(isinstance(tracks,list) and len(tracks)==20,"track roster")
    reg.require(all(isinstance(t,dict) and t.get("code") in CALENDAR for t in tracks) and len({t["code"] for t in tracks})==20,"unique codes")
    rows=[]
    # Explicitly preserve the early calendar discrepancy. Race lap average
    # speed and time imply 5.5129858 km; later FIA preview lists 5.513 km.
    implied=Decimal("99.347")*Decimal("199.772")/Decimal("3.6")
    for t in sorted(tracks,key=lambda x:x["code"]):
        code=t["code"];game_m=exact_scaled(t["lap_km"],1000)
        official=FASTEST_MS[code];actual=lap_ms(t["fastest_lap_2012"])
        base=exact_scaled(t["base_lap"],1000)
        expected=5513 if code=="USA" else CALENDAR[code]
        rows.append(dict(code=code,game_m=game_m,calendar_m=CALENDAR[code],reviewed_reference_m=expected,
                         fastest_ms=actual,official_fastest_ms=official,gameplay_buffer_ms=base-actual,
                         length_matches=game_m==expected,fastest_matches=actual==official,buffer_matches=base-actual==500))
    errors=sum(not row[k] for row in rows for k in ("length_matches","fastest_matches","buffer_matches"))
    return dict(status="PASS" if not errors else "FAIL",kind="DOCUMENTARY_REFERENCE_COMPARISON",errors=errors,
                fastest_matches=sum(r["fastest_matches"] for r in rows),length_matches=sum(r["length_matches"] for r in rows),
                buffer_matches=sum(r["buffer_matches"] for r in rows),
                usa_pre_race_calendar_m=CALENDAR["USA"],usa_race_implied_length_m=float(implied),
                sources=SOURCES,rows=rows,calibration="NOT_PERFORMED",
                missing_outline_references={"repo":"f1db/f1db","sha":F1DB_SHA,"license":"CC-BY-4.0 (repository notice checked; downstream rights not independently verified)",
                  "license_blob":"4ea99c213c5c0c005ae4e80df8e52169d06896ec","layouts":LAYOUTS,
                  "status":"DOCUMENTARY_SOURCE_IDENTIFIED_NOT_IMPORTED","limitations":"SVG outlines tied to 2012 race metadata; no metric width/elevation or survey validation. No assets copied or game files modified."})

