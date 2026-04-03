"""
Predefined pharma QA workflows — ready-to-use multi-agent pipelines.

Each workflow is a factory function that returns a configured AgentTeam.
Workflows support precision modes for quality gates, structured outputs,
regulatory reference injection, and audit trails.
"""

from pathlib import Path
from typing import Optional

from pharma_agents.agent import DEFAULT_MODEL
from pharma_agents.team import AgentTeam, WorkflowStep, StepType


def capa_workflow(
    enable_review: bool = False,
    enable_structured_output: bool = False,
    enable_audit_trail: bool = False,
    enable_regulatory_context: bool = False,
    audit_log_dir: Optional[Path] = None,
) -> AgentTeam:
    """
    Full CAPA investigation workflow.

    Variables: {deviation}, {batch}, {product} (optional)

    Pipeline:
      1. Quality → Deviation classification & regulatory assessment
      2. Lean + Risk (parallel) → Root cause analysis + risk assessment
      3. Project → CAPA action plan with timeline
      4. Document → Final investigation report & CAPA form
    """
    team = AgentTeam(
        name="CAPA Investigation Workflow",
        enable_review=enable_review,
        enable_structured_output=enable_structured_output,
        enable_audit_trail=enable_audit_trail,
        enable_regulatory_context=enable_regulatory_context,
        audit_log_dir=audit_log_dir,
    )

    team.add_step(WorkflowStep(
        name="Deviation Classification",
        agent_role="quality",
        prompt_template=(
            "A deviation has been reported. Classify this deviation, assess regulatory "
            "impact, and determine required actions.\n\n"
            "Deviation: {deviation}\n"
            "Batch: {batch}\n"
            "Product: {product}"
        ),
        use_prior_context=False,
        require_review=True,
        regulatory_topics=["deviation", "capa", "quality_system"],
    ))

    team.add_step(WorkflowStep(
        name="Root Cause & Risk Analysis",
        step_type=StepType.PARALLEL,
        prompt_template="Analyze the following deviation: {deviation} (Batch: {batch})",
        require_review=True,
        parallel_tasks=[
            {
                "name": "Root Cause Analysis",
                "agent_role": "lean",
                "prompt_template": (
                    "Perform a structured root cause analysis (5 Whys + Ishikawa) for "
                    "this deviation:\n\n{deviation}\n\nBatch: {batch}, Product: {product}"
                ),
                "regulatory_topics": ["deviation", "capa"],
            },
            {
                "name": "Risk Assessment",
                "agent_role": "risk",
                "prompt_template": (
                    "Perform an FMEA risk assessment for this deviation. Evaluate patient "
                    "safety, product quality, and data integrity risks.\n\n"
                    "Deviation: {deviation}\n"
                    "Batch: {batch}, Product: {product}"
                ),
                "regulatory_topics": ["risk", "deviation"],
            },
        ],
    ))

    team.add_step(WorkflowStep(
        name="CAPA Action Plan",
        agent_role="project",
        prompt_template=(
            "Based on the quality assessment, root cause analysis, and risk assessment "
            "provided in context, create a detailed CAPA action plan with:\n"
            "- Immediate containment actions\n"
            "- Corrective actions with owners and deadlines\n"
            "- Preventive actions with implementation timeline\n"
            "- Effectiveness check plan\n\n"
            "Deviation: {deviation}\nBatch: {batch}"
        ),
        require_review=True,
        regulatory_topics=["capa", "quality_system"],
    ))

    team.add_step(WorkflowStep(
        name="Investigation Report",
        step_type=StepType.SYNTHESIZE,
        synthesize_role="document",
        synthesize_prompt=(
            "Using all the analysis provided in context, produce a complete "
            "GMP-compliant Investigation Report and CAPA Form for:\n\n"
            "Deviation: {deviation}\nBatch: {batch}\nProduct: {product}\n\n"
            "Include all sections: description, classification, root cause, "
            "risk assessment, corrective actions, preventive actions, "
            "effectiveness criteria, and approval signatures."
        ),
        require_review=True,
        regulatory_topics=["documentation", "capa", "deviation"],
    ))

    return team


def validation_workflow(
    enable_review: bool = False,
    enable_structured_output: bool = False,
    enable_audit_trail: bool = False,
    enable_regulatory_context: bool = False,
    audit_log_dir: Optional[Path] = None,
) -> AgentTeam:
    """
    Equipment/process validation workflow.

    Variables: {equipment}, {validation_type}, {process} (optional)

    Pipeline:
      1. Validation → Strategy & protocol design
      2. Risk → Risk-based scope assessment
      3. Analytical → Test method requirements
      4. Document → Complete validation protocol
    """
    team = AgentTeam(
        name="Validation Protocol Workflow",
        enable_review=enable_review,
        enable_structured_output=enable_structured_output,
        enable_audit_trail=enable_audit_trail,
        enable_regulatory_context=enable_regulatory_context,
        audit_log_dir=audit_log_dir,
    )

    team.add_step(WorkflowStep(
        name="Validation Strategy",
        agent_role="validation",
        prompt_template=(
            "Design a validation strategy for the following:\n\n"
            "Equipment/System: {equipment}\n"
            "Validation Type: {validation_type}\n"
            "Process: {process}\n\n"
            "Include lifecycle approach, acceptance criteria framework, "
            "and regulatory basis."
        ),
        use_prior_context=False,
        require_review=True,
        regulatory_topics=["validation", "process_validation", "equipment_qualification"],
    ))

    team.add_step(WorkflowStep(
        name="Validation Risk Assessment",
        agent_role="risk",
        prompt_template=(
            "Perform a risk assessment to determine the validation scope, "
            "test priorities, and critical parameters for:\n\n"
            "Equipment/System: {equipment}\n"
            "Validation Type: {validation_type}\n"
            "Process: {process}\n\n"
            "Use FMEA to identify critical quality attributes and critical "
            "process parameters requiring qualification."
        ),
        require_review=True,
        regulatory_topics=["risk", "validation"],
    ))

    team.add_step(WorkflowStep(
        name="Analytical Requirements",
        agent_role="analytical",
        prompt_template=(
            "Define the analytical test methods required to support "
            "validation of:\n\n"
            "Equipment/System: {equipment}\n"
            "Validation Type: {validation_type}\n"
            "Process: {process}\n\n"
            "Include system suitability criteria, method references, and "
            "any method validation requirements."
        ),
        regulatory_topics=["analytical", "validation"],
    ))

    team.add_step(WorkflowStep(
        name="Validation Protocol",
        step_type=StepType.SYNTHESIZE,
        synthesize_role="document",
        synthesize_prompt=(
            "Using the validation strategy, risk assessment, and analytical "
            "requirements from context, produce a complete validation protocol "
            "document for:\n\n"
            "Equipment/System: {equipment}\n"
            "Validation Type: {validation_type}\n"
            "Process: {process}\n\n"
            "Include all protocol sections: objective, scope, responsibilities, "
            "equipment description, test procedures with acceptance criteria, "
            "deviation handling, and approval block."
        ),
        require_review=True,
        regulatory_topics=["documentation", "validation"],
    ))

    return team


def audit_readiness_workflow(
    enable_review: bool = False,
    enable_structured_output: bool = False,
    enable_audit_trail: bool = False,
    enable_regulatory_context: bool = False,
    audit_log_dir: Optional[Path] = None,
) -> AgentTeam:
    """
    Audit/inspection readiness workflow.

    Variables: {audit_type}, {scope}, {timeline} (optional)

    Pipeline:
      1. Audit → Gap analysis & readiness assessment
      2. Quality + Risk (parallel) → Compliance check + risk ranking
      3. Project → Remediation plan
      4. Document → Audit readiness checklist & briefing pack
    """
    team = AgentTeam(
        name="Audit Readiness Workflow",
        enable_review=enable_review,
        enable_structured_output=enable_structured_output,
        enable_audit_trail=enable_audit_trail,
        enable_regulatory_context=enable_regulatory_context,
        audit_log_dir=audit_log_dir,
    )

    team.add_step(WorkflowStep(
        name="Readiness Assessment",
        agent_role="audit",
        prompt_template=(
            "Perform an audit readiness assessment for:\n\n"
            "Audit Type: {audit_type}\n"
            "Scope: {scope}\n"
            "Timeline: {timeline}\n\n"
            "Identify key risk areas, likely inspector focus points, and "
            "critical documentation that must be current."
        ),
        use_prior_context=False,
        require_review=True,
        regulatory_topics=["audit", "quality_system"],
    ))

    team.add_step(WorkflowStep(
        name="Compliance & Risk Check",
        step_type=StepType.PARALLEL,
        require_review=True,
        parallel_tasks=[
            {
                "name": "Compliance Review",
                "agent_role": "quality",
                "prompt_template": (
                    "Review current regulatory compliance status for an "
                    "upcoming {audit_type} audit covering: {scope}\n\n"
                    "Identify any open deviations, overdue CAPAs, pending "
                    "change controls, or data integrity gaps that could be "
                    "flagged during inspection."
                ),
                "regulatory_topics": ["audit", "data_integrity", "quality_system"],
            },
            {
                "name": "Inspection Risk Assessment",
                "agent_role": "risk",
                "prompt_template": (
                    "Assess the risk profile for an upcoming {audit_type} "
                    "audit covering: {scope}\n\n"
                    "Rank risk areas by likelihood of inspector findings and "
                    "severity of potential observations (483, critical, major, minor)."
                ),
                "regulatory_topics": ["risk", "audit"],
            },
        ],
    ))

    team.add_step(WorkflowStep(
        name="Remediation Plan",
        agent_role="project",
        prompt_template=(
            "Based on the readiness assessment, compliance review, and risk "
            "assessment in context, create a remediation plan to close gaps "
            "before the audit.\n\n"
            "Audit Type: {audit_type}\nTimeline: {timeline}\n\n"
            "Prioritize actions by risk, assign owners, and set deadlines "
            "that allow time for QA review before the inspection date."
        ),
        regulatory_topics=["audit", "capa"],
    ))

    team.add_step(WorkflowStep(
        name="Audit Readiness Pack",
        step_type=StepType.SYNTHESIZE,
        synthesize_role="document",
        synthesize_prompt=(
            "Compile a complete Audit Readiness Pack using all analysis in "
            "context. Include:\n\n"
            "1. Executive summary of readiness status\n"
            "2. Gap analysis with remediation status\n"
            "3. Document checklist for the audit scope\n"
            "4. Key personnel preparation notes\n"
            "5. Back-room strategy and escalation contacts\n\n"
            "Audit Type: {audit_type}\nScope: {scope}"
        ),
        require_review=True,
        regulatory_topics=["documentation", "audit"],
    ))

    return team


def sop_creation_workflow(
    enable_review: bool = False,
    enable_structured_output: bool = False,
    enable_audit_trail: bool = False,
    enable_regulatory_context: bool = False,
    audit_log_dir: Optional[Path] = None,
) -> AgentTeam:
    """
    SOP creation workflow.

    Variables: {title}, {process}, {department} (optional)

    Pipeline:
      1. Quality → Regulatory requirements & compliance framework
      2. Lean → Process optimization & best practices
      3. Document → Complete SOP document
    """
    team = AgentTeam(
        name="SOP Creation Workflow",
        enable_review=enable_review,
        enable_structured_output=enable_structured_output,
        enable_audit_trail=enable_audit_trail,
        enable_regulatory_context=enable_regulatory_context,
        audit_log_dir=audit_log_dir,
    )

    team.add_step(WorkflowStep(
        name="Regulatory Framework",
        agent_role="quality",
        prompt_template=(
            "Identify all regulatory requirements and GMP references applicable "
            "to an SOP for:\n\n"
            "Title: {title}\n"
            "Process: {process}\n"
            "Department: {department}\n\n"
            "List specific regulations (FDA, EU GMP, ICH), required content "
            "sections, and any mandatory acceptance criteria."
        ),
        use_prior_context=False,
        require_review=True,
        regulatory_topics=["documentation", "quality_system"],
    ))

    team.add_step(WorkflowStep(
        name="Process Optimization",
        agent_role="lean",
        prompt_template=(
            "Review the process for potential optimization before documenting:\n\n"
            "Process: {process}\n"
            "Department: {department}\n\n"
            "Identify waste, suggest lean improvements, and recommend critical "
            "control points and in-process checks. All suggestions must be "
            "GMP-compatible."
        ),
    ))

    team.add_step(WorkflowStep(
        name="SOP Document",
        step_type=StepType.SYNTHESIZE,
        synthesize_role="document",
        synthesize_prompt=(
            "Write a complete, publication-ready SOP document using the "
            "regulatory framework and process optimization from context.\n\n"
            "Title: {title}\n"
            "Process: {process}\n"
            "Department: {department}\n\n"
            "Produce the full SOP with all required sections, ready for "
            "review and approval."
        ),
        require_review=True,
        regulatory_topics=["documentation"],
    ))

    return team


def oos_investigation_workflow(
    enable_review: bool = False,
    enable_structured_output: bool = False,
    enable_audit_trail: bool = False,
    enable_regulatory_context: bool = False,
    audit_log_dir: Optional[Path] = None,
) -> AgentTeam:
    """
    Out-of-Specification investigation workflow.

    Variables: {test_result}, {specification}, {method}, {batch}, {product}

    Pipeline:
      1. Analytical → Method review & Phase I lab investigation
      2. Quality → OOS classification & Phase II assessment
      3. Lean → Root cause analysis
      4. Risk → Impact assessment
      5. Document → Complete OOS investigation report
    """
    team = AgentTeam(
        name="OOS Investigation Workflow",
        enable_review=enable_review,
        enable_structured_output=enable_structured_output,
        enable_audit_trail=enable_audit_trail,
        enable_regulatory_context=enable_regulatory_context,
        audit_log_dir=audit_log_dir,
    )

    team.add_step(WorkflowStep(
        name="Phase I - Lab Investigation",
        agent_role="analytical",
        prompt_template=(
            "Perform a Phase I laboratory investigation for this OOS result:\n\n"
            "Test Result: {test_result}\n"
            "Specification: {specification}\n"
            "Method: {method}\n"
            "Batch: {batch}, Product: {product}\n\n"
            "Review: analyst technique, instrument performance, system suitability, "
            "sample preparation, reagent/standard integrity, and calculation verification."
        ),
        use_prior_context=False,
        require_review=True,
        regulatory_topics=["oos", "analytical"],
    ))

    team.add_step(WorkflowStep(
        name="OOS Classification",
        agent_role="quality",
        prompt_template=(
            "Based on the Phase I lab investigation in context, classify this OOS "
            "and determine whether Phase II (manufacturing) investigation is needed.\n\n"
            "Test Result: {test_result}\n"
            "Specification: {specification}\n"
            "Batch: {batch}, Product: {product}\n\n"
            "Assess regulatory reporting requirements and batch disposition impact."
        ),
        require_review=True,
        regulatory_topics=["oos", "deviation", "quality_system"],
    ))

    team.add_step(WorkflowStep(
        name="Phase II - Root Cause & Risk",
        step_type=StepType.PARALLEL,
        require_review=True,
        parallel_tasks=[
            {
                "name": "Manufacturing Root Cause",
                "agent_role": "lean",
                "prompt_template": (
                    "Perform Phase II manufacturing root cause analysis for this OOS:\n\n"
                    "Test Result: {test_result} (Spec: {specification})\n"
                    "Batch: {batch}, Product: {product}\n\n"
                    "Investigate: raw materials, equipment, process parameters, "
                    "environmental conditions, and personnel factors."
                ),
                "regulatory_topics": ["oos", "deviation"],
            },
            {
                "name": "OOS Risk Assessment",
                "agent_role": "risk",
                "prompt_template": (
                    "Assess patient safety and product quality risk for this OOS:\n\n"
                    "Test Result: {test_result} (Spec: {specification})\n"
                    "Batch: {batch}, Product: {product}\n\n"
                    "Evaluate: impact on released batches, field alert criteria, "
                    "recall assessment, and adjacent batch risk."
                ),
                "regulatory_topics": ["risk", "oos"],
            },
        ],
    ))

    team.add_step(WorkflowStep(
        name="OOS Investigation Report",
        step_type=StepType.SYNTHESIZE,
        synthesize_role="document",
        synthesize_prompt=(
            "Produce a complete OOS Investigation Report per FDA guidance, "
            "using all analysis from context.\n\n"
            "Test Result: {test_result}\n"
            "Specification: {specification}\n"
            "Method: {method}\n"
            "Batch: {batch}, Product: {product}\n\n"
            "Include: Phase I findings, Phase II findings, root cause conclusion, "
            "risk assessment summary, batch disposition recommendation, CAPA, "
            "and regulatory notification assessment."
        ),
        require_review=True,
        regulatory_topics=["documentation", "oos", "deviation"],
    ))

    return team


# ---------------------------------------------------------------------------
# Registry of all workflows
# ---------------------------------------------------------------------------

WORKFLOWS = {
    "capa": {
        "factory": capa_workflow,
        "description": "Full CAPA investigation: deviation → root cause → risk → action plan → report",
        "variables": ["deviation", "batch", "product"],
    },
    "validation": {
        "factory": validation_workflow,
        "description": "Validation protocol: strategy → risk scope → analytical methods → protocol document",
        "variables": ["equipment", "validation_type", "process"],
    },
    "audit": {
        "factory": audit_readiness_workflow,
        "description": "Audit readiness: gap analysis → compliance/risk check → remediation → readiness pack",
        "variables": ["audit_type", "scope", "timeline"],
    },
    "sop": {
        "factory": sop_creation_workflow,
        "description": "SOP creation: regulatory framework → process optimization → complete SOP",
        "variables": ["title", "process", "department"],
    },
    "oos": {
        "factory": oos_investigation_workflow,
        "description": "OOS investigation: lab investigation → classification → root cause/risk → report",
        "variables": ["test_result", "specification", "method", "batch", "product"],
    },
}


def run_workflow(
    workflow_name: str,
    variables: dict,
    model: str = DEFAULT_MODEL,
    on_step_complete=None,
    # Precision controls
    enable_review: bool = False,
    enable_structured_output: bool = False,
    enable_audit_trail: bool = False,
    enable_regulatory_context: bool = False,
    audit_log_dir: Optional[Path] = None,
) -> "WorkflowResult":
    """
    Convenience function to run a named workflow.

    Args:
        workflow_name: Key from WORKFLOWS dict.
        variables: Dict of variables for prompt templates.
        model: Claude model to use.
        on_step_complete: Optional progress callback.
        enable_review: Enable QA reviewer cross-validation.
        enable_structured_output: Require structured JSON in responses.
        enable_audit_trail: Generate ALCOA+ compliant audit trail.
        enable_regulatory_context: Auto-inject regulatory references.
        audit_log_dir: Directory for audit trail files.

    Returns:
        WorkflowResult with all outputs, reviews, and audit trail.

    Example — Standard mode (fast):
        result = run_workflow("capa", {"deviation": "...", "batch": "...", "product": "..."})

    Example — Precision mode (thorough, with all quality layers):
        result = run_workflow(
            "capa",
            {"deviation": "...", "batch": "...", "product": "..."},
            enable_review=True,
            enable_structured_output=True,
            enable_audit_trail=True,
            enable_regulatory_context=True,
            audit_log_dir=Path("outputs/audit"),
        )
    """
    if workflow_name not in WORKFLOWS:
        available = ", ".join(WORKFLOWS.keys())
        raise ValueError(f"Unknown workflow: '{workflow_name}'. Available: {available}")

    entry = WORKFLOWS[workflow_name]
    team = entry["factory"](
        enable_review=enable_review,
        enable_structured_output=enable_structured_output,
        enable_audit_trail=enable_audit_trail,
        enable_regulatory_context=enable_regulatory_context,
        audit_log_dir=audit_log_dir,
    )
    team.model = model
    return team.run(variables=variables, on_step_complete=on_step_complete)
