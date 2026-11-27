# Autonomous Debugging 0.5 series

The Engineering Lab owns investigation workflow, not a duplicate failure classifier, test runner, or agent capable of modifying the game. Existing APEX-Simulation diagnosis/correlation and FAST/Test Lab, Development Lab analyzer and Lab Hub orchestration remain authoritative. Reviewed game main 50e0b475399b0e94a8229996df2ee8043d89f9b6: tools/apex_lab_diagnosis.py (blob eb55d8865478a54ddfbe8f85a31f0515abc2e6f7) and tools/apex_lab_correlation.py (blob 6608c13b8ad01bebf4b3029d7ecf098dd96b1cd3). Hub 1.1.0 has persistent sessions; do not replicate its execution engine.

## 0.5.0
Create a private local registry folder outside checkouts. `python -m engineering_lab debug-open examples/debug-case.json --registry PATH` and `python -m engineering_lab debug-inspect --id BUG-DEMO-001 --registry PATH`. Exact target SHA, classification of observation, expected/observed symptom, bounded local evidence files and digest, immutable publication through registry.publish_once. Trusted local filesystem; not authenticated or tamper-proof. Observed failures require evidence; static or user reports are not confirmed failures. No inferred cause, test result or promotion.

Limits: two materialized hypotheses, one targeted attempt per candidate, 15 min lightweight workload, 1 MiB local file. Policy; no arbitrary execution. No permanent agent, new secrets, FULL, personal runner or game changes. Subsequent increments 0.5.1 classification/history, 0.5.2 reproduction, 0.5.3 solution proposal, 0.5.4 engineering memory. Each validated separately.

## 0.5.1

Register original correlation.json as case evidence, then `debug-classify --registry PATH --id BUG-ID --source correlation.json --case fixture.gd`. The existing game producer supplies classification, not this tool. `debug-history --registry PATH --fingerprint HASH` searches up to 1000 records and revalidates their evidence. Same fingerprint across commits is a recurrence lead, not the same root cause. Static signals and unverified user reports cannot be classified as observed CI failures. No raw log parser duplicated.
