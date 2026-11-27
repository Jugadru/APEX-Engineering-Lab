# Racecraft Research Lab — 0.8

Independent original synthetic references; not a second game engine. Audited Core 2 e118f6289753adbd151bd23e4e4b1cce8ac45bed: race_independent_racecraft_091710.gd (8dc73a11bd960203aede0de1e1e2ccd9a6868b3b) uses frozen observations, target commitment and timers, not opponent goals; race_space_0655.gd (d1427138fda7c610a31970d38e806f1dc471df6f) owns live sporting traffic in schematic units, corridor veto, pit clearance; race_merge_traffic_0669174.gd (a7bc3cf27a68cffc63b13656e25b9b3f4d03e0e8) separates signed gap and classified priority. Hyper ef280b0c43e2f56348fabee5765b8285ead4c4c8 racecraft_kernel_13.gd (8e9976bf4a915a4087b320a5e674edacf7f04420) already owns experimental tick plans and physically confirmed passes. Do not copy runtime code or replace either authority. Foundation pin 1c226891f24796d0a14535693d32f626a5b476f5, REF-105 and IDEA-031/033/034 conceptual only. No external code copied.

Run from clean checkout: python -m engineering_lab experiment-racecraft-suite --registry /tmp/new-racecraft. Reuses frozen plans/results/report; no arbitrary executable. Integer mm and mm/s are SI subunits in this Lab only, not direct mappings to schematic units. 0.8.0: bounded 1–24 car observations via Snapshot.from_rows, validated unique IDs, immutable canonical order, active subset only, classified progress and shortest signed periodic gap separate, half-track tie negative, ties by stable ID. At equal physical arc but different lap, classification is not physical order. No future target, command, RNG policy or motion. Inactive exclusion does not model pit or finished sporting classification. Four layouts, 128 permutations, 24-car fixtures. Exact candidate/main racecraft workflow required for future closures, not retroactive. All previous regression and 0.7 closure retained. This is a foundation, not complete Racecraft. No game validation or FPS.

## 0.8.1

`racecraft_spatial_awareness`: reuse exp_spatial.Ring with integer millimetres; separate active physical neighbors, same corridor front/rear and coincident IDs. TTC is floor of constant-speed positive closing estimate to buffered front contact, not braking prediction. Static lateral sweep at frozen longitudinal position: identical synthetic rectangles 5000×1800 mm with 300 mm buffer, conservative inclusive contact; track edge checks footprint plus buffer. Existing overlap is reported blocked, no teleport or collision resolution. Five layouts including wrap, dense, inactive/lapped and coincident; compare against exhaustive reference and permutation. Counts are cases, not CPU timing. No continuous swept motion yet. REF-105/IDEA-024/033/034/040 concept only.

## 0.8.2

`racecraft_trajectory`: original finite station DP (2–7 stations, up to four candidate offsets each). Artificial cost in mm²: offset preference plus squared first difference plus twice squared second difference; hard bound on offset change per station. Exact exhaustive oracle, lexicographic ties, explicit infeasible outcome, 29 fixtures. Station candidates already represent admissible sampled offsets; no between-station collision/curvature validation, real road surface or minimum-lap-time claim. REF-109/IDEA-021/023/024/034 concept only, no copied source.

## 0.8.3

`racecraft_overtaking`: observe front same-corridor car, require unwrapped classified gap equal to physical gap, >5300 mm, closing >=2000 mm/s and estimated draw-clear <=6000 ms. Try fixed offsets ±3000 mm, static sweep and constant-speed destination traffic veto. Candidate is not a command or safety guarantee. Separate observed_crossing on 2–32 consecutive snapshots, active pair, same geometry, monotonic bounded progress, lateral separation at sampled sign crossing and clear final classified lead. No actual sporting award or continuous collision claim; synthetic max 100000 mm per tick is only a jump guard. 48 decisions + four crossing cases. REF-105/IDEA-024/025/026/033/040 concept only.

## 0.8.4

`racecraft_defensive`: owner-bound consecutive tick memory, one own-side commitment while nearby target or threat persists. Safety veto holds observed own position (not switch side); five consecutive clear ticks release memory, no forced return. Synthetic 40-tick sequence with alternating rival observed line, temporary blockage and renewed threat. Does not claim FIA compliance, motion, collision freedom or 2012 calibration. REF-105/IDEA-028/029/033/034 conceptual.

## 0.8.5

`racecraft_collision`: exact Fraction time intervals intersect longitudinal and lateral expanded footprints over t∈[0,1], enumerate relevant periodic images. Inclusive touch and initial overlap distinguished, first contact rational. Compare to independent boundary-event enumeration (72 cases), symmetry and interior contacts. Inputs are bounded linear endpoint proposals, not predicted trajectories; no yaw, acceleration, real collision physics or actual gameplay clearance. No response/teleport. REF-105/IDEA-033/034/040 conceptual.
