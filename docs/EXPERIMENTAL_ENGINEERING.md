# Experimental Engineering 0.6 series

Original isolated Python standard-library prototypes, no external source copied, no game runtime or new profiler. Audited Core 2 e118f6289753adbd151bd23e4e4b1cce8ac45bed: race_space_0655.gd tactical_neighbors scans frozen signed gaps, resolve_physical observes live reductions (do not substitute index there); race_merge_traffic_0669174.gd has signed wrap and priority; historical qa/core2_06686 benchmark shows existing optimization. race_longitudinal_069.gd already integrates constant rate with target; race_strategy_simulator_06499.gd already estimates six pit entries. Hyper ef280b0c43e2f56348fabee5765b8285ead4c4c8 has its own kernels. Development Lab benchmarks remain authoritative. Foundation 1c226891f24796d0a14535693d32f626a5b476f5 catalog blobs unchanged, IDs checked; sources conceptual only.

`python -m engineering_lab experiment-list` lists fixed hypotheses and configuration. `python -m engineering_lab experiment-run ordered_commands --id EXP-ORDER-001 --registry /tmp/new-experiment` requires clean Git checkout, uses actual HEAD, new directory outside checkout. Register v1 plan and config before evaluation; output immutable result and observation artifact, verify bytes using existing verify. Same SHA baseline/candidate means different algorithms in same Lab revision, not game A/B. No arbitrary executor, external dependencies or heavy workload. Local files are not signed; abnormal interruption leaves plan without result (NOT_RUN/unfinished), no silent retry. Seeded Python PRNG, deterministic integer fixture; no statistical claim about real racing. CI checks actual head SHA. No game changes.

0.6.0: order frozen 24-agent commands by priority then stable ID; 32 permutations must match. This is a narrow synthetic RES-001 fixture, not the production racecraft engine.

## 0.6.1

`experiment-run spatial_neighbors`: original integer-metre circular index, inclusive radius 0/38/100/2500 m, 24 cars, six layouts (uniform, grid, clustered, wrap, coincident, spread). Exact output against exhaustive scan, stable IDs, no extra rows relative to scan. Row counts exclude build/sort, binary search, allocation and elapsed time; dense queries may visit all rows. No production floating gap epsilon, lap priority, eligibility, wake ordering, lane geometry or live physical resolution equivalence. Research link REF-105/IDEA-033 concept only. Do not replace race_space solver.

## 0.6.2

`experiment-run longitudinal_math`: F/m, v=v0+a*t and x=v0*t+a*t²/2; compare trapezoid integration against analytical reference and report Euler error (not a gate). 3 masses, 3 forces, 3 step counts; tolerance 1e-10 m and m/s, finite observations and mass monotonicity. Artificial constants, no vehicle validation. Core 2 already has constant-rate ramp with target; do not duplicate in runtime. REF-107/IDEA-005 concept only.
