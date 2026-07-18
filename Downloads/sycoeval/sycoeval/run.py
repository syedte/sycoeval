"""Run the sycophancy eval end to end.

Usage:
    python -m sycoeval.run --dataset data/pairs.jsonl --model claude-haiku-4-5
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .client import AnthropicClient
from .dataset import load_pairs
from .grade import PairResult, grade_answer, summarize


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="data/pairs.jsonl")
    ap.add_argument("--model", default="claude-haiku-4-5")
    ap.add_argument("--judge-model", default="claude-haiku-4-5")
    ap.add_argument("--out", default="results")
    ap.add_argument("--limit", type=int, default=None, help="run only the first N pairs")
    args = ap.parse_args()

    pairs = load_pairs(args.dataset)
    if args.limit:
        pairs = pairs[: args.limit]

    subject = AnthropicClient(model=args.model)
    judge = AnthropicClient(model=args.judge_model, max_tokens=10)

    results, transcript = [], []
    for i, pair in enumerate(pairs, 1):
        neutral_ans = subject.complete(pair.neutral)
        pressured_ans = subject.complete(pair.pressured)
        ng = grade_answer(judge, pair.neutral, pair.correct_answer, neutral_ans)
        pg = grade_answer(judge, pair.neutral, pair.correct_answer, pressured_ans)
        results.append(PairResult(pair.id, pair.topic, ng, pg))
        transcript.append({
            "id": pair.id, "topic": pair.topic,
            "neutral_answer": neutral_ans, "pressured_answer": pressured_ans,
            "neutral_grade": ng, "pressured_grade": pg,
        })
        print(f"[{i}/{len(pairs)}] {pair.id}: neutral={ng} pressured={pg}"
              + ("  << FLIP" if results[-1].flipped else ""))

    summary = summarize(results)
    summary["model"] = args.model
    summary["judge_model"] = args.judge_model
    summary["timestamp"] = datetime.now(timezone.utc).isoformat()

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (out / f"summary_{stamp}.json").write_text(json.dumps(summary, indent=2))
    (out / f"transcript_{stamp}.json").write_text(json.dumps(transcript, indent=2))

    print("\n=== Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
