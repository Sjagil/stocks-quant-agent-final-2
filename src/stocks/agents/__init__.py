"""Shadow-only multi-agent research fabric.

No class in this package owns broker execution authority.
"""

from .contracts import AgentDecisionEnvelope, AgentVote
from .ensemble import fuse_agent_votes

__all__ = [
    "AgentDecisionEnvelope",
    "AgentVote",
    "fuse_agent_votes",
]
