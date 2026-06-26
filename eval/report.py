"""Render eval results as a simple metrics table."""

from __future__ import annotations


def print_report(results: list) -> None:
    total = len(results)
    tool_correct = sum(1 for r in results if r.tool_call_correct)
    avg_keyword_score = sum(r.keyword_score for r in results) / total if total else 0.0

    print(f"{'id':<14} {'tool_ok':<8} {'keywords':<10} {'tool_calls'}")
    for r in results:
        kw = f"{r.keyword_hits}/{r.keyword_total}" if r.keyword_total else "n/a"
        print(f"{r.id:<14} {str(r.tool_call_correct):<8} {kw:<10} {r.tool_calls}")

    print()
    print(f"Tool-call correctness: {tool_correct}/{total} ({tool_correct / total:.0%})")
    print(f"Avg keyword coverage:  {avg_keyword_score:.0%}")
