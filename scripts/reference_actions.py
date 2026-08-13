from __future__ import annotations

import json
from pathlib import Path

from stocks.capabilities import (
    CapabilityRegistry,
)
from stocks.research.reference_actions import (
    ReferenceActionRegistry,
)


ROOT = Path(
    __file__
).resolve().parents[1]


def main() -> int:
    capabilities = (
        CapabilityRegistry.load(
            ROOT
            / "config"
            / "capabilities.yaml",
            project_root=ROOT,
        )
    )

    actions = (
        ReferenceActionRegistry.load(
            ROOT
            / "config"
            / "reference_actions.yaml",
            capabilities=capabilities,
        )
    )

    print(
        json.dumps(
            actions.summary(),
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
