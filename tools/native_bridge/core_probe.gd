extends SceneTree
const Adapter = preload("res://experimental/apex2/scenario_adapter.gd")
const Replay = preload("res://scripts/core/race_replay_0660.gd")
const TICKS = 100
const SEED = 2026
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var rows: Array = []
	for spec in [["ITA","Seco"],["GBR","Chuva intensa"]]:
		var pair: Dictionary = Adapter.create_pair(str(spec[0]),str(spec[1]),SEED)
		if pair.is_empty(): quit(1); return
		var race = pair.core
		var s: Dictionary = pair.scenario
		var session = Replay.new()
		session.attach(race)
		var start_ms: int = roundi(float(race.clock)*1000)
		var start: int = Time.get_ticks_usec()
		for i in range(TICKS):
			if not session.step_tick(): quit(1); return
		var elapsed: int = Time.get_ticks_usec()-start
		var final: Array = []
		for car in race.cars:
			final.append({"id":int(car.id),"progress_units":roundi(float(car.progress)*1000000.0)})
		final.sort_custom(func(a: Dictionary,b: Dictionary)->bool:return int(a.id)<int(b.id))
		rows.append({"track":str(spec[0]),"weather":str(spec[1]),"seed":SEED,"ticks":session.tick,
			"elapsed_sim_ms":roundi(float(race.clock)*1000)-start_ms,"initial":s.cars,"length_mm":s.lap_length_mm,
			"final":final,"hash":str(session.hashes[-1]),"elapsed_cpu_usec":elapsed,"commands":[]})
	print("APEX_BRIDGE_RESULT ",JSON.stringify({"engine":"Core2","rows":rows}))
	quit(0)
