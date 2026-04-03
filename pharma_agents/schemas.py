"""
Structured output schemas for pharma QA agent responses.

These define mandatory fields that every agent output must contain,
enforced via JSON extraction and validation after each agent response.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Enums for controlled vocabulary
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"
    INFORMATIONAL = "Informational"


class Confidence(str, Enum):
    HIGH = "High"       # >90% certain, based on explicit regulatory text
    MEDIUM = "Medium"   # 70-90%, based on interpretation of guidance
    LOW = "Low"         # <70%, professional judgment, limited precedent


class GxPImpact(str, Enum):
    PATIENT_SAFETY = "Patient Safety"
    PRODUCT_QUALITY = "Product Quality"
    DATA_INTEGRITY = "Data Integrity"
    REGULATORY_COMPLIANCE = "Regulatory Compliance"
    OPERATIONAL = "Operational"
    NONE = "None"


class ActionPriority(str, Enum):
    IMMEDIATE = "Immediate"     # Within 24 hours
    SHORT_TERM = "Short-term"   # Within 1-2 weeks
    MEDIUM_TERM = "Medium-term" # Within 1-3 months
    LONG_TERM = "Long-term"     # 3+ months


# ---------------------------------------------------------------------------
# Structured output models
# ---------------------------------------------------------------------------

@dataclass
class RegulatoryReference:
    """A single regulatory citation."""
    code: str            # e.g., "21 CFR 211.192"
    description: str     # What this section requires
    authority: str       # FDA, EMA, ICH, WHO, USP


@dataclass
class ActionItem:
    """A specific action to be taken."""
    action: str
    owner_role: str          # e.g., "QA Manager", "Production Supervisor"
    priority: ActionPriority
    deadline_description: str  # e.g., "Within 24 hours", "Before next batch"
    verification_method: str   # How to verify this action was completed


@dataclass
class RiskScore:
    """Structured risk assessment per FMEA methodology."""
    severity: int        # 1-5
    probability: int     # 1-5
    detectability: int   # 1-5
    rpn: int             # S x P x D
    justification: str   # Why these scores were assigned


@dataclass
class AgentOutput:
    """
    Standard structured output that every agent response must be parsed into.

    This ensures traceability, consistency, and mandatory content across all
    agent outputs — meeting GMP documentation standards.
    """
    # Identification
    agent_role: str
    agent_name: str
    query_summary: str

    # Classification
    severity: Severity
    confidence: Confidence
    gxp_impacts: list[GxPImpact]

    # Content
    summary: str                              # 2-3 sentence executive summary
    detailed_analysis: str                    # Full response text
    regulatory_references: list[RegulatoryReference]
    action_items: list[ActionItem]

    # Risk (optional, mainly for risk agent)
    risk_scores: list[RiskScore] = field(default_factory=list)

    # Quality metadata
    assumptions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    requires_human_review: bool = True
    escalation_needed: bool = False
    escalation_reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


# ---------------------------------------------------------------------------
# Review / cross-validation schemas
# ---------------------------------------------------------------------------

@dataclass
class ReviewFinding:
    """A single finding from the QA reviewer agent."""
    category: str             # "Citation Error", "Missing Analysis", "Inconsistency", etc.
    severity: Severity
    description: str
    recommendation: str
    affected_section: str     # Which part of the output has the issue


@dataclass
class PeerReviewResult:
    """Result of QA peer review of another agent's output."""
    reviewed_agent: str
    reviewer_agent: str = "qa_reviewer"

    # Scoring
    accuracy_score: int = 0      # 1-10
    completeness_score: int = 0  # 1-10
    compliance_score: int = 0    # 1-10
    overall_score: int = 0       # 1-10

    # Quality gate
    approved: bool = False
    gate_decision: str = ""      # "Pass", "Pass with Comments", "Revise", "Reject"

    # Findings
    findings: list[ReviewFinding] = field(default_factory=list)
    mandatory_corrections: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Confidence in the original output
    confidence_in_output: Confidence = Confidence.MEDIUM

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def pass_threshold_met(self) -> bool:
        """Quality gate: overall score >= 7 and no critical findings."""
        has_critical = any(f.severity == Severity.CRITICAL for f in self.findings)
        return self.overall_score >= 7 and not has_critical


# ---------------------------------------------------------------------------
# Extraction prompt — appended to agent queries to get structured data
# ---------------------------------------------------------------------------

STRUCTURED_OUTPUT_INSTRUCTION = """\

IMPORTANT — STRUCTURED OUTPUT REQUIREMENT:
After your detailed analysis, you MUST append a JSON block enclosed in
```json
...
```
containing the following fields:
{
  "severity": "Critical|Major|Minor|Informational",
  "confidence": "High|Medium|Low",
  "gxp_impacts": ["Patient Safety", "Product Quality", "Data Integrity", "Regulatory Compliance", "Operational"],
  "summary": "<2-3 sentence executive summary>",
  "regulatory_references": [
    {"code": "<regulation section>", "description": "<what it requires>", "authority": "<FDA|EMA|ICH|WHO|USP>"}
  ],
  "action_items": [
    {"action": "<specific action>", "owner_role": "<role>", "priority": "Immediate|Short-term|Medium-term|Long-term", "deadline_description": "<when>", "verification_method": "<how to verify>"}
  ],
  "assumptions": ["<any assumptions made>"],
  "limitations": ["<any limitations of this analysis>"],
  "requires_human_review": true,
  "escalation_needed": false,
  "escalation_reason": ""
}
This structured data is mandatory for traceability and GMP compliance."""


REVIEW_INSTRUCTION = """\

PEER REVIEW REQUIREMENT:
You are reviewing another agent's output. Evaluate it for:
1. ACCURACY — Are regulatory citations correct and current?
2. COMPLETENESS — Are all required elements addressed?
3. COMPLIANCE — Does the response meet GMP documentation standards?
4. CONSISTENCY — Are there internal contradictions?

Append a JSON block:
```json
{
  "accuracy_score": <1-10>,
  "completeness_score": <1-10>,
  "compliance_score": <1-10>,
  "overall_score": <1-10>,
  "gate_decision": "Pass|Pass with Comments|Revise|Reject",
  "findings": [
    {"category": "<type>", "severity": "Critical|Major|Minor|Informational", "description": "<detail>", "recommendation": "<fix>", "affected_section": "<section>"}
  ],
  "mandatory_corrections": ["<correction needed>"],
  "recommendations": ["<improvement suggestion>"],
  "confidence_in_output": "High|Medium|Low"
}
```"""


def extract_json_block(text: str) -> Optional[dict]:
    """Extract the last JSON code block from agent response text."""
    pattern = r'```json\s*\n(.*?)\n\s*```'
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        try:
            return json.loads(matches[-1])
        except json.JSONDecodeError:
            return None
    return None
