"""Load and validate paired sycophancy prompts.

Each record is a factual question asked two ways:
  neutral:  the bare question
  pressured: the same question with a user opinion pushing the wrong answer

A sycophantic model answers correctly on the neutral form but flips
toward the user's stated (wrong) belief on the pressured form.
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PromptPair:
    id: str
    topic: str
    neutral: str
    pressured: str
    correct_answer: str
    pressured_toward: str  # the wrong answer the user pushes


def load_pairs(path: str | Path) -> list[PromptPair]:
    pairs = []
    with open(path) as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            missing = {f for f in PromptPair.__dataclass_fields__} - raw.keys()
            if missing:
                raise ValueError(f"line {line_no}: missing fields {sorted(missing)}")
            pairs.append(PromptPair(**{k: raw[k] for k in PromptPair.__dataclass_fields__}))
    ids = [p.id for p in pairs]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate pair ids in dataset")
    return pairs
