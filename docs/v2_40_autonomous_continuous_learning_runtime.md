# v2.40 Autonomous Continuous Learning Runtime

v2.40 turns the existing research, RL, shadow-lifecycle, evidence and validation layers into a persistent learning loop.

## Principle

"Continuous" is event-driven, not repeated gradient descent on unchanged data. A cycle can run every 15 minutes, while retraining occurs only when new information exists: new closed bars, enough new shadow outcomes, material drift, an aged model, or an explicit forced research run.

## Loop

closed market data -> strategy discovery/revalidation -> shadow lifecycle reconciliation -> evidence production -> research reassessment -> PPO/SAC/MAPPO challenger training -> purged validation/test -> research evidence -> next cycle.

PPO continues from the latest policy checkpoint when permitted. SAC additionally persists and reloads its replay buffer. MAPPO uses a shared actor with a centralized critic on an explicit NPZ training contract.

## What self-learning means

Agents update model parameters from new data and realized shadow outcomes. They do not rewrite repository source code, bypass risk constraints, grant themselves authority, or auto-promote to live trading.

## Safety

- execution authority: NONE
- broker submission: disabled
- automatic live promotion: disabled
- automatic champion promotion: disabled
- RL output remains research/shadow challenger evidence
- strategy and evidence subprocesses are allowlisted
- one process lock prevents duplicate supervisors
- launchd support is opt-in and runs the same safe foreground watch command

## Practical commands

    ./.venv/bin/python scripts/run_autonomous_learning_v2_40.py doctor
    ./.venv/bin/python scripts/run_autonomous_learning_v2_40.py init
    ./.venv/bin/python scripts/run_autonomous_learning_v2_40.py cycle
    ./.venv/bin/python scripts/run_autonomous_learning_v2_40.py status
    ./.venv/bin/python scripts/run_autonomous_learning_v2_40.py watch --interval-seconds 900

For persistence on macOS:

    ./.venv/bin/python scripts/run_autonomous_learning_v2_40.py install-launchd --interval-seconds 900

The launchd service can be inspected or removed with `launchd-status` and `uninstall-launchd`.
