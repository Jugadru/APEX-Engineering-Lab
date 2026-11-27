# Physics Research Lab — series 0.7

Independent original SI analytical references, not a new game engine. Audited Core 2 e118f6289753adbd151bd23e4e4b1cce8ac45bed docs APEX_069_LONGITUDINAL_PHYSICS, APEX_070_POWERTRAIN, APEX_0701_FUEL_MASS, APEX_071_TYRE_GRIP, APEX_072_VEHICLE_DYNAMICS and scripts race_tyre_thermal/race_aero_wake. Core 2 retains authority over vehicle state, KERS/DRS, fuel, tyre wear/heat, pit, replay, racecraft and solver. Hyper ef280b0c43e2f56348fabee5765b8285ead4c4c8 has separate longitudinal adapter and integer V8 prototype. Foundation 1c226891f24796d0a14535693d32f626a5b476f5 physics IDEA-001–020 and REF-107 conceptual references, not measured data. No copied source or proprietary telemetry. 2012 constraints are context, not calibration.

Run from clean Git checkout: `python -m engineering_lab experiment-physics-suite --registry /tmp/new-physics-suite`. Each named physics fixture uses existing frozen plan/config/result and verified artifacts; suite output JSON/Markdown at same actual HEAD. Fixed bounded experiments only; no game execution. Preserve adverse results; if unexpected exception, CI fails and retains available artifacts. Synthetic acceptance is not scientific authentication or gameplay approval. All coefficients artificial. Python version/OS/architecture recorded in workload environment.

## 0.7.0
Constant net force, exact step until stop, no reverse motion; work-energy equality using factored difference of squares, nonnegative displacement, dt zero, acceleration and braking. 54 fixed combinations, relative residual <=1e-10; input finite bounded SI domain, no hidden clamp of invalid input. No integration into Core 2 or Hyper.

Roadmap: 0.7.1 tyre, 0.7.2 aero, 0.7.3 powertrain, 0.7.4 braking, 0.7.5 load transfer, 0.7.6 fuel/energy, 0.7.7 integration, 0.7.8 numerical validation. Each a separate candidate and criterion.
