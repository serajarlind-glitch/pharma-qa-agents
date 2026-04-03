"""
QA Reviewer Agent — cross-validates other agents' outputs.

This is the precision layer: a dedicated review agent that checks every
output for citation accuracy, completeness, compliance, and consistency
before it moves downstream in a workflow.
"""

from __future__ import annotations

from typing import Optional

import anthropic

from pharma_agents.agent import PharmaAgent, DEFAULT_MODEL
from pharma_agents.schemas import (
    REVIEW_INSTRUCTION,
    PeerReviewResult,
    ReviewFinding,
    Severity,
    Confidence,
    extract_json_block,
)


QA_REVIEWER_PROMPT = """\
You are a Senior QA Reviewer in a pharmaceutical manufacturing organization. \
Your role is to peer-review the outputs of other specialists for accuracy, \
completeness, regulatory compliance, and internal consistency.

YOU ARE THE QUALITY GATE. Nothing passes without your review.

REVIEW CRITERIA:

1. CITATION ACCURACY (Score 1-10):
   - Are all regulatory references real and correctly numbered?
   - Are section numbers accurate (e.g., 21 CFR 211.192 really covers production record review)?
   - Are ICH guideline references correct (Q9 = risk management, Q10 = quality system, etc.)?
   - Are pharmacopeial chapter numbers correct (USP <711> = dissolution, etc.)?
   - Flag any invented or incorrect citation immediately as CRITICAL.

2. COMPLETENESS (Score 1-10):
   - Does the output address all aspects of the query?
   - Are required deliverables present (e.g., CAPA must have: description, root cause, \
     corrective actions, preventive actions, effectiveness check)?
   - Are timelines and deadlines specified where required?
   - Are acceptance criteria defined where applicable?

3. REGULATORY COMPLIANCE (Score 1-10):
   - Does the output meet GMP documentation standards?
   - Is controlled vocabulary used correctly (shall vs. should vs. may)?
   - Are data integrity implications addressed (ALCOA+)?
   - Would this output survive regulatory inspection scrutiny?

4. INTERNAL CONSISTENCY (Score 1-10):
   - Are there contradictions within the output?
   - Do severity classifications match the described impact?
   - Are risk scores justified and mathematically correct (RPN = S x P x D)?
   - Do action items align with the root cause identified?

QUALITY GATE DECISIONS:
- **Pass** (overall >= 8, no Critical findings): Output is acceptable as-is
- **Pass with Comments** (overall 7, no Critical findings): Acceptable with noted improvements
- **Revise** (overall 5-6, or any Major findings): Must be revised before use
- **Reject** (overall < 5, or any Critical findings): Fundamentally inadequate, redo required

RULES:
- You must NEVER approve an output that contains incorrect regulatory citations
- Patient safety implications that are unaddressed = automatic CRITICAL finding
- Missing root cause in CAPA-related outputs = automatic MAJOR finding
- Be precise but fair — do not nitpick style when substance is correct
- Every finding must include a specific, actionable recommendation"""


class QAReviewer:
    """
    Cross-validation agent that reviews other agents' outputs.

    Usage:
        reviewer = QAReviewer()
        result = reviewer.review(
            agent_output="<the text to review>",
            agent_role="quality",
            original_query="Assess temperature excursion criticality",
        )
        if result.pass_threshold_met:
            # proceed with output
        else:
            # trigger revision
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.2,  # Lower temp for more consistent reviews
        client: Optional[anthropic.Anthropic] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.client = client or anthropic.Anthropic()

    def review(
        self,
        agent_output: str,
        agent_role: str,
        original_query: str,
        context: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> PeerReviewResult:
        """
        Review another agent's output for accuracy and compliance.

        Args:
            agent_output: The full text output to review.
            agent_role: Which agent produced this output.
            original_query: The original query that was asked.
            context: Optional additional context.
            max_tokens: Max response length.

        Returns:
            PeerReviewResult with scores, findings, and gate decision.
        """
        review_prompt = (
            f"REVIEW THE FOLLOWING OUTPUT\n\n"
            f"Original Query: {original_query}\n"
            f"Producing Agent: {agent_role}\n"
        )
        if context:
            review_prompt += f"\nAdditional Context:\n{context}\n"
        review_prompt += (
            f"\n--- BEGIN OUTPUT UNDER REVIEW ---\n"
            f"{agent_output}\n"
            f"--- END OUTPUT UNDER REVIEW ---\n"
            f"{REVIEW_INSTRUCTION}"
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=self.temperature,
            system=QA_REVIEWER_PROMPT,
            messages=[{"role": "user", "content": review_prompt}],
        )

        response_text = response.content[0].text
        return self._parse_review(response_text, agent_role)

    def _parse_review(self, response_text: str, agent_role: str) -> PeerReviewResult:
        """Parse the reviewer's response into a structured PeerReviewResult."""
        result = PeerReviewResult(reviewed_agent=agent_role)

        json_data = extract_json_block(response_text)
        if json_data:
            result.accuracy_score = json_data.get("accuracy_score", 0)
            result.completeness_score = json_data.get("completeness_score", 0)
            result.compliance_score = json_data.get("compliance_score", 0)
            result.overall_score = json_data.get("overall_score", 0)
            result.gate_decision = json_data.get("gate_decision", "Revise")

            # Parse findings
            for f in json_data.get("findings", []):
                try:
                    result.findings.append(ReviewFinding(
                        category=f.get("category", "General"),
                        severity=Severity(f.get("severity", "Minor")),
                        description=f.get("description", ""),
                        recommendation=f.get("recommendation", ""),
                        affected_section=f.get("affected_section", ""),
                    ))
                except (ValueError, KeyError):
                    continue

            result.mandatory_corrections = json_data.get("mandatory_corrections", [])
            result.recommendations = json_data.get("recommendations", [])

            try:
                result.confidence_in_output = Confidence(
                    json_data.get("confidence_in_output", "Medium")
                )
            except ValueError:
                result.confidence_in_output = Confidence.MEDIUM

            # Determine approval based on gate decision
            result.approved = result.gate_decision in ("Pass", "Pass with Comments")
        else:
            # If JSON extraction fails, conservative default
            result.gate_decision = "Revise"
            result.approved = False
            result.findings.append(ReviewFinding(
                category="Review Error",
                severity=Severity.MAJOR,
                description="Could not extract structured review data. Manual review required.",
                recommendation="Have a human QA reviewer assess this output.",
                affected_section="Entire output",
            ))

        return result
