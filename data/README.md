# Reproducible data

No customer data is committed. `shadowgauge.simulation.generate_events` deterministically creates all demo traffic in memory: four fictional support intents, documented answers, sparse natural failures, and a shipping/returns regression after 65% of the stream.

To materialize a run, use:

```bash
shadowgauge simulate --count 800 --db demo.db --output report.json
```

Both outputs are ignored because they are reproducible. The integration test executes the same path in a temporary directory.
