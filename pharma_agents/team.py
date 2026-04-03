"""
Team orchestration engine for multi-agent pharma QA workflows.

Supports sequential chains, parallel fan-out, synthesis patterns,
quality gates with peer review, audit trails, and structured outputs.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

from pharma_agents.agent import PharmaAgent, DEFAULT_MODEL
from pharma_agents.prompts import AGENT_ROLES
from pharma_agents.schemas import (
    STRUCTURED_OUTPUT_INSTRUCTION,
    extract_json_block,
)
from pharma_agents.reviewer import QAReviewer
from pharma_agents.audit_trail import AuditTrail
from pharma_agents.standards import get_regulations_for_topic, format_regulation_context


class StepType(str, Enum):
    SINGLE = "single"
    PARALLEL = "parallel"
    SYNTHESIZE = "synthesize"


@dataclass
class StepResult:
    """Result from a single workflow step."""
    step_name: str
    agent_role: str
    output: str
    elapsed_seconds: float
    success: bool
    error: Optional[str] = None
    # Structured metadata extracted from output
    structured_data: Optional[dict] = None
    # Review results
    review_score: int = 0
    review_decision: str = ""
    review_approved: bool = False


@dataclass
class WorkflowResult:
    """Complete workflow execution result."""
    workflow_name: str
    steps: list[StepResult] = field(default_factory=list)
    final_output: str = ""
    total_elapsed: float = 0.0
    audit_trail_summary: str = ""

    @property
    def success(self) -> bool:
        return all(s.success for s in self.steps)

    @property
    def all_reviewed(self) -> bool:
        return all(s.review_decision != "" for s in self.steps if s.success)

    def summary(self) -> str:
        lines = [
            f"## Workflow: {self.workflow_name}",
            f"**Status**: {'COMPLETE' if self.success else 'PARTIAL FAILURE'}",
            f"**Total time**: {self.total_elapsed:.1f}s",
            f"**Steps**: {len(self.steps)}",
            f"**All reviewed**: {self.all_reviewed}",
            "",
            "| # | Step | Agent | Time | Review | Score |",
            "|---|------|-------|------|--------|-------|",
        ]
        for i, step in enumerate(self.steps, 1):
            status = "OK" if step.success else "FAIL"
            review = step.review_decision or "—"
            score = f"{step.review_score}/10" if step.review_score else "—"
            lines.append(
                f"| {i} | {step.step_name} | {step.agent_role} | "
                f"{step.elapsed_seconds:.1f}s | {review} | {score} |"
            )
        return "\n".join(lines)


@dataclass
class WorkflowStep:
    """Definition of a single step in a workflow."""
    name: str
    step_type: StepType = StepType.SINGLE
    # For SINGLE steps
    agent_role: Optional[str] = None
    prompt_template: str = ""
    # For PARALLEL steps
    parallel_tasks: list[dict] = field(default_factory=list)
    # For SYNTHESIZE steps — agent that combines prior outputs
    synthesize_role: Optional[str] = None
    synthesize_prompt: str = ""
    # Whether to pass all prior outputs as context
    use_prior_context: bool = True
    # Quality gate: require peer review before proceeding
    require_review: bool = False
    # Regulatory topic hints for auto-injecting reference context
    regulatory_topics: list[str] = field(default_factory=list)


class AgentTeam:
    """
    Orchestrates a team of PharmaAgents through a defined workflow.

    Features:
    - Sequential, parallel, and synthesis execution patterns
    - Quality gates with QA reviewer cross-validation
    - Automatic regulatory reference injection
    - Structured output extraction
    - Full ALCOA+ audit trail
    - Configurable review thresholds and retry logic

    Usage:
        team = AgentTeam(enable_review=True, enable_audit_trail=True)
        team.add_step(WorkflowStep(
            name="Quality Assessment",
            agent_role="quality",
            prompt_template="Assess this deviation: {deviation}",
            require_review=True,
            regulatory_topics=["deviation", "capa"],
        ))
        result = team.run(variables={"deviation": "Batch failed dissolution"})
        print(result.audit_trail_summary)
    """

    def __init__(
        self,
        name: str = "Pharma QA Team",
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        max_parallel: int = 4,
        client: Optional[anthropic.Anthropic] = None,
        # Precision controls
        enable_review: bool = False,
        enable_structured_output: bool = False,
        enable_audit_trail: bool = False,
        enable_regulatory_context: bool = False,
        # Quality gate thresholds
        review_min_score: int = 7,
        max_revision_attempts: int = 1,
        # Audit trail output
        audit_log_dir: Optional[Path] = None,
    ):
        self.name = name
        self.model = model
        self.temperature = temperature
        self.max_parallel = max_parallel
        self.client = client or anthropic.Anthropic()
        self.steps: list[WorkflowStep] = []

        # Precision layers
        self.enable_review = enable_review
        self.enable_structured_output = enable_structured_output
        self.enable_audit_trail = enable_audit_trail
        self.enable_regulatory_context = enable_regulatory_context
        self.review_min_score = review_min_score
        self.max_revision_attempts = max_revision_attempts

        # Initialize subsystems
        self.reviewer = QAReviewer(model=model, client=self.client) if enable_review else None
        self.audit = AuditTrail(log_dir=audit_log_dir) if enable_audit_trail else None

    def add_step(self, step: WorkflowStep) -> "AgentTeam":
        """Add a step to the workflow. Returns self for chaining."""
        self.steps.append(step)
        return self

    def _make_agent(self, role: str) -> PharmaAgent:
        return PharmaAgent(
            role=role,
            model=self.model,
            temperature=self.temperature,
            client=self.client,
        )

    def _format_prompt(self, template: str, variables: dict, prior_outputs: dict) -> str:
        """Replace {variable} placeholders and inject prior context."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        for step_name, output in prior_outputs.items():
            result = result.replace(f"{{step:{step_name}}}", output)
        return result

    def _build_context(self, prior_outputs: dict) -> str:
        """Build context string from all prior step outputs."""
        if not prior_outputs:
            return ""
        sections = []
        for step_name, output in prior_outputs.items():
            sections.append(f"### {step_name}\n{output}")
        return "\n\n---\n\n".join(sections)

    def _inject_regulatory_context(self, prompt: str, topics: list[str]) -> str:
        """Auto-inject relevant regulatory references based on topic hints."""
        if not self.enable_regulatory_context or not topics:
            return prompt
        all_regs = []
        for topic in topics:
            all_regs.extend(get_regulations_for_topic(topic))
        # Deduplicate
        seen = set()
        unique = []
        for r in all_regs:
            if r.code not in seen:
                seen.add(r.code)
                unique.append(r)
        if unique:
            reg_context = format_regulation_context(unique)
            return f"{reg_context}\n\n---\n\n{prompt}"
        return prompt

    def _inject_structured_output_requirement(self, prompt: str) -> str:
        """Append structured output instruction to the prompt."""
        if self.enable_structured_output:
            return prompt + STRUCTURED_OUTPUT_INSTRUCTION
        return prompt

    def _run_single(
        self,
        step: WorkflowStep,
        variables: dict,
        prior_outputs: dict,
        original_query: str = "",
    ) -> StepResult:
        """Execute a single-agent step with optional review and audit."""
        t0 = time.time()
        try:
            agent = self._make_agent(step.agent_role)
            prompt = self._format_prompt(step.prompt_template, variables, prior_outputs)

            # Inject regulatory context
            prompt = self._inject_regulatory_context(prompt, step.regulatory_topics)

            # Inject structured output requirement
            prompt = self._inject_structured_output_requirement(prompt)

            context = self._build_context(prior_outputs) if step.use_prior_context else None
            output = agent.query(prompt, context=context)
            elapsed = time.time() - t0

            # Extract structured data if enabled
            structured_data = None
            if self.enable_structured_output:
                structured_data = extract_json_block(output)

            result = StepResult(
                step_name=step.name,
                agent_role=step.agent_role,
                output=output,
                elapsed_seconds=elapsed,
                success=True,
                structured_data=structured_data,
            )

            # Record to audit trail
            if self.audit:
                severity = ""
                confidence = ""
                gxp_impacts = []
                if structured_data:
                    severity = structured_data.get("severity", "")
                    confidence = structured_data.get("confidence", "")
                    gxp_impacts = structured_data.get("gxp_impacts", [])

                self.audit.record_step(
                    step_name=step.name,
                    agent_role=step.agent_role,
                    agent_name=AGENT_ROLES.get(step.agent_role, {}).get("name", ""),
                    model=self.model,
                    temperature=self.temperature,
                    query_input=prompt,
                    response_output=output,
                    elapsed_seconds=elapsed,
                    context_provided=context or "",
                    severity=severity,
                    confidence=confidence,
                    gxp_impacts=gxp_impacts,
                )

            # Quality gate: peer review
            if self.enable_review and (step.require_review or self.enable_review):
                result = self._apply_review_gate(
                    result, step, variables, prior_outputs, original_query
                )

            return result

        except Exception as e:
            elapsed = time.time() - t0
            if self.audit:
                self.audit.record_step(
                    step_name=step.name,
                    agent_role=step.agent_role or "unknown",
                    agent_name="",
                    model=self.model,
                    temperature=self.temperature,
                    query_input="",
                    response_output="",
                    elapsed_seconds=elapsed,
                    success=False,
                    error_message=str(e),
                )
            return StepResult(
                step_name=step.name,
                agent_role=step.agent_role or "unknown",
                output="",
                elapsed_seconds=elapsed,
                success=False,
                error=str(e),
            )

    def _apply_review_gate(
        self,
        result: StepResult,
        step: WorkflowStep,
        variables: dict,
        prior_outputs: dict,
        original_query: str,
    ) -> StepResult:
        """Run QA review on a step result. Retry if below threshold."""
        if not self.reviewer:
            return result

        query_summary = self._format_prompt(
            step.prompt_template, variables, prior_outputs
        )[:500]

        review = self.reviewer.review(
            agent_output=result.output,
            agent_role=result.agent_role,
            original_query=query_summary,
        )

        result.review_score = review.overall_score
        result.review_decision = review.gate_decision
        result.review_approved = review.approved

        # Record review in audit trail
        if self.audit:
            self.audit.record_review(
                step_name=step.name,
                review_score=review.overall_score,
                review_decision=review.gate_decision,
                findings_count=len(review.findings),
            )

        # If review fails and we have revision budget, retry with feedback
        if not review.approved and self.max_revision_attempts > 0:
            corrections = "\n".join(
                f"- {c}" for c in review.mandatory_corrections
            )
            findings_text = "\n".join(
                f"- [{f.severity.value}] {f.description}: {f.recommendation}"
                for f in review.findings
            )

            revision_prompt = (
                f"Your previous output was reviewed and rated {review.overall_score}/10 "
                f"({review.gate_decision}). Please revise addressing these findings:\n\n"
                f"MANDATORY CORRECTIONS:\n{corrections}\n\n"
                f"FINDINGS:\n{findings_text}\n\n"
                f"Original output to revise:\n{result.output}"
            )

            agent = self._make_agent(step.agent_role)
            revision_prompt = self._inject_structured_output_requirement(revision_prompt)
            context = self._build_context(prior_outputs) if step.use_prior_context else None

            t0 = time.time()
            revised_output = agent.query(revision_prompt, context=context)
            revision_elapsed = time.time() - t0

            # Update result with revision
            result.output = revised_output
            result.elapsed_seconds += revision_elapsed

            if self.enable_structured_output:
                result.structured_data = extract_json_block(revised_output)

            # Record revision in audit trail
            if self.audit:
                self.audit.record_step(
                    step_name=f"{step.name} (Revision)",
                    agent_role=step.agent_role,
                    agent_name=AGENT_ROLES.get(step.agent_role, {}).get("name", ""),
                    model=self.model,
                    temperature=self.temperature,
                    query_input=revision_prompt[:2000],
                    response_output=revised_output,
                    elapsed_seconds=revision_elapsed,
                )

        return result

    def _run_parallel(
        self,
        step: WorkflowStep,
        variables: dict,
        prior_outputs: dict,
        original_query: str = "",
    ) -> list[StepResult]:
        """Execute multiple agents in parallel."""
        results = []
        with ThreadPoolExecutor(max_workers=self.max_parallel) as executor:
            futures = {}
            for task in step.parallel_tasks:
                sub_step = WorkflowStep(
                    name=f"{step.name} — {task.get('name', task['agent_role'])}",
                    agent_role=task["agent_role"],
                    prompt_template=task.get("prompt_template", step.prompt_template),
                    use_prior_context=step.use_prior_context,
                    require_review=step.require_review,
                    regulatory_topics=task.get("regulatory_topics", step.regulatory_topics),
                )
                future = executor.submit(
                    self._run_single, sub_step, variables, prior_outputs, original_query
                )
                futures[future] = sub_step.name

            for future in as_completed(futures):
                results.append(future.result())

        return results

    def run(
        self,
        variables: Optional[dict] = None,
        on_step_complete=None,
    ) -> WorkflowResult:
        """
        Execute the full workflow.

        Args:
            variables: Dict of variables to inject into prompt templates.
            on_step_complete: Optional callback(step_result) for progress reporting.

        Returns:
            WorkflowResult with all step outputs, review scores, and audit trail.
        """
        variables = variables or {}
        prior_outputs: dict[str, str] = {}
        workflow_result = WorkflowResult(workflow_name=self.name)
        t_start = time.time()

        # Build a summary of the original query for review context
        original_query = " | ".join(f"{k}={v}" for k, v in variables.items())

        for step in self.steps:
            if step.step_type == StepType.SINGLE:
                result = self._run_single(step, variables, prior_outputs, original_query)
                workflow_result.steps.append(result)
                if result.success:
                    prior_outputs[step.name] = result.output
                if on_step_complete:
                    on_step_complete(result)

            elif step.step_type == StepType.PARALLEL:
                results = self._run_parallel(step, variables, prior_outputs, original_query)
                for r in results:
                    workflow_result.steps.append(r)
                    if r.success:
                        prior_outputs[r.step_name] = r.output
                    if on_step_complete:
                        on_step_complete(r)

            elif step.step_type == StepType.SYNTHESIZE:
                synth_step = WorkflowStep(
                    name=step.name,
                    agent_role=step.synthesize_role,
                    prompt_template=step.synthesize_prompt,
                    use_prior_context=True,
                    require_review=step.require_review,
                    regulatory_topics=step.regulatory_topics,
                )
                result = self._run_single(
                    synth_step, variables, prior_outputs, original_query
                )
                workflow_result.steps.append(result)
                if result.success:
                    prior_outputs[step.name] = result.output
                if on_step_complete:
                    on_step_complete(result)

        # Final output is the last successful step
        for step_result in reversed(workflow_result.steps):
            if step_result.success:
                workflow_result.final_output = step_result.output
                break

        workflow_result.total_elapsed = time.time() - t_start

        # Generate audit trail summary
        if self.audit:
            workflow_result.audit_trail_summary = self.audit.generate_summary()

        return workflow_result
