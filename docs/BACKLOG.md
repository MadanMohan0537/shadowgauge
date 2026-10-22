# Rigorous feature backlog

This backlog compares proposed work with the MVP so plans are not confused with shipped behavior. The sampling-bias inspector and grader-version bridge are implemented. Other items remain planned.

| Priority | Feature | Concrete user problem | Intended behavior | Dependencies | Success test | Risks and tradeoffs |
|---|---|---|---|---|---|---|
| P1 shipped | Sampling-bias inspector | Adaptive sampling makes a raw average look like population quality | Store inclusion probabilities; show raw and capped inverse-probability estimates with ESS | Sampling policy + event store | On skewed synthetic traffic, weighted estimate recovers the known mix more closely than raw | Tiny probabilities inflate variance; clipping lowers variance but adds bias |
| P2 shipped | Grader-version bridge | A grader upgrade can look like an app regression | Double-grade a frozen overlap batch; isolate grader-only shifts; preserve segment breakdowns and quarantine incompatible versions | Versioned grader names + frozen overlap artifact | Seeded grader-only PSI shift creates measurement hold, not product incident; compatible control still detects app regression | Double grading costs more; overlap may miss rare intents; hold pauses product alerting |
| P2 | Privacy budget and field redaction | Shadow copies may retain secrets or personal data | Allowlist fields, redact patterns, enforce TTL, and count retained bytes by class | Schema registry, deletion job | Seeded secrets never reach SQLite and expired rows disappear | Regex redaction misses context; over-redaction harms grading |
| P2 | Sequential false-alarm control | Repeated window checks inflate false positives | Calibrate alert thresholds across repeated tests and surface the error budget | Historical clean replay | Clean 30-day replay stays under target false-alert rate while injected regressions remain detectable | More conservative thresholds delay detection |
| P3 | Coverage allocator | Fixed new-intent oversampling can exhaust the budget early | Allocate the daily budget by novelty, volume, uncertainty, and minimum segment floors | Intent clustering, shared atomic counter | Rare critical segments meet coverage floors without exceeding cap | Gaming or unstable clusters can divert budget |
| P3 | Delayed-label audit | Proxy graders can drift away from real customer outcomes | Join later refunds, escalations, or human reviews to grader predictions | Consent-safe label pipeline | Monthly precision/recall report catches seeded grader decay | Labels are delayed, selective, and potentially sensitive |
| P3 | Incident explainer | A PSI number does not tell an operator what changed | Rank changed intents, grader dimensions, and representative redacted examples | Segment aggregates, privacy layer | On an injected intent regression, correct segment ranks first | Examples may leak data or imply false causality |
| P3 | Queue health SLO | A quiet monitor can silently stop grading | Track queue age, processing lag, throughput, and dead letters separately from model quality | Worker heartbeats | Killed-worker drill alerts before quality data becomes stale | More operational alerts can create noise |
| P4 | Signed policy snapshots | Teams cannot reproduce why an old request was selected or alerted | Persist immutable sampler, grader, and threshold versions with each decision | Config serialization, release process | Historical replay reproduces the original decision byte-for-byte | Storage and migration complexity |

## Next slice

Build privacy redaction and retention next. The bridge protects attribution, but the
current queue still stores raw prompts, contexts and responses indefinitely.

## Further rigorous additions — planned

| Priority | Feature | Problem and behavior | Dependencies | Success test | Risks/tradeoffs |
|---|---|---|---|---|---|
| P1 | Bridge promotion ledger | A compatible report does not prove which grader was activated | Persist proposed, quarantined, approved and active transitions with immutable thresholds | Historical incident identifies exactly one active grader policy | Workflow state adds operator burden |
| P2 | Bridge uncertainty bands | Point thresholds are brittle on small overlaps | Bootstrap paired mean/flip shifts per intent and suppress conclusions with low support | Clean repeated fixtures meet predeclared false-quarantine budget | Wide bands can block upgrades |
| P2 | Sentinel intent set | Traffic overlap may omit rare critical intents | Require curated safety/billing sentinels alongside traffic-derived overlap | Removing a sentinel segment always creates coverage debt | Sentinels can become stale |
| P3 | Dual-stream incident replay | Quarantine pauses current alerts | Reprocess quarantined windows under both graders after approval | Replayed decisions preserve original evidence and show attribution | Storage and operational complexity |

