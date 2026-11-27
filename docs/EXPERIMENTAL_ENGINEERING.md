# Experimental Engineering 0.6 series

Original isolated Python standard-library prototypes, no external source copied, no game runtime or new profiler. Audited Core 2 e118f6289753adbd151bd23e4e4b1cce8ac45bed: race_space_0655.gd tactical_neighbors scans frozen signed gaps, resolve_physical observes live reductions (do not substitute index there); race_merge_traffic_0669174.gd has signed wrap and priority; historical qa/core2_06686 benchmark shows existing optimization. race_longitudinal_069.gd already integrates constant rate with target; race_strategy_simulator_06499.gd already estimates six pit entries. Hyper ef280b0c43e2f56348fabee5765b8285ead4c4c8 has its own kernels. Development Lab benchmarks remain authoritative. Foundation 1c226891f24796d0a14535693d32f626a5b476f5 catalog blobs unchanged, IDs checked; sources conceptual only.

`python -m engineering_lab experiment-list` lists fixed hypotheses and configuration. `python -m engineering_lab experiment-run ordered_commands --id EXP-ORDER-001 --registry /tmp/new-experiment` requires clean Git checkout, uses actual HEAD, new directory outside checkout. Register v1 plan and config before evaluation; output immutable result and observation artifact, verify bytes using existing verify. Same SHA baseline/candidate means different algorithms in same Lab revision, not game A/B. No arbitrary executor, external dependencies or heavy workload. Local files are not signed; abnormal interruption leaves plan without result (NOT_RUN/unfinished), no silent retry. Seeded Python PRNG, deterministic integer fixture; no statistical claim about real racing. CI checks actual head SHA. No game changes.

0.6.0: order frozen 24-agent commands by priority then stable ID; 32 permutations must match. This is a narrow synthetic RES-001 fixture, not the production racecraft engine.

## 0.6.1

`experiment-run spatial_neighbors`: original integer-metre circular index, inclusive radius 0/38/100/2500 m, 24 cars, six layouts (uniform, grid, clustered, wrap, coincident, spread). Exact output against exhaustive scan, stable IDs, no extra rows relative to scan. Row counts exclude build/sort, binary search, allocation and elapsed time; dense queries may visit all rows. No production floating gap epsilon, lap priority, eligibility, wake ordering, lane geometry or live physical resolution equivalence. Research link REF-105/IDEA-033 concept only. Do not replace race_space solver.

## 0.6.2

`experiment-run longitudinal_math`: F/m, v=v0+a*t and x=v0*t+a*t²/2; compare trapezoid integration against analytical reference and report Euler error (not a gate). 3 masses, 3 forces, 3 step counts; tolerance 1e-10 m and m/s, finite observations and mass monotonicity. Artificial constants, no vehicle validation. Core 2 already has constant-rate ramp with target; do not duplicate in runtime. REF-107/IDEA-005 concept only.

## 0.6.3

`experiment-run mass_grip_sensitivity`: a=min(F/m,mu*g) in SI, 4 masses × 5 coefficients × 2 forces. All 40 cases checked for limits and monotonicity, both regimes must occur. Report endpoint effects at fixed other factors and regime counts; no causal/statistical inference about F1. No combined longitudinal/lateral grip, aero, thermal, weight transfer or 2012 calibration. REF-107/IDEA-005/015 concept only.

## 0.6.4

`experiment-run pit_cost_comparison`: synthetic 8-lap horizon, single mandatory stop after lap 1..6. Cost = sum old tyre laps + sum fresh tyre laps + pit penalty (integer milliseconds internally, seconds reported). Direct sums vs prefix sums must be exactly equal for all 97 cases; count model-level additions including prefix construction, not CPU time. One nominal policy and one policy selected from 32 sampled scenarios; freeze both choices before generating 64 heldout scenarios from independent seed. Hindsight oracle only evaluates regret; retain positive or negative regret delta without using it as a gate. No real 2012 calibration, dynamic safety-car, weather, pit occupancy, double stack or race logic. REF-106/IDEA-041/045/048 conceptual link; no copied code. Current Core 2 strategy simulator remains authoritative.

## 0.6.5

`experiment-report --registry PATH --id EXP-ID` revalidates the plan, config, result, bytes and observation bindings. `experiment-suite-report --entry PATH ID --entry PATH ID --output NEW.json --markdown NEW.md` summarizes supplied entries only, requires same exact revision, rejects duplicate experiments, preserves incomplete/adverse states and exploratory observations in JSON. Markdown reports frozen criteria and observed values; JSON retains full per-case data. Outputs are exclusive, not a multi-file transaction. A missing result is NOT_RUN, aggregate INCONCLUSIVE. Reports do not authenticate authorship, re-execute, infer FPS or authorize promotion. Hosted job executes five bounded experiments on exact candidate SHA and archives reports. No game edits.
