# v2.40.1 SB3 persistence hotfix

Fixes atomic model checkpoint and SAC replay-buffer persistence when Stable-Baselines3 applies suffix-aware save-path normalization. Also upgrades the legacy fake-model regression test to mirror actual SB3 suffix semantics. No authority, broker, promotion, or risk settings are changed.
