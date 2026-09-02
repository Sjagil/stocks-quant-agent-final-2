"""Production runtime v2.41.

Broker writes remain fail-closed unless explicit runtime authority gates pass.
"""
from .contracts_v2_41 import ExecutionMode, ProductionIntent
__all__ = ["ExecutionMode", "ProductionIntent"]
