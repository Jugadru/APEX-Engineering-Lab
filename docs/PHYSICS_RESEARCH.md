# Physics Research Lab — series 0.7

Independent original SI analytical references, not a new game engine. Audited Core 2 e118f6289753adbd151bd23e4e4b1cce8ac45bed docs APEX_069_LONGITUDINAL_PHYSICS, APEX_070_POWERTRAIN, APEX_0701_FUEL_MASS, APEX_071_TYRE_GRIP, APEX_072_VEHICLE_DYNAMICS and scripts race_tyre_thermal/race_aero_wake. Core 2 retains authority over vehicle state, KERS/DRS, fuel, tyre wear/heat, pit, replay, racecraft and solver. Hyper ef280b0c43e2f56348fabee5765b8285ead4c4c8 has separate longitudinal adapter and integer V8 prototype. Foundation 1c226891f24796d0a14535693d32f626a5b476f5 physics IDEA-001–020 and REF-107 conceptual references, not measured data. No copied source or proprietary telemetry. 2012 constraints are context, not calibration.

Run from clean Git checkout: `python -m engineering_lab experiment-physics-suite --registry /tmp/new-physics-suite`. Each named physics fixture uses existing frozen plan/config/result and verified artifacts; suite output JSON/Markdown at same actual HEAD. Fixed bounded experiments only; no game execution. Preserve adverse results; if unexpected exception, CI fails and retains available artifacts. Synthetic acceptance is not scientific authentication or gameplay approval. All coefficients artificial. Python version/OS/architecture recorded in workload environment.

## 0.7.0
Constant net force, exact step until stop, no reverse motion; work-energy equality using factored difference of squares, nonnegative displacement, dt zero, acceleration and braking. 54 fixed combinations, relative residual <=1e-10; input finite bounded SI domain, no hidden clamp of invalid input. No integration into Core 2 or Hyper.

Roadmap: 0.7.1 tyre, 0.7.2 aero, 0.7.3 powertrain, 0.7.4 braking, 0.7.5 load transfer, 0.7.6 fuel/energy, 0.7.7 integration, 0.7.8 numerical validation. Each a separate candidate and criterion.

## 0.7.1

`physics_tyre`: independent radial projection into friction ellipse (zero-load/zero-axis safe), exact one-node thermal equation C*dT/dt=Q-h(T-Ta) in kelvin, irreversible saturating energy-proxy wear and artificial temperature/wear grip modifier. 45 grip, 18 partition and 9 wear cases. No pressure, slip curve, two-node temperature, measured Pirelli bands, graining/blistering or runtime ledger replacement; Core 2 already owns those effects. No compound calibration. REF-107/IDEA-015/016/017 concept only.

## 0.7.2

`physics_aero`: q=rho*v²/2, drag=q*CdA*(1-loss), positive downforce=q*ClA*(1-loss), power=drag*v. 48 cases, zero air density/speed, independent modifiers, quadratic forces and cubic power verified. Loss fractions are prescribed synthetic inputs, not computed slipstream, DRS permission or dirty-air geometry. Core 2 retains single wake source and aerodynamic authority. No CFD, ride-height model or measured 2012 coefficients. REF-107/IDEA-010/011 concept only.

## 0.7.3

`physics_powertrain`: original artificial torque interpolation, seven total ratios, 18000 RPM limiter used as era reference from the audited APEX powertrain documentation, not independently revalidated regulation. omega=v/r*ratio, P=T*omega, wheel force=T*ratio*eta/r; apply prescribed cut duty to average output. 210 cases (7 gears, 5 speeds, 2 throttles, 3 cuts). Zero at rest intentionally: rigid gear without clutch cannot model launch. No autonomous shift controller, KERS or proprietary engine curve. REF-107/IDEA-001–004 concept only. Core 2 and Hyper powertrain remain separate.
