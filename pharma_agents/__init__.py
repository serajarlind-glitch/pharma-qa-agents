"""
Pharma QA Agents - Claude-powered multi-agent system for pharmaceutical quality assurance.

A team of 9 specialized AI agents for GxP compliance, validation, CAPA,
risk assessment, lean manufacturing, and documentation.

Precision layers:
- QA Reviewer: Cross-validates every agent output for citation accuracy and compliance
- Structured Outputs: Mandatory JSON metadata (severity, confidence, actions, references)
- Regulatory Standards DB: Embedded citation index for 18+ regulations
- ALCOA+ Audit Trail: Full traceability for every agent interaction
"""

__version__ = "2.1.0"

from pharma_agents.agent import PharmaAgent
from pharma_agents.team import AgentTeam, WorkflowStep, StepType
from pharma_agents.reviewer import QAReviewer
from pharma_agents.workflows import WORKFLOWS, run_workflow
from pharma_agents.audit_trail import AuditTrail
from pharma_agents.schemas import AgentOutput, PeerReviewResult
from pharma_agents.regulatory_intelligence import RegulatoryIntelligence

__all__ = [
    "PharmaAgent",
    "AgentTeam",
    "WorkflowStep",
    "StepType",
    "QAReviewer",
    "WORKFLOWS",
    "run_workflow",
    "AuditTrail",
    "AgentOutput",
    "PeerReviewResult",
    "RegulatoryIntelligence",
]
