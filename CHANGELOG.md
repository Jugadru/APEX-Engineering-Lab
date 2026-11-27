# Changelog

## 0.9.5 — Undercut & Overcut Intelligence

- Original four-lap dry one-stop duel, same 0.9.4 tyre cost, 12 plans, four equally weighted rival forecasts, exogenous traffic at equal-distance lap boundaries. Select lexicographically by expected loss count then gap and own elapsed time; compare solo minimum elapsed plan. Fixed 24-state grid and 96 sampled scenarios; six frozen zero-violation criteria, eight tests. Return rank is a crossing-order proxy, not physical track position. No reactive rivals, actual traffic/overtaking, or promotion.

## 0.9.4 — Tyre Degradation Intelligence

- Separate synthetic lap-age cost model with soft/medium/hard/wet profiles and quadratic post-cliff penalty. Original costs and experiments unchanged; not coupled to physics_tyre. Posterior-aware one-to-three-stop reference, 256 weighted eight-lap paths, 72 sampled twelve-lap paths, independent segment-DP hindsight oracle checked against short brute enumeration. Eight frozen zero-violation criteria, nine tests. No historical tyre calibration, thermal integration, inventory or sporting promotion.

## 0.9.3 — Multi-Stint Strategy Intelligence

- Extend posterior-aware Bellman decisions to one through three stops, with explicit stop budget and deterministic tie-breaking favoring no stop. Verify one-stop value against v0.9.2, exhaustive weighted 256-path replay and independent complete-plan hindsight cost, plus 72 held-out scenarios including out-of-prior regime. Eight frozen zero-violation criteria and eleven tests. Initial fixture passed but chose exactly one stop in all 72 sampled cases; expected costs tied. Add targeted coverage for required two/three stops and optional additional service in a conditional worn-tyre state, not a new performance sample. Preserve existing synthetic tyre costs and earlier experiments; no inventory, sporting compound rules, traffic, or game promotion.

## 0.9.2 — Weather Prediction Intelligence

- Original exact Bayesian posterior and adaptive Bellman decisions over two unknown fixed synthetic flip rates with equal prior probability. Compare fixed mean forecast, heuristic and regime-known lower bound. Frozen eight-lap 256-path mixture evaluation, Brier score and 96 independent sampled cases across two in-prior regimes and one out-of-prior regime. Nine zero-violation criteria and eight tests. No real weather calibration or game promotion. Preserve previous experiments unchanged.

## 0.9.1 — Adaptive Strategy Reference

- Add original finite-horizon integer Bellman reference under the existing synthetic binary Markov weather and one mandatory stop model. Preserve 0.9.0 comparison and results. Compare expected costs by exhaustive weighted path replay for four fixed transition regimes (256 paths each), then separate 64-case held-out sample. Frozen acceptance: zero weight/Bellman mismatches, expected dominance violations, illegal actions, prefix causality violations, negative hindsight regret and replay mismatches. Eight targeted tests. No claim of real race optimality or production promotion.

## 0.9.0 — Strategy Research Lab

- Owner-authorized bounded engineering scope transition from audited 0.8.18; twenty exact workflow approvals in active closure; original 0.8.9 closure retained in git history. Full scientific and production validation remain out of scope, not resolved.
- Reuse experimental registry for paired synthetic one-stop decisions under binary weather. Compare a simple causal heuristic against bounded Monte Carlo with common forecast paths, independent held-out weather and hindsight-only evaluation. Initial candidate 461 tests per Python, ten workflows passed after runner provisioning failures and one transient metadata query failure. Audit hardens fractional/boolean stop rejection, initial-state and stint validation, exact episode cost reconciliation and exhaustive short-prefix causality; adds bounded metadata retries without relaxing gate identity or authentication checks. Original 32-case regret results retained as exploratory (heuristic 5725 ms, Monte Carlo 8850 ms); no VSE, real tyre/traffic model or game promotion.

## 0.8.18 — Adaptive Control Refinement

- Refine a feasible oriented trajectory towards the requested continuous steering/throttle/brake/KERS controls, with bounded deterministic line search and joint swept revalidation. Never worsen the declared command deviation objective or commit infeasible state. Five tests and six wet/dry edge scenarios. Audit revision: fix repeated shift cut over 10 ms substeps (four regressions); extend platform evidence to oriented/refined trajectories with explicit numerical tolerances, preserving exact legacy comparison (two tests); strengthen reopened stage workflow coverage (three tests). Include separately developed historical pace holdout and pinned native scenario evidence (PRs 56 and 53), verified together against current base to avoid stale-branch CI. Native replay uses a previous pinned Hyper record and a fresh Core 2 run. No global optimum, real-track or game promotion claim.

## 0.8.17 — Oriented Motion Solver

- Compose 10 ms yaw steps, continuous interpolated oriented rectangular envelopes, separating-axis motion bounds, strip containment, lazy bounded multi-car search and atomic failure. Synthetic straight Cartesian strip; not real-world collision response, calibrated geometry, continuous optimality or full sporting integration. Nine tests and two 24-car eight-tick replay episodes.

## 0.8.16 — Steering and Yaw Dynamics

- Add small-angle dynamic bicycle reference with bounded steering rate, body lateral velocity, axle yaw moment and world heading/position. Reuse the existing combined tyre force/energy path via optional axle demands; legacy commands unchanged. Eight proposed mirrored wet/dry/braking episodes (ten outer ticks each, twenty substeps per tick), seven tests. Synthetic constants; not full planar energy, historical calibration, rotated multi-car collision or runtime integration. Model reference: https://optimal-control-ad-personal-repos-bb7de67c51e7f51ec3bda98b62f32.pages.gitlab.lrz.de/explanations/vehicle_dynamics/db/ .

## 0.8.15 REV3 — Platform replay evidence (candidate)

- Portable exact replay CLI and hosted Linux/Windows/macOS comparison on Python 3.13, with explicit failure on mismatches. Compare episode digests and refined edge recovery; retain raw artifacts. This does not certify all motor behavior, local native performance, or independent review.

## 0.8.15 REV2 — Control search refinement

- Retain the primary search and add a deterministic second tier of bounded intermediate braking and lateral-control requests only when the primary options are exhausted. Share the same search node budget; preserve environmental inputs and atomic rejection. Five tests include an edge recovery not available in the original control set. Finite search, not continuous feasibility or optimality.

## 0.8.15 REV1 — Swept contact refinement

- Preserve the conservative broad phase, refine ambiguous pairs with rational piecewise-quadratic ranges, split at stopping times, reject unresolved intervals at fixed depth. Six targeted tests including a reproducible false veto from equal lateral acceleration. Still axis-aligned synthetic geometry; no exact oriented-body collision or contact response claim.

## 0.8.15 — Unified Motion Solver (candidate)

- Joint bounded search over existing coupled vehicle steps with persistent SI lateral velocity, shared grip and energy limits, conservative swept periodic envelopes, deterministic ordering and atomic infeasible/budget outcomes. Three proposed 100-tick synthetic episodes and ten targeted tests; no physical calibration, full race or runtime promotion. Validation status must be read from exact-head CI.

## 0.8.14 — Coupled Local Motion

- Reuse existing 0.7 vehicle force/energy and saturated combined-grip result for stateful local lateral kinematics; check interior path extrema, reject invalid edge/low-speed/domain continuation. 24 force cases, two eight-tick sequences, two edge cases, eight tests. Separate lateral work identity, not full 2D energy, yaw/steering or sporting integration.


## 0.8.13 — Historical Reference Crosscheck

- Compare all 20 pinned game lap lengths, official 2012 fastest race laps and declared +500 ms game buffers; preserve early Austin discrepancy and later source. Document three missing outline references from pinned F1DB CC-BY-4.0 repository; no SVG copy or measured geometry claim. Five new tests. Historical reference verification is not calibration.


## 0.8.12 — Historical Rule Evidence

- Selected 2012 FIA driving clauses 20.2–20.5 reviewed from original 9 March 2012 document; explicit declared-event signals and unknowns, no automatic penalties. 16 fixtures / 64 clause checks, seven tests. Not full regulation or steward equivalence.


## 0.8.11 — Track Evidence

- Read-only audit of pinned actual Core 2 season/track physics/tyre data and geometry license notice, exact blob checks, 20 normalized centerline records; distinguish licensed reference from schematic placeholders and historical calibration blocked. Five new tests and exact-head hosted source audit. No geometry copied or sporting changes.


## 0.8.10 — Bounded Motion Research

- Reopen Racecraft for closed-loop constant-acceleration reference, bounded discrete alternatives with exact conservative chord envelope, explicit infeasible/budget states rather than teleport or instant stop. Three 16-tick episodes, independent SI reference and sampled quadratic trajectory, seven tests. No real calibration or runtime promotion.


## 0.8.9 — Racecraft Stability & Validation

- 60 scripted observation ticks, repeated in reversed roster order and with diagnostic memory checkpoint; 4320 decisions including replays. Eight new tests, including four reproduced boundary failures and additional exact horizon/constructor checks. Correct all-active periodic ETA veto and frozen constructor validation; preserve QA 46051839453. No sporting motion or game save/replay claim.


## 0.8.8 — Racecraft Integration

- Compose frozen observation, behavioral acceptance, defensive precedence, fixed attack latch/cooldown and batch geometry feasibility. 12 scripted ticks, 288 decisions, seven tests. Diagnostic proposals only; never apply stationary fallback or constant-speed endpoints to game state.


## 0.8.7 — Driver Personality

- Bounded artificial patient/balanced/assertive traits and wet/wear/pressure preference budget, hard feasibility never overridden. 162 decisions, six tests. No real driver psychology or calibration.


## 0.8.6 — Multi-Agent Racing

- Complete frozen proposal batch, symmetric bounded veto and iterative chain recheck, retain initial invalid geometry without teleport. 21 scenarios including 16 seeded 24-car rosters, seven tests. Stationary fallback is geometric reference, not physically executable braking.


## 0.8.5 — Collision Avoidance

- Exact rational swept contact for linearly moving rectangular centers with periodic longitudinal images; boundary-event oracle, 72 cases, eight tests. Detect between-endpoint conflicts, no physical response or real geometry claim.


## 0.8.4 — Defensive Intelligence

- Fixed own-side defensive commitment, frozen safety veto, five-clear-tick hysteresis and no reactive opponent-line chase. 40-tick fixture, seven tests. No actual steering or sporting regulation adjudication.


## 0.8.3 — Overtaking Intelligence

- Frozen observed attack opportunity, classified-rival check, lateral clearance and destination closing veto, no future intent. Observed classified crossing on consecutive samples with separation and bounded progress; no sporting award. 48 decision and four crossing cases, eight tests.


## 0.8.2 — Trajectory Optimization

- Bounded offline discrete path DP with preference, first/second difference costs and stable lexicographic ties; exhaustive comparison across 29 scenarios. Seven tests. Explicit infeasibility, no continuous path or lap-time claim.


## 0.8.1 — Spatial Awareness

- Reuse periodic Ring index with frozen active cars; signed front/rear/coincident observations, constant-speed TTC estimate and static lateral sweep/edge clearance. Five layouts, 456 queries, 570 clearance checks, nine new tests. No moving collision solver or production equivalence.


## 0.8.0 — Racecraft Foundation

- Original immutable active-car observations in integer SI subunits; classified progress separate from circular physical gap, stable tie order, no future intent. Four 24-car layouts and 128 permutations. Ten foundation tests plus two closure tests. Dedicated exact-SHA hosted racecraft suite required from 0.8 closure onward; prior physics closure preserved. No game or Hyper edits.


## 0.7.10 — Stage Closure Gate

- Permanent stage exit checklist, live same-repository workflow metadata validation (exact SHA, workflow, attempt, main push, identical merge tree), retained adverse runs and open-finding block. Transition gate checks ancestry and rejects stale reviewed code; 19 new tests. Cumulative light regression workflows run on PR and main. No branch-protection changes or game promotion.


## 0.7.9 — Physics Boundary Audit

- Five reproduced boundary failures on unchanged 0.7.8 (QA 46045062037): exact stop residue, stationary interval, out-of-domain thermal/spring output, unrepresentable stopping distance. Reject invalid continuation without clipping; enforce exact candidate checkout in QA. Seven new tests including 240 seeded vehicle cases. Original physics criteria unchanged. No game or calibration change.


## 0.7.8 — Numerical Stability & Validation

- Analytical nonlinear coast oracle, four timestep resolutions, 12 coast comparisons and three fixed 120-tick sequences repeated. Cumulative work, kinetic energy carried by consumed fuel, mass/store/lap balance and deterministic repeat checks. Ten new tests; preserve original experiment regression on physics changes. No actual sporting or calibration claim.


## 0.7.7 — Integrated Vehicle Dynamics

- Compose independent aero, powertrain, load, tyre and energy references into a bounded forward step, brake precedence and feasible energy work limit. 180 cases, twelve tests including low-speed regularization and tiny-dt rejection. No sporting integration or dynamic steering.


## 0.7.6 — Fuel & Energy Management

- SI fuel chemical/shaft/wheel energy and bounded KERS source offers; debit accepted work once, record conversion losses and unmet demand. 162 cases, nine tests. No real fuel/KERS calibration or idle/recharge model.


## 0.7.5 — Suspension & Weight Transfer

- Quasi-static four-corner load redistribution with explicit saturation, independent analytical underdamped spring reference. 36 load and 12 spring cases, eight tests; no calibrated suspension.


## 0.7.4 — Braking Dynamics

- Constant friction-limited braking, analytical stop distance, front/rear heat allocation and adiabatic heat rise reference. 54 cases, seven tests; no wheel-lock or brake cooling calibration.


## 0.7.3 — Engine & Powertrain

- Artificial V8-shaped torque curve, rigid seven-ratio gearing, RPM, crank/wheel power and prescribed shift cut. 210 cases, eight new tests, no launch controller or calibrated engine.


## 0.7.2 — Aerodynamic Research

- SI still-air drag/downforce, independent prescribed losses, drag power, 48 cases and six new tests. No CFD or aerodynamic calibration.


## 0.7.1 — Tyre Physics Laboratory

- Combined friction ellipse with zero-axis handling, exact lumped thermal step (Kelvin), bounded energy-proxy wear and thermal/wear grip modifier. 45 force, 18 heat and 9 wear cases; ten new tests. Not calibrated tyres.


## 0.7.0 — Vehicle Physics Foundation

- Bounded SI constant-force step, exact stop, work-energy residual and 54 combinations; seven tests. Same-SHA physics suite, environment metadata, original models only.


## 0.6.5 — Scientific Experiment Reports

- Verified individual and same-revision suite reports with frozen config and observation binding, explicit incomplete/fail states, JSON and Markdown output. Ten tests, complete five-experiment hosted suite. No runtime/game claims.


## 0.6.4 — Experimental Optimization

- Exact integer-millisecond direct versus prefix pit cost comparison; 32 training and 64 independent heldout scenarios plus nominal case, six possible entries. Explore regret of nominal versus sampled policy, no improvement assumed. Eight new tests; no runtime timing or game change.


## 0.6.3 — Parameter Sensitivity

- 40-case full-factorial artificial mass, grip and force grid; engine/traction regimes, bounds and monotonic effects, six tests. No calibrated tyre model.


## 0.6.2 — Mathematical Models

- Constant-force SI analytical reference versus trapezoid and Euler integration; 27 synthetic cases and six tests. No physical calibration.


## 0.6.1 — Algorithm Comparison

- Periodic sorted spatial index vs exhaustive scan; 24 cars, six layouts, four radii, 576 queries. Count other rows, not elapsed time. Eight new tests.


## 0.6.0 — Experimental Engineering Core

- Fixed bounded built-in experiment execution with actual checkout SHA, frozen registry plan/config, immutable evidence, exact-candidate CI. 24-agent stable-order synthetic fixture, seven new tests. No game changes.


## 0.5.4 — Engineering Memory

- Immutable snapshots of investigation stages, search by tags and normalized text, preserve adverse/unrun results, detect newer evidence without erasing history. Documentary example of actual Development Lab failure and correction. Ten new tests and end-to-end synthetic memory smoke.


## 0.5.3 — Solution Intelligence

- Up to two predeclared hypotheses and candidate plan hashes; require matching baseline failure and identical workload, criteria, Lab and scope kind. Review dossier with evidence, files and rollback, no auto patch/merge. Actual synthetic correction; nine new tests.


## 0.5.2 — Automatic Reproduction

- Bind predeclared reproduction criteria to existing registry plan/results, fixed SHA, seed, command digest and <=15 minute budget; distinguish matching failure, different failure, not reproduced and unrun. Actual bounded synthetic demo; nine new tests. No arbitrary executor.


## 0.5.1 — Bug Intelligence

- Reuse existing correlation output bound to case evidence and exact SHA; local classification, stable recurrence fingerprint and history. Eight new tests. Similarity is not causation.


## 0.5.0 — Autonomous Debugging

- Immutable investigation intake, exact target SHA, local evidence validation, explicit budgets and conservative status. Eight new tests. No executor, cause inference or game edits.


## 0.4.1 — Evidence Integration

- Durable actual static/analyzer aggregate evidence at exact game SHA; imports existing analyzer summary, headless profile and correlation outputs with explicit limitations.
- Opt-in authenticated read-only metadata with existing managed credential, fixed repo/endpoint allowlist; no new token or cross-repo access provisioned.
- Hosted same-repo metadata smoke and public discovery attempt, 12 new tests. No runtime claim.


## 0.4.0 — Code Intelligence

- Reuse existing pinned game graph producer; supplemental lexical duplicate-body and single-mention candidates.
- Import private analyzer 0.2.1 matching revision, rank coupling/complexity/hot-operation hypotheses, reverse-impact and comparable graph diff.
- Hosted pinned-game static integration and 15 new contract tests. No runtime performance or sporting claims, no private analyzer dispatch.


## 0.3.0 — Research Intelligence

- Pin da Foundation separada, 198 REF e 120 IDEA sem duplicar catálogo.
- Quatro fontes com commits e LICENSE revisados, cinco propostas e critérios prévios.
- CLI pesquisa catálogo, descoberta GitHub/Crossref opt-in, ranking ordinal e plano v1.
- 20 testes novos offline; sem execução externa, autorização de cópia ou mudança no jogo.


## 0.2.0 — Scientific Evidence Registry

- Registro lateral de origem vinculado ao resultado, preservando formato v1.
- Adapter público GitHub opt-in, com validação de SHA, run, tentativa, repositório e digest de ZIPs.
- Snapshot local não autenticado, maturidade conservadora e prontidão para revisão sem promoção.
- 20 novos testes offline; nenhuma execução pesada, assinatura ou integração automática.
- A CI valida o SHA candidato; consulta ao vivo e adapters especializados não estão homologados por fixtures.


## 0.1.0 — Foundation (candidate)

- 12 áreas de pesquisa documentadas; limites de autonomia e relação com o ecossistema.
- Quatro contratos de interoperabilidade v1; registro local original com plano imutável, resultado, critério e verificação de bytes.
- Demo aritmético sintético, testes e CI hospedada.
- Nenhum código privado copiado, nenhum jogo alterado, nenhum benchmark pesado, nenhum runner pessoal.
- Aprovação depende da execução no SHA candidato; consulte Actions e PR. Não declarar release homologada por este arquivo.
