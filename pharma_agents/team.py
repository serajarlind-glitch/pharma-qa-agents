"""
Team orchestration engine for multi-agent pharma QA workflows.

Supports sequential chains, parallel fan-out, and synthesis patterns.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

from pharma_agents.agent import PharmaAgent, DEFAULT_MODEL
from pharma_agents.prompts import AGENT_ROLES


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


@dataclass
class WorkflowResult:
    """Complete workflow execution result."""
    workflow_name: str
    steps: list[StepResult] = field(default_factory=list)
    final_output: str = ""
    total_elapsed: float = 0.0

    @property
    def success(self) -> bool:
        return all(s.success for s in self.steps)

    def summary(self) -> str:
        lines = [
            f"## Workflow: {self.workflow_name}",
            f"**Status**: {'COMPLETE' if self.success else 'PARTIAL FAILURE'}",
            f"**Total time**: {self.total_elapsed:.1f}s",
            f"**Steps**: {len(self.steps)}",
            "",
        ]
        for i, step in enumerate(self.steps, 1):
            status = "OK" if step.success else "FAILED"
            lines.append(
                f"{i}. [{status}] {step.step_name} "
                f"({step.agent_role}, {step.elapsed_seconds:.1f}s)"
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


class AgentTeam:
    """
    Orchestrates a team of PharmaAgents through a defined workflow.

    Usage:
        team = AgentTeam()
        team.add_step(WorkflowStep(
            name="Quality Assessment",
            agent_role="quality",
            prompt_template="Assess this deviation: {deviation}",
        ))
        team.add_step(WorkflowStep(
            name="Root Cause Analysis",
            agent_role="lean",
            prompt_template="Perform 5 Whys on this deviation: {deviation}",
        ))
        result = team.run(variables={"deviation": "Batch failed dissolution"})
    """

    def __init__(
        self,
        name: str = "Pharma QA Team",
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        max_parallel: int = 4,
        client: Optional[anthropic.Anthropic] = None,
    ):
        self.name = name
        self.model = model
        self.temperature = temperature
        self.max_parallel = max_parallel
        self.client = client or anthropic.Anthropic()
        self.steps: list[WorkflowStep] = []

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
        # Replace workflow variables
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        # Replace step output references like {step:Quality Assessment}
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

    def _run_single(
        self, step: WorkflowStep, variables: dict, prior_outputs: dict
    ) -> StepResult:
        """Execute a single-agent step."""
        t0 = time.time()
        try:
            agent = self._make_agent(step.agent_role)
            prompt = self._format_prompt(step.prompt_template, variables, prior_outputs)
            context = self._build_context(prior_outputs) if step.use_prior_context else None
            output = agent.query(prompt, context=context)
            return StepResult(
                step_name=step.name,
                agent_role=step.agent_role,
                output=output,
                elapsed_seconds=time.time() - t0,
                success=True,
            )
        except Exception as e:
            return StepResult(
                step_name=step.name,
                agent_role=step.agent_role or "unknown",
                output="",
                elapsed_seconds=time.time() - t0,
                success=False,
                error=str(e),
            )

    def _run_parallel(
        self, step: WorkflowStep, variables: dict, prior_outputs: dict
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
                )
                future = executor.submit(
                    self._run_single, sub_step, variables, prior_outputs
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
            WorkflowResult with all step outputs.
        """
        variables = variables or {}
        prior_outputs: dict[str, str] = {}
        workflow_result = WorkflowResult(workflow_name=self.name)
        t_start = time.time()

        for step in self.steps:
            if step.step_type == StepType.SINGLE:
                result = self._run_single(step, variables, prior_outputs)
                workflow_result.steps.append(result)
                if result.success:
                    prior_outputs[step.name] = result.output
                if on_step_complete:
                    on_step_complete(result)

            elif step.step_type == StepType.PARALLEL:
                results = self._run_parallel(step, variables, prior_outputs)
                for r in results:
                    workflow_result.steps.append(r)
                    if r.success:
                        prior_outputs[r.step_name] = r.output
                    if on_step_complete:
                        on_step_complete(r)

            elif step.step_type == StepType.SYNTHESIZE:
                # Synthesis step: one agent combines all prior outputs
                synth_step = WorkflowStep(
                    name=step.name,
                    agent_role=step.synthesize_role,
                    prompt_template=step.synthesize_prompt,
                    use_prior_context=True,
                )
                result = self._run_single(synth_step, variables, prior_outputs)
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
        return workflow_result
