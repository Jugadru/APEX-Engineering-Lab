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

## 0.7.4

`physics_brakes`: cap request by normal load times friction, exact forward step, stopping distance m*v²/(2F) (None if moving without braking), heat equals negative brake work, prescribed front/rear split, adiabatic temperature rise Q/C. 54 cases. Demand above grip is a saturation indicator, not actual wheel locking. No ABS, disc cooling, per-wheel slip or calibrated heat capacity. REF-107/IDEA-013/014/015 conceptual.

## 0.7.5

`physics_load`: longitudinal transfer m*ax*h/wheelbase, lateral m*ay*h/track, separate static and aero front fractions, positive ay transfers right. Clip infeasible axle/side load redistribution explicitly and report requested/realized values; proportionally distribute lateral transfer by axle load. 36 load cases. Separate unforced linear sprung-mass perturbation about static equilibrium, exact underdamped solution and energy/partition checks (12 cases). Not a dynamic four-wheel suspension, roll stiffness, unsprung mass, real track surface, or wheel-lift solver. REF-107/IDEA-006–009 concept only.

## 0.7.6

`physics_energy`: synthetic LHV 43 MJ/kg, fixed efficiencies; cap shaft offer by fuel and power*time, KERS source offer by request, 60 kW and remaining 400 kJ lap budget (from audited APEX era reference), stored energy. Convert offers to wheel energy. Allocate KERS-first, then combustion, debit only accepted work and record source losses, unmet demand and remaining fuel/store/lap. 162 cases. KERS limits here explicitly at source side; do not replace existing authority or assume regulatory equivalence. No idle burn, regeneration, refuel, automatic lap reset, pit state or 2012 measured data. REF-107/IDEA-001/002/005 conceptual.

## 0.7.7

`physics_vehicle`: pure forward step, frozen initial mass and force inputs, aero/load and thermal/wear grip factor, rear drive and load-proportional brake/lateral request, rigid gear and KERS offer with cut and brake precedence. Work constraint uses 48 fixed bisection iterations when necessary, retaining feasible lower endpoint; debit only accepted positive drive work once. Work-energy and source balance, zero dt, coast, empty store and brake precedence tested over 180 scenarios. Lateral demand is diagnostic only; no lateral motion, actual suspension integration, thermal state update, clutch, strategy, pit/traffic solver or race. KERS-first allocation and frozen power assumptions belong to toy reference, not Core 2/Hyper contract. No measured parameters. REF-107/IDEA-001/005/008/010/011/015 concept only.

The reference explicitly accepts dt=0 or 1 microsecond to 0.5 s. Power-to-force conversion uses a 1 m/s denominator floor at low positive speed, while zero speed still has no launch drive. This is a numerical convention, not calibrated launch dynamics; original fixture criteria remain unchanged.
