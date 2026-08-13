from pathlib import Path

from stocks.capabilities import CapabilityMode, CapabilityRegistry
from stocks.integrations import IntegrationRegistry
from stocks.research import ResearchPipeline


ROOT = Path(__file__).resolve().parents[1]

EXPECTED = {
    "vectorbt",
    "optuna",
    "pybroker",
    "skfolio",
    "sb3_contrib",
    "qlib",
    "vnpy",
    "finrl",
    "moondev",
    "nautilus",
    "lean",
    "stocks_reference",
    "vnpy_ib",
}


def test_all_reference_engines_are_registered() -> None:
    registry = CapabilityRegistry.load(
        ROOT / "config" / "capabilities.yaml",
        project_root=ROOT,
    )
    assert set(registry.names()) == EXPECTED


def test_direct_libraries_are_not_needlessly_isolated() -> None:
    registry = CapabilityRegistry.load(
        ROOT / "config" / "capabilities.yaml",
        project_root=ROOT,
    )
    for name in {
        "vectorbt",
        "optuna",
        "pybroker",
        "skfolio",
        "sb3_contrib",
    }:
        assert registry.get(name).mode is CapabilityMode.DIRECT_PYTHON


def test_workers_map_to_existing_integration_registry() -> None:
    capabilities = CapabilityRegistry.load(
        ROOT / "config" / "capabilities.yaml",
        project_root=ROOT,
    )
    integrations = IntegrationRegistry.load(
        ROOT / "config" / "integrations.yaml",
        project_root=ROOT,
    )
    for name in {"qlib", "vnpy", "finrl", "moondev", "nautilus"}:
        spec = capabilities.get(name)
        assert spec.mode is CapabilityMode.INTEGRATION_WORKER
        assert spec.integration in integrations.names()


def test_pipeline_uses_every_registered_engine() -> None:
    capabilities = CapabilityRegistry.load(
        ROOT / "config" / "capabilities.yaml",
        project_root=ROOT,
    )
    pipeline = ResearchPipeline.load(
        ROOT / "config" / "research_pipeline.yaml",
        capabilities=capabilities,
    )
    assert set(pipeline.engines()) == EXPECTED


def test_stocks_reference_is_not_imported_into_main_namespace() -> None:
    registry = CapabilityRegistry.load(
        ROOT / "config" / "capabilities.yaml",
        project_root=ROOT,
    )
    assert (
        registry.get("stocks_reference").mode
        is CapabilityMode.SUBPROCESS_REFERENCE
    )
