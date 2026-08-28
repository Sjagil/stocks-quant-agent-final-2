# v2.42 Production Intelligence & Validation

v2.42 closes the gap between infrastructure readiness and actual decision-system readiness.

- IBKR 30-minute RTH bars are aggregated onto the EODHD 09:30/10:30/... session grid before cross-provider validation or canonical overlay.
- Forward-strategy finalist symbols are hydrated into the high-priority provider fabric before the forward signal engine runs.
- EODHD economic events are consumed causally as risk windows; high-impact US events can block new entries around release time.
- EODHD news is fetched with publication timestamps, deduplicated, and rescored by ProsusAI/FinBERT. Production blocks new entries if configured NLP is unavailable rather than silently treating all news as neutral.
- News/macro context can only gate or modestly scale an existing portfolio proposal. It cannot originate an order.
- PPO/SAC produce persistent shadow advisories. Zero-action PPO is labeled degenerate; SAC remains challenger-only until sufficient evidence.
- A synchronized multi-asset MAPPO dataset is generated automatically. MAPPO remains research-only.
- Learning runtime locks recover only when the recorded PID is dead, preventing a stale lock from creating a launchd restart loop.
- PAPER submission is disabled during upgrade. No automatic live promotion or RL direct broker control is introduced.
