"""Module 7b stage 3: data mix, seed-specific block order, checkpoint rule, primary metrics (CPU)."""
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rl" / "training"))
import common_7b as C  # noqa: E402
import stage3_p0 as S  # noqa: E402


def kind(u):
    return "name" if u["n_name_damaged"] > 0 else "clean" if u["n_damaged"] == 0 else "other"


def test_blocks_keep_the_mix_in_every_seed():
    a, b = S.train_items(1), S.train_items(2)
    assert sorted(x["item_id"] for x in a) == sorted(x["item_id"] for x in b)
    assert [x["item_id"] for x in a] != [x["item_id"] for x in b]
    for items in (a, b):
        for i in range(0, len(items), S.BLOCK):
            assert collections.Counter(kind(u) for u in items[i:i + S.BLOCK]) == {"name": 8, "clean": 3, "other": 5}


def ev(rep, pres):
    return {"p0_dev_eval": {"repair_rate_post": rep, "preservation_post": pres}}


def test_choose_rule():
    base = ev(0.05, 0.90)
    assert S.choose({50: ev(0.1, 0.95), 100: ev(0.3, 0.89), 150: ev(0.4, 0.88)}, base)["step"] == 100
    assert S.choose({50: ev(0.3, 0.95), 100: ev(0.3, 0.95)}, base)["step"] == 50          # tie: earlier
    r = S.choose({50: ev(0.5, 0.70), 100: ev(0.2, 0.80)}, base)
    assert r == {"step": 100, "flag": "no_checkpoint_qualified", "preservation_floor": 0.89}


def test_copy_and_oracle_metrics():
    items = C.load_items(S.DATA / "p0_dev_eval.jsonl")
    for answer, rep in (("input", 0.0), ("target", 1.0)):
        rows = [dict(item_id=i["item_id"], **C.score_answer(i, i[answer])) for i in items]
        m = C.primary_metrics(items, rows)
        assert m["repair_rate"] == rep and m["preservation"] == 1.0 and m["format_failure"] == 0.0


def test_gated_answer_keeps_nothing():
    it = C.load_items(S.DATA / "p0_dev_names.jsonl")[0]
    s = C.score_answer(it, "Corrected line: " + it["target"])
    assert s["gated"] and s["preserved"] == 0 and not s["gated_post"] and s["repaired_post"] == it["n_damaged"]


def test_reward_cer_ablation():
    it = C.load_items(S.DATA / "p0_dev_names.jsonl")[0]
    assert S.reward_cer(it, it["target"]) == 1.0 and S.reward_cer(it, "") == 0.0
    assert 0 < S.reward_cer(it, it["input"]) < 1
