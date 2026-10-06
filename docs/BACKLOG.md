# Rigorous feature backlog

This backlog compares proposed work with the MVP so plans are not confused with shipped behavior. P1, the sampling-bias inspector, is implemented. Items below remain planned.

| Priority | Feature | Concrete user problem | Intended behavior | Dependencies | Success test | Risks and tradeoffs |
|---|---|---|---|---|---|---|
| P1 shipped | Sampling-bias inspector | Adaptive sampling makes a raw average look like population quality | Store inclusion probabilities; show raw and capped inverse-probability estimates with ESS | Sampling policy + event store | On skewed synthetic traffic, weighted estimate recovers the known mix more closely than raw | Tiny probabilities inflate variance; clipping lowers variance but adds bias |
| P2 | Grader-version bridge | A grader upgrade can look like an app regression | Double-grade a frozen overlap batch; isolate grader-only shifts; preserve segment breakdowns | Versioned grader registry, overlap store | A grader-only score change does not open a product incident | Double grading costs more and overlap may miss rare intents |
| P2 | Privacy budget and field redaction | Shadow copies may retain secrets or personal data | Allowlist fields, redact patterns, enforce TTL, and count retained bytes by class | Schema registry, deletion job | Seeded secrets never reach SQLite and expired rows disappear | Regex redaction misses context; over-redaction harms grading |
| P2 | Sequential false-alarm control | Repeated window checks inflate false positives | Calibrate alert thresholds across repeated tests and surface the error budget | Historical clean replay | Clean 30-day replay stays under target false-alert rate while injected regressions remain detectable | More conservative thresholds delay detection |
| P3 | Coverage allocator | Fixed new-intent oversampling can exhaust the budget early | Allocate the daily budget by novelty, volume, uncertainty, and minimum segment floors | Intent clustering, shared atomic counter | Rare critical segments meet coverage floors without exceeding cap | Gaming or unstable clusters can divert budget |
| P3 | Delayed-label audit | Proxy graders can drift away from real customer outcomes | Join later refunds, escalations, or human reviews to grader predictions | Consent-safe label pipeline | Monthly precision/recall report catches seeded grader decay | Labels are delayed, selective, and potentially sensitive |
| P3 | Incident explainer | A PSI number does not tell an operator what changed | Rank changed intents, grader dimensions, and representative redacted examples | Segment aggregates, privacy layer | On an injected intent regression, correct segment ranks first | Examples may leak data or imply false causality |
| P3 | Queue health SLO | A quiet monitor can silently stop grading | Track queue age, processing lag, throughput, and dead letters separately from model quality | Worker heartbeats | Killed-worker drill alerts before quality data becomes stale | More operational alerts can create noise |
| P4 | Signed policy snapshots | Teams cannot reproduce why an old request was selected or alerted | Persist immutable sampler, grader, and threshold versions with each decision | Config serialization, release process | Historical replay reproduces the original decision byte-for-byte | Storage and migration complexity |

## Next slice

Build the grader-version bridge first. It protects the central promise—alert on product drift, not measurement drift—and can be proven with a frozen dual-graded fixture before any external service is introduced.
