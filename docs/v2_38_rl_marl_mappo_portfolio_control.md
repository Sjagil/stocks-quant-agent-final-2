# v2.38 RL / MARL / MAPPO Portfolio Control

v2.38 is a research/shadow challenger layer. It does not generate alpha, bypass v2.33 strategy acceptance, bypass v2.34/v2.35 portfolio constraints, submit broker orders, or promote itself live.

Core design:
- PPO primary single-controller challenger; SAC continuous-control challenger; MAPPO multi-agent challenger.
- Hard action projection outside the learned policy: long-only, no leverage, accepted strategies only, strategy/family/cluster caps, turnover, portfolio heat and cash floor.
- Reward uses net log wealth and explicit penalties for turnover, action jerk, drawdown deterioration, Expected Shortfall/tail risk and HHI concentration, with only a small alpha-alignment bonus.
- Purged chronological datasets; no random shuffle across time.
- v2.37 shadow outcomes are the preferred training/calibration source.
- RL actions become shadow targets only when lifecycle reconciliation is READY.
- Challenger promotion is OOS-after-costs against a deterministic baseline and remains forward-shadow only.
