#!/usr/bin/env python3
"""
Pharma QA Agents — CLI entry point.

Usage:
    # List agents and workflows
    python run.py --list

    # Single agent query
    python run.py agent quality "Assess temperature excursion: 12°C for 45 min"

    # Run a predefined workflow
    python run.py workflow capa \
        --var deviation="Batch 2024-0892 failed dissolution, 68% at 30 min (spec ≥80%)" \
        --var batch="2024-0892" \
        --var product="Aspirin 500mg tablets"

    # Interactive mode
    python run.py agent lean --interactive

    # Save output to file
    python run.py agent document "Create CAPA form" --output capa-form.md
"""

import argparse
import sys
from pathlib import Path

from pharma_agents.agent import PharmaAgent, DEFAULT_MODEL
from pharma_agents.prompts import AGENT_ROLES
from pharma_agents.workflows import WORKFLOWS, run_workflow


def list_all():
    """List available agents and workflows."""
    print("\n=== Pharma QA Agents ===\n")
    print("AGENTS:")
    for key, info in AGENT_ROLES.items():
        print(f"  {key:15s}  {info['name']} ({info['title']})")

    print("\nWORKFLOWS:")
    for key, info in WORKFLOWS.items():
        vars_str = ", ".join(f"{{{v}}}" for v in info["variables"])
        print(f"  {key:15s}  {info['description']}")
        print(f"  {'':15s}  Variables: {vars_str}")
    print()


def run_agent_query(args):
    """Run a single agent query."""
    agent = PharmaAgent(
        role=args.agent_role,
        model=args.model or DEFAULT_MODEL,
        temperature=args.temperature,
    )

    if args.interactive:
        print(f"\n{'='*60}")
        print(f"  {agent.name} ({agent.title})")
        print(f"  Model: {agent.model}")
        print(f"{'='*60}")
        print("  Type 'exit' to quit, 'clear' to reset history.\n")

        while True:
            try:
                user_input = input("You: ").strip()
                if not user_input:
                    continue
                if user_input.lower() == "exit":
                    break
                if user_input.lower() == "clear":
                    agent.clear_history()
                    print("  [History cleared]\n")
                    continue

                response = agent.query(user_input, keep_history=True)
                print(f"\n{agent.name}:\n{response}\n")
            except (KeyboardInterrupt, EOFError):
                break
        return

    if not args.query:
        print("Error: provide a query or use --interactive")
        sys.exit(1)

    query = " ".join(args.query)
    response = agent.query(query)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(response)
        print(f"Saved to {args.output}")
    else:
        print(response)


def run_workflow_cmd(args):
    """Run a named workflow."""
    # Parse variables
    variables = {}
    if args.var:
        for v in args.var:
            if "=" not in v:
                print(f"Error: variable must be key=value, got: {v}")
                sys.exit(1)
            key, value = v.split("=", 1)
            variables[key.strip()] = value.strip()

    def on_step(result):
        status = "OK" if result.success else "FAILED"
        review = ""
        if result.review_decision:
            review = f" | Review: {result.review_decision} ({result.review_score}/10)"
        print(f"  [{status}] {result.step_name} ({result.elapsed_seconds:.1f}s){review}")

    # Determine precision mode
    precision = getattr(args, "precision", False)
    audit_dir = Path(args.output).parent / "audit" if args.output else None

    print(f"\nRunning workflow: {args.workflow_name}")
    if precision:
        print("  Mode: PRECISION (review + structured output + audit trail + regulatory context)")
    print()

    live_reg = getattr(args, "live", False)

    result = run_workflow(
        args.workflow_name,
        variables=variables,
        model=args.model or DEFAULT_MODEL,
        on_step_complete=on_step,
        enable_review=precision,
        enable_structured_output=precision,
        enable_audit_trail=precision,
        enable_regulatory_context=precision,
        enable_live_regulatory=precision or live_reg,
        audit_log_dir=audit_dir if precision else None,
    )

    print(f"\n{result.summary()}\n")

    if result.audit_trail_summary:
        print(result.audit_trail_summary)
        print()

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(result.final_output)
        print(f"Final output saved to {args.output}")
        if result.audit_trail_summary:
            audit_file = Path(args.output).parent / "audit-trail.md"
            audit_file.write_text(result.audit_trail_summary)
            print(f"Audit trail saved to {audit_file}")
    else:
        print("\n--- Final Output ---\n")
        print(result.final_output)


def main():
    parser = argparse.ArgumentParser(
        description="Pharma QA Agents — Claude-powered multi-agent system",
    )
    parser.add_argument("--list", action="store_true", help="List agents and workflows")
    parser.add_argument("--model", type=str, help="Claude model override")
    parser.add_argument("--temperature", type=float, default=0.3)

    sub = parser.add_subparsers(dest="command")

    # agent sub-command
    agent_p = sub.add_parser("agent", help="Query a single agent")
    agent_p.add_argument("agent_role", choices=list(AGENT_ROLES.keys()))
    agent_p.add_argument("query", nargs="*", help="Your question")
    agent_p.add_argument("-i", "--interactive", action="store_true")
    agent_p.add_argument("-o", "--output", type=str, help="Save response to file")

    # workflow sub-command
    wf_p = sub.add_parser("workflow", help="Run a multi-agent workflow")
    wf_p.add_argument("workflow_name", choices=list(WORKFLOWS.keys()))
    wf_p.add_argument("-v", "--var", action="append", help="key=value variable")
    wf_p.add_argument("-o", "--output", type=str, help="Save final output to file")
    wf_p.add_argument(
        "-p", "--precision", action="store_true",
        help="Enable precision mode: QA review, structured output, audit trail, regulatory context",
    )
    wf_p.add_argument(
        "--live", action="store_true",
        help="Enable live regulatory intelligence (checks official sources for current data)",
    )

    args = parser.parse_args()

    if args.list:
        list_all()
        return

    if args.command == "agent":
        run_agent_query(args)
    elif args.command == "workflow":
        run_workflow_cmd(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
