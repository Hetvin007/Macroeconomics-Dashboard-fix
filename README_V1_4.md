# Macro Intelligence Terminal v1.4

## Cross-Asset Macro Attribution

v1.4 adds a descriptive cross-asset attribution layer on top of the v1.3 market-reaction engine.

### What it does
- Classifies validated economic surprises into transparent macro impulse buckets.
- Compares observed event-window moves in rates, USD and equities.
- Labels the response as tightening-style, easing-style, growth/risk-positive, growth/risk-negative, or mixed.
- Reports a response-consistency flag.

### Important limitation
This is **descriptive**, not causal. A post-release market move is not automatically attributed to the release because multiple events can occur in the same window.

### Data policy
- Consensus values must be supplied from a validated source.
- Market observations must come from configured official/open sources.
- Missing observations remain missing; the engine does not synthesize market moves.
