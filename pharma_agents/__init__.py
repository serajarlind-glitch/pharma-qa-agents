"""
Pharma QA Agents - Claude-powered multi-agent system for pharmaceutical quality assurance.

A team of 9 specialized AI agents for GxP compliance, validation, CAPA,
risk assessment, lean manufacturing, and documentation.
"""

__version__ = "2.0.0"

from pharma_agents.agent import PharmaAgent
from pharma_agents.team import AgentTeam
from pharma_agents.workflows import WORKFLOWS, run_workflow

__all__ = ["PharmaAgent", "AgentTeam", "WORKFLOWS", "run_workflow"]
