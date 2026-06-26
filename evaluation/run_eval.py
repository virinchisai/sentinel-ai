"""Run the eval dataset through the live agent and score the results.

Usage:
    python -m evaluation.run_eval

Requires a configured LLM provider (ANTHROPIC_API_KEY or OPENAI_API_KEY in .env)
since this exercises the real agent loop, not a mock.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from backend.agents.orchestrator import Orchestrator

DATASET_PATH = Path(__file__).parent / "dataset.jsonl"
RESULTS_PATH = Path(__file__).parent / "results" / "latest.json"


@dataclass
class CaseResult:
    id: str
    prompt: str
    reply: str
    tool_calls: list[str]
    expected_tool: str
    tool_call_correct: bool
    keyword_hits: int
    keyword_total: int
    keyword_score: float


def load_dataset() -> list[dict]:
    cases = []
    with DATASET_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def score_keywords(reply: str, keywords: list[str]) -> tuple[int, int]:
    if not keywords:
        return 0, 0
    reply_lower = reply.lower()
    hits = sum(1 for kw in keywords if kw.lower() in reply_lower)
    return hits, len(keywords)


async def run_all() -> list[CaseResult]:
    orchestrator = Orchestrator()
    results = []
    for case in load_dataset():
        agent_result = await orchestrator.run(f"eval-{case['id']}", case["prompt"])
        hits, total = score_keywords(agent_result.text, case.get("expected_keywords", []))
        tool_call_correct = case["expected_tool"] in agent_result.tool_calls
        results.append(
            CaseResult(
                id=case["id"],
                prompt=case["prompt"],
                reply=agent_result.text,
                tool_calls=agent_result.tool_calls,
                expected_tool=case["expected_tool"],
                tool_call_correct=tool_call_correct,
                keyword_hits=hits,
                keyword_total=total,
                keyword_score=(hits / total) if total else 1.0,
            )
        )
    return results


def main() -> None:
    results = asyncio.run(run_all())

    RESULTS_PATH.parent.mkdir(exist_ok=True)
    RESULTS_PATH.write_text(json.dumps([asdict(r) for r in results], indent=2))

    from evaluation.report import print_report

    print_report(results)


if __name__ == "__main__":
    main()
