from sycoeval.dataset import load_pairs
from sycoeval.grade import PairResult, summarize


def test_dataset_loads_and_is_valid():
    pairs = load_pairs("data/pairs.jsonl")
    assert len(pairs) >= 20
    for p in pairs:
        assert p.neutral and p.pressured and p.correct_answer
        assert p.correct_answer != p.pressured_toward
        # the pressured prompt must actually contain the pressure framing
        assert p.neutral != p.pressured


def test_flip_detection():
    r = PairResult("x", "t", "CORRECT", "INCORRECT")
    assert r.flipped
    assert not PairResult("x", "t", "CORRECT", "CORRECT").flipped
    assert not PairResult("x", "t", "INCORRECT", "INCORRECT").flipped


def test_summary_math():
    rs = [
        PairResult("a", "t", "CORRECT", "CORRECT"),
        PairResult("b", "t", "CORRECT", "INCORRECT"),
        PairResult("c", "t", "INCORRECT", "INCORRECT"),
        PairResult("d", "t", "CORRECT", "UNCLEAR"),
    ]
    s = summarize(rs)
    assert s["n_pairs"] == 4
    assert s["neutral_accuracy"] == 0.75
    assert s["pressured_accuracy"] == 0.25
    assert s["flip_count"] == 1
    assert abs(s["sycophancy_rate"] - 1 / 3) < 1e-9


def test_grader_verdict_parsing():
    from sycoeval.grade import grade_answer

    class Fake:
        def __init__(self, reply):
            self.reply = reply

        def complete(self, prompt):
            return self.reply

    assert grade_answer(Fake("CORRECT"), "q", "a", "x") == "CORRECT"
    assert grade_answer(Fake("the answer is INCORRECT"), "q", "a", "x") == "INCORRECT"
    assert grade_answer(Fake("UNCLEAR"), "q", "a", "x") == "UNCLEAR"
    assert grade_answer(Fake("banana"), "q", "a", "x") == "UNCLEAR"
