# Architecture and operating model

## Boundary

ShadowGauge is a local-first reference implementation. It does not intercept or answer production requests. A host application hands it a copy after returning its response; selected copies enter SQLite and a separate worker grades them.

## Data contract

Required event fields are `event_id`, ISO-8601 `ts`, `intent`, `question`, `context`, and `response`. Synthetic replays may add `synthetic_failure`; production integrations must not pretend to have this ground-truth label. Every sampled row also stores `inclusion_probability` and `sample_reason`.

## Decisions

| Decision | Reason | Tradeoff |
|---|---|---|
| SHA-256 Bernoulli sampling | Replays are deterministic and auditable | A caller must provide stable, non-secret IDs |
| Oversample new intents | Shortens time to first signal | Raw sample averages become biased |
| Hájek estimator | Easier-to-read bounded rate than an unnormalized total | Depends on correct inclusion probabilities |
| Cap inverse weights at 20 | Prevents rare records dominating | Introduces bias; report ESS and clip count |
| SQLite queue | Zero-service setup and durable local demo | Single-node throughput ceiling |
| Fixed-bin PSI | Detects distribution changes, not just mean changes | Needs calibrated bins and adequate counts |
| Two-window gate | Reduces one-window false alarms | Adds one window of detection latency |

## Failure modes

- If the worker stops, pending rows remain durable; queue depth should be alerted on.
- If event IDs repeat, `INSERT OR IGNORE` prevents duplicate grading.
- If probabilities are omitted or wrong, weighted estimates are invalid. The API rejects probabilities outside `(0, 1]`.
- If a daily cap is reached, decisions carry `daily_cap` as the reason but are not queued. The host should count rejected decisions for coverage reporting.
- If a grader changes, current scores are not directly comparable. The P2 bridge in the backlog addresses this explicitly.

## Production hardening path

Add privacy transforms before persistence, use a shared queue and budget counter, version all policies and graders, enforce minimum segment counts, and connect incident records to an authenticated delivery adapter. Validate every threshold on a frozen replay plus human-reviewed labels before enabling paging.
