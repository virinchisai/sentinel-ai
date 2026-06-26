"""Agent planner: decomposes complex queries into sub-tasks and executes them.

The planner uses the LLM to generate a step-by-step plan, then executes each
step through the orchestrator's tool-calling loop. Destructive actions (e.g.
creating GitHub issues) can be gated behind human approval.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

DESTRUCTIVE_TOOLS = {"github_create_issue", "github_comment_on_issue"}

PLANNING_PROMPT = """You are a planning agent. Given the user's request, break it into a numbered list of concrete steps.
Each step should be a single action that can be accomplished with one tool call or a direct answer.
If a step requires a destructive action (creating issues, sending emails), mark it with [APPROVAL_REQUIRED].

Respond with ONLY a JSON array of step objects:
[{"step": 1, "description": "...", "needs_approval": false}, ...]

User request: {query}"""


@dataclass
class PlanStep:
    step: int
    description: str
    needs_approval: bool = False
    status: str = "pending"  # pending | approved | completed | skipped
    result: str = ""


@dataclass
class Plan:
    query: str
    steps: list[PlanStep] = field(default_factory=list)
    requires_approval: bool = False


def create_plan(llm_provider, query: str) -> Plan:
    """Use the LLM to decompose a query into a plan."""
    messages = [{"role": "user", "content": PLANNING_PROMPT.format(query=query)}]
    response = llm_provider.chat(messages, tools=[])

    try:
        steps_data = json.loads(response.text)
        steps = [
            PlanStep(
                step=s.get("step", i + 1),
                description=s["description"],
                needs_approval=s.get("needs_approval", False),
            )
            for i, s in enumerate(steps_data)
        ]
    except (json.JSONDecodeError, KeyError):
        steps = [PlanStep(step=1, description=query)]

    plan = Plan(query=query, steps=steps)
    plan.requires_approval = any(s.needs_approval for s in steps)
    return plan


@dataclass
class ToolTrace:
    tool_name: str
    arguments: dict
    result: str
    duration_ms: float = 0.0
    success: bool = True


@dataclass
class AgentTrace:
    plan: Plan | None = None
    tool_traces: list[ToolTrace] = field(default_factory=list)
    retries: int = 0
