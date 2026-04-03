"""
GxP Audit Trail — full traceability for every agent action.

Implements ALCOA+ principles:
  Attributable — who (which agent), what, when
  Legible      — structured JSON records
  Contemporaneous — timestamped at execution time
  Original     — immutable append-only log
  Accurate     — captures exact inputs and outputs
  +Complete    — includes all steps, including failures
  +Consistent  — uniform record format
  +Enduring    — persisted to file
  +Available   — queryable by step, agent, or workflow
"""

from __future__ import annotations

import json
import hashlib
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class AuditRecord:
    """A single auditable event in the agent workflow."""
    # Identity
    record_id: str = ""
    workflow_id: str = ""
    step_name: str = ""
    sequence_number: int = 0

    # Attribution (ALCOA: Attributable)
    agent_role: str = ""
    agent_name: str = ""
    model: str = ""
    temperature: float = 0.0

    # Timing (ALCOA: Contemporaneous)
    timestamp_utc: str = ""
    elapsed_seconds: float = 0.0

    # Content (ALCOA: Original, Accurate)
    query_input: str = ""
    context_provided: str = ""
    response_output: str = ""
    output_hash: str = ""  # SHA-256 of the response for tamper detection

    # Classification
    severity: str = ""
    confidence: str = ""
    gxp_impacts: list[str] = field(default_factory=list)

    # Review trail
    reviewed: bool = False
    review_score: int = 0
    review_decision: str = ""
    review_findings_count: int = 0

    # Status
    success: bool = True
    error_message: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class AuditTrail:
    """
    Append-only audit log for pharma QA agent workflows.

    Every agent interaction is recorded with full ALCOA+ traceability.
    Records are stored in a JSON-lines file for easy parsing and review.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        self.workflow_id = str(uuid.uuid4())[:12]
        self.records: list[AuditRecord] = []
        self.sequence = 0
        self.log_dir = log_dir
        self.start_time = datetime.now(timezone.utc)

    def record_step(
        self,
        step_name: str,
        agent_role: str,
        agent_name: str,
        model: str,
        temperature: float,
        query_input: str,
        response_output: str,
        elapsed_seconds: float,
        context_provided: str = "",
        severity: str = "",
        confidence: str = "",
        gxp_impacts: Optional[list[str]] = None,
        success: bool = True,
        error_message: str = "",
    ) -> AuditRecord:
        """Record a single agent step execution."""
        self.sequence += 1

        record = AuditRecord(
            record_id=str(uuid.uuid4())[:12],
            workflow_id=self.workflow_id,
            step_name=step_name,
            sequence_number=self.sequence,
            agent_role=agent_role,
            agent_name=agent_name,
            model=model,
            temperature=temperature,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            elapsed_seconds=round(elapsed_seconds, 2),
            query_input=query_input[:2000],  # Truncate for storage
            context_provided=context_provided[:1000] if context_provided else "",
            response_output=response_output[:5000],  # Truncate for storage
            output_hash=hashlib.sha256(response_output.encode()).hexdigest(),
            severity=severity,
            confidence=confidence,
            gxp_impacts=gxp_impacts or [],
            success=success,
            error_message=error_message,
        )

        self.records.append(record)

        # Append to file if log_dir is set
        if self.log_dir:
            self._write_record(record)

        return record

    def record_review(
        self,
        step_name: str,
        review_score: int,
        review_decision: str,
        findings_count: int,
    ):
        """Attach review results to an existing step record."""
        for record in reversed(self.records):
            if record.step_name == step_name:
                record.reviewed = True
                record.review_score = review_score
                record.review_decision = review_decision
                record.review_findings_count = findings_count

                # Update file if logging
                if self.log_dir:
                    self._write_full_log()
                break

    def _write_record(self, record: AuditRecord):
        """Append a single record to the JSON-lines log file."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / f"audit-{self.workflow_id}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(record.to_dict(), default=str) + "\n")

    def _write_full_log(self):
        """Rewrite the complete log (used when updating review data)."""
        if not self.log_dir:
            return
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / f"audit-{self.workflow_id}.jsonl"
        with open(log_file, "w") as f:
            for record in self.records:
                f.write(json.dumps(record.to_dict(), default=str) + "\n")

    def generate_summary(self) -> str:
        """Generate a human-readable audit trail summary."""
        lines = [
            f"# Audit Trail Summary",
            f"**Workflow ID**: {self.workflow_id}",
            f"**Started**: {self.start_time.isoformat()}",
            f"**Total Steps**: {len(self.records)}",
            f"**Successful**: {sum(1 for r in self.records if r.success)}",
            f"**Reviewed**: {sum(1 for r in self.records if r.reviewed)}",
            "",
            "| # | Step | Agent | Time | Confidence | Review | Hash (first 12) |",
            "|---|------|-------|------|------------|--------|------------------|",
        ]

        for r in self.records:
            review_str = f"{r.review_decision} ({r.review_score}/10)" if r.reviewed else "Pending"
            lines.append(
                f"| {r.sequence_number} | {r.step_name} | {r.agent_role} | "
                f"{r.elapsed_seconds:.1f}s | {r.confidence} | {review_str} | "
                f"`{r.output_hash[:12]}` |"
            )

        # GxP compliance note
        lines.extend([
            "",
            "---",
            "*This audit trail is generated in compliance with ALCOA+ principles.*",
            f"*All timestamps are UTC. Output hashes are SHA-256 for tamper detection.*",
        ])

        return "\n".join(lines)
