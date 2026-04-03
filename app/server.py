"""
FastAPI backend for Pharma QA Agents local app.
"""

import asyncio
import json
import sys
import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Add parent dir to path for pharma_agents import
sys.path.insert(0, str(Path(__file__).parent.parent))

from pharma_agents.prompts import AGENT_ROLES
from pharma_agents.agent import PharmaAgent, DEFAULT_MODEL
from pharma_agents.workflows import WORKFLOWS, run_workflow
from app.database import (
    init_db, create_run, add_step, complete_run,
    get_runs, get_run, save_chat, get_chat_history, get_stats,
)

app = FastAPI(title="Pharma QA Agents", version="2.1.0")

# Static files and templates
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Custom Jinja2 filter for JSON parsing
import json as _json
templates.env.filters["from_json"] = lambda s: _json.loads(s) if s else {}

# Initialize database on startup
init_db()


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    stats = get_stats()
    recent = get_runs(limit=10)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "agents": AGENT_ROLES,
        "workflows": WORKFLOWS,
        "stats": stats,
        "recent_runs": recent,
    })


@app.get("/workflow/{name}", response_class=HTMLResponse)
async def workflow_page(request: Request, name: str):
    if name not in WORKFLOWS:
        return HTMLResponse("Workflow not found", status_code=404)
    wf = WORKFLOWS[name]
    return templates.TemplateResponse("workflow.html", {
        "request": request,
        "name": name,
        "workflow": wf,
        "agents": AGENT_ROLES,
    })


@app.get("/chat/{agent_role}", response_class=HTMLResponse)
async def chat_page(request: Request, agent_role: str):
    if agent_role not in AGENT_ROLES:
        return HTMLResponse("Agent not found", status_code=404)
    history = get_chat_history(agent_role)
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "agent_role": agent_role,
        "agent": AGENT_ROLES[agent_role],
        "history": history,
        "all_agents": AGENT_ROLES,
    })


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    runs = get_runs(limit=100)
    return templates.TemplateResponse("history.html", {
        "request": request,
        "runs": runs,
    })


@app.get("/run/{run_id}", response_class=HTMLResponse)
async def run_detail_page(request: Request, run_id: str):
    data = get_run(run_id)
    if not data:
        return HTMLResponse("Run not found", status_code=404)
    return templates.TemplateResponse("run_detail.html", {
        "request": request,
        "run": data["run"],
        "steps": data["steps"],
    })


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/agents")
async def api_agents():
    return AGENT_ROLES


@app.get("/api/workflows")
async def api_workflows():
    return {k: {"description": v["description"], "variables": v["variables"]}
            for k, v in WORKFLOWS.items()}


@app.get("/api/stats")
async def api_stats():
    return get_stats()


@app.get("/api/runs")
async def api_runs(limit: int = 50):
    return get_runs(limit)


@app.get("/api/run/{run_id}")
async def api_run(run_id: str):
    data = get_run(run_id)
    if not data:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return data


@app.post("/api/chat/{agent_role}")
async def api_chat(agent_role: str, request: Request):
    body = await request.json()
    message = body.get("message", "")
    if not message:
        return JSONResponse({"error": "No message"}, status_code=400)
    if agent_role not in AGENT_ROLES:
        return JSONResponse({"error": "Unknown agent"}, status_code=404)

    agent = PharmaAgent(role=agent_role)
    response = agent.query(message)
    save_chat(agent_role, message, response)
    return {"response": response, "agent": AGENT_ROLES[agent_role]["name"]}


@app.post("/api/workflow/run")
async def api_run_workflow(request: Request):
    """Start a workflow and return run_id. Use SSE endpoint to stream progress."""
    body = await request.json()
    workflow_name = body.get("workflow")
    variables = body.get("variables", {})
    precision = body.get("precision", False)

    if workflow_name not in WORKFLOWS:
        return JSONResponse({"error": "Unknown workflow"}, status_code=400)

    run_id = create_run(workflow_name, variables, precision)

    # Run workflow in background thread
    def _run():
        try:
            def on_step(result):
                add_step(
                    run_id, result.step_name, result.agent_role,
                    result.output, result.elapsed_seconds, result.success,
                    result.error,
                    getattr(result, 'review_score', None),
                    getattr(result, 'review_decision', None),
                    getattr(result, 'structured_data', None),
                )
                # Signal progress via a file (simple IPC)
                progress_file = Path(__file__).parent / f".progress_{run_id}"
                progress_file.write_text(json.dumps({
                    "step": result.step_name,
                    "agent": result.agent_role,
                    "success": result.success,
                    "elapsed": result.elapsed_seconds,
                    "review_score": getattr(result, 'review_score', 0),
                    "review_decision": getattr(result, 'review_decision', ''),
                }))

            wf_result = run_workflow(
                workflow_name, variables,
                on_step_complete=on_step,
                enable_review=precision,
                enable_structured_output=precision,
                enable_audit_trail=precision,
                enable_regulatory_context=precision,
                enable_live_regulatory=precision,
            )
            complete_run(
                run_id, "completed", wf_result.total_elapsed,
                wf_result.final_output, wf_result.summary(),
                wf_result.audit_trail_summary,
            )
        except Exception as e:
            complete_run(run_id, "failed", 0, "", str(e))
        finally:
            # Clean up progress file
            progress_file = Path(__file__).parent / f".progress_{run_id}"
            if progress_file.exists():
                progress_file.unlink()
            # Write done signal
            done_file = Path(__file__).parent / f".done_{run_id}"
            done_file.write_text("done")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {"run_id": run_id, "status": "started"}


@app.get("/api/workflow/progress/{run_id}")
async def api_workflow_progress(run_id: str):
    """SSE endpoint for real-time workflow progress."""
    async def event_stream():
        progress_file = Path(__file__).parent / f".progress_{run_id}"
        done_file = Path(__file__).parent / f".done_{run_id}"
        last_step = ""

        while True:
            # Check for completion
            if done_file.exists():
                done_file.unlink()
                data = get_run(run_id)
                if data:
                    yield f"data: {json.dumps({'type': 'complete', 'run': data['run'], 'steps': data['steps']})}\n\n"
                break

            # Check for step progress
            if progress_file.exists():
                try:
                    content = progress_file.read_text()
                    if content != last_step:
                        last_step = content
                        yield f"data: {json.dumps({'type': 'step', **json.loads(content)})}\n\n"
                except Exception:
                    pass

            await asyncio.sleep(0.5)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/export/{run_id}")
async def api_export(run_id: str, format: str = "markdown"):
    """Export a run's output."""
    data = get_run(run_id)
    if not data:
        return JSONResponse({"error": "Not found"}, status_code=404)

    run = data["run"]
    steps = data["steps"]

    if format == "markdown":
        lines = [
            f"# {run['workflow_name'].upper()} Investigation Report",
            f"\n**Run ID**: {run['id']}",
            f"**Date**: {run['started_at']}",
            f"**Status**: {run['status']}",
            f"**Precision Mode**: {'Yes' if run['precision_mode'] else 'No'}",
            f"**Total Time**: {run['total_elapsed']:.1f}s" if run['total_elapsed'] else "",
            f"\n**Variables**:",
        ]
        variables = json.loads(run['variables'])
        for k, v in variables.items():
            lines.append(f"- {k}: {v}")

        lines.append("\n---\n")
        lines.append("## Step-by-Step Analysis\n")

        for i, step in enumerate(steps, 1):
            review = ""
            if step['review_score']:
                review = f" | Review: {step['review_decision']} ({step['review_score']}/10)"
            lines.append(f"### Step {i}: {step['step_name']} ({step['agent_role']}){review}\n")
            lines.append(step['output'] or "(no output)")
            lines.append("\n---\n")

        if run['audit_trail']:
            lines.append("\n## Audit Trail\n")
            lines.append(run['audit_trail'])

        content = "\n".join(lines)
        return JSONResponse({"content": content, "filename": f"{run['workflow_name']}-{run['id']}.md"})

    return JSONResponse({"error": "Unsupported format"}, status_code=400)
