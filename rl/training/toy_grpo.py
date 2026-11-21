"""Module 7a: a toy GRPO in numpy, small enough to check by hand (plan section 7a). $0, CPU, seconds.

    python rl/training/toy_grpo.py          # runs the experiments, writes figures/ and results.json

The task is task B in miniature. A "line" has L words; d of them are damaged in the OCR (some
"hard", standing for damaged scientific-name words, the rest "easy"); the other L - d are correct.
For each word the policy emits one token, an action:
    0 KEEP  (copy the OCR word)    1 FIX  (write the right word)    2 OTHER (write some other word)
On a correct word KEEP and FIX both leave it right and OTHER breaks it; on a damaged word only FIX
repairs it. The reward is Reward v1.2's formula: weighted repaired / weighted damaged - 0.5 * broken (hard words weigh 3; clean
line: 1 - 0.5 * broken), clipped to [-1, 1]. Line lengths and damage counts are drawn from the real
task B dev units (`data/cache/taskb/units/dev.jsonl`), hard = damaged name words.

The policy is a 3 x 3 table of logits theta[state, action], state = clean / easy / hard. With a
softmax policy the gradient of log pi(a | s) is (onehot(a) - pi(.|s)) / T, so every term of the
GRPO update below is written out by hand: no autograd, nothing hidden.

This is a teaching model, not a stand-in for a language model: its "tokens" are independent given
the state, there is no prompt understanding and no shared representation. It shows how GRPO turns
rewards into updates, not how a 0.6B model will learn.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KEEP, FIX, OTHER = 0, 1, 2
CLEAN, EASY, HARD = 0, 1, 2
# Starting policy: copies a lot, fixes easy damage sometimes, rarely fixes names.
THETA0 = np.array([[2.0, 0.0, -2.5],      # clean word: mostly KEEP
                   [0.8, 0.3, -1.0],      # easy damage
                   [0.8, -1.5, -0.3]])    # hard damage (names)


def load_items(path=ROOT / "data/cache/taskb/units/dev.jsonl", seed=0):
    """(n_words, n_easy, n_hard) for every dev unit; synthetic fallback if the cache is absent."""
    if path.exists():
        rows = [json.loads(line) for line in path.open(encoding="utf-8")]
        return [(r["n_words"], r["n_damaged"] - r["n_name_damaged"], r["n_name_damaged"]) for r in rows]
    rng = np.random.default_rng(seed)
    return [(int(n), int(d), 0) for n, d in zip(rng.integers(3, 16, 3000), rng.integers(0, 4, 3000))]


def states_of(item):
    n, e, h = item
    return np.array([CLEAN] * (n - e - h) + [EASY] * e + [HARD] * h)


NAME_WEIGHT = 3.0          # as in Reward v1.2: a damaged name word counts three times


def reward(states, actions):
    w = np.where(states == HARD, NAME_WEIGHT, 1.0)
    dmg = states != CLEAN
    repaired = (w * (dmg & (actions == FIX))).sum()
    broken = ((states == CLEAN) & (actions == OTHER)).sum()
    base = repaired / w[dmg].sum() if dmg.any() else 1.0
    return float(np.clip(base - 0.5 * broken, -1, 1))


def probs(theta, T=1.0):
    z = theta / T
    z = z - z.max(axis=1, keepdims=True)
    p = np.exp(z)
    return p / p.sum(axis=1, keepdims=True)


def sample(p, s, rng):
    """One completion: an action for every word, drawn from pi(. | state of that word)."""
    c = p[s].cumsum(axis=1)
    return (rng.random(len(s))[:, None] > c[:, :-1]).sum(axis=1)


# ------------------------------------------------------------------ the GRPO step (the core)
def grpo_step(theta, theta_ref, batch, rng, G=8, T=1.0, lr=0.5, eps=0.2, beta=0.0, epochs=2,
              scale_std=True, loss="grpo", filter_zero_std=False, reward_scale=1.0):
    """One GRPO update. `batch` is a list of items (prompts). Returns new theta and diagnostics.

    1. sample G completions per prompt from the old policy
    2. reward each; advantage = (r - group mean) [/ group std]: every token of a completion
       shares its completion's advantage
    3. for `epochs` passes: ratio rho = pi_theta(a) / pi_old(a) per token; clipped surrogate
       min(rho A, clip(rho, 1-eps, 1+eps) A); optional KL to the reference policy (k3 estimator)
    4. aggregate token terms: "grpo" mean over a completion's tokens, then over completions;
       "dapo" sum over all tokens / number of tokens; "dr_grpo" sum / (G * max length)
    """
    p_old = probs(theta, T)
    groups, zero_std = [], 0
    for item in batch:
        s = states_of(item)
        comp = [sample(p_old, s, rng) for _ in range(G)]
        r = np.array([reward(s, a) for a in comp]) * reward_scale
        if r.std() < 1e-9:
            zero_std += 1
            if filter_zero_std:                    # DAPO's dynamic sampling: the group carries no signal
                continue
        adv = r - r.mean()
        if scale_std:
            adv = adv / (r.std() + 1e-6)
        groups.append((s, comp, adv))
    n_tok = sum(len(s) * G for s, _, _ in groups) or 1
    l_max = max((len(s) for s, _, _ in groups), default=1)
    p_ref = probs(theta_ref, T)
    for _ in range(epochs):
        p = probs(theta, T)
        grad = np.zeros_like(theta)
        for s, comp, adv in groups:
            for a, A in zip(comp, adv):
                w = {"grpo": 1 / (len(groups) * G * len(s)), "dapo": 1 / n_tok,
                     "dr_grpo": 1 / (len(groups) * G * l_max)}[loss]
                rho = p[s, a] / p_old[s, a]
                clipped = (A > 0) & (rho > 1 + eps) | (A < 0) & (rho < 1 - eps)
                coef = np.where(clipped, 0.0, rho * A)                    # d surrogate / d log pi
                coef = coef - beta * (1 - p_ref[s, a] / p[s, a])          # d (-beta * k3) / d log pi
                for x, act, c in zip(s, a, coef):
                    grad[x] += w * c * ((np.arange(3) == act) - p[x]) / T  # chain rule through softmax
        theta = theta + lr * grad                                          # gradient ascent
    kl = float((p_ref * np.log(p_ref / probs(theta, T))).sum(axis=1).mean())
    return theta, {"frac_reward_zero_std": zero_std / len(batch), "kl_to_ref": kl}


# ------------------------------------------------------------------ evaluation and experiments
def evaluate(theta, items, rng, n=400, T=1.0):
    p = probs(theta, T)
    idx = rng.choice(len(items), min(n, len(items)), replace=False)
    rs = [reward(states_of(items[i]), sample(p, states_of(items[i]), rng)) for i in idx]
    return {"mean_reward": float(np.mean(rs)), "p_fix_easy": float(p[EASY, FIX]),
            "p_fix_hard": float(p[HARD, FIX]), "p_break_clean": float(p[CLEAN, OTHER])}


def train(items, steps=60, batch=16, seed=0, sample_from=None, **kw):
    """`sample_from`: the items batches are drawn from (default: all); evaluation is always on all."""
    rng = np.random.default_rng(seed)
    theta, hist = THETA0.copy(), []
    pool = sample_from or items
    for t in range(steps):
        b = [pool[i] for i in rng.choice(len(pool), batch, replace=False)]
        theta, diag = grpo_step(theta, THETA0, b, rng, **kw)
        hist.append({"step": t, **diag, **evaluate(theta, items, rng, n=200, T=kw.get("T", 1.0))})
    return theta, hist


def zero_std_at_start(items, Gs=(2, 4, 8, 16), Ts=(0.5, 1.0, 1.5), n=600, seed=1):
    rng = np.random.default_rng(seed)
    out = {}
    for T in Ts:
        p = probs(THETA0, T)
        for G in Gs:
            z = 0
            for i in rng.choice(len(items), n, replace=False):
                s = states_of(items[i])
                r = [reward(s, sample(p, s, rng)) for _ in range(G)]
                z += np.std(r) < 1e-9
            out[f"T={T},G={G}"] = z / n
    return out


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    items = load_items()
    fig_dir = HERE / "figures"
    fig_dir.mkdir(exist_ok=True)
    res = {"n_items": len(items), "theta0": THETA0.tolist()}

    # E1: how many groups carry no signal before training, by group size and temperature
    res["E1_zero_std_at_start"] = zero_std_at_start(items)

    # E2: training curves under the variants the notes discuss (3 seeds each)
    variants = {"GRPO (std scaling, beta 0)": {}, "no std scaling (Dr. GRPO style)": {"scale_std": False},
                "KL beta 0.5": {"beta": 0.5}, "filter zero-std groups (DAPO style)": {"filter_zero_std": True},
                "G = 2": {"G": 2}}
    curves = {}
    for name, kw in variants.items():
        runs = [train(items, seed=s, **kw)[1] for s in range(3)]
        curves[name] = runs
        res.setdefault("E2_final", {})[name] = {k: float(np.mean([r[-1][k] for r in runs]))
                                                 for k in ("mean_reward", "p_fix_easy", "p_fix_hard",
                                                           "p_break_clean", "kl_to_ref", "frac_reward_zero_std")}
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    for name, runs in curves.items():
        for k, a in zip(("mean_reward", "frac_reward_zero_std", "p_fix_hard"), ax):
            a.plot(np.mean([[h[k] for h in r] for r in runs], axis=0), label=name)
            a.set_title(k)
    ax[0].set_xlabel("step")
    ax[2].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(fig_dir / "toy_grpo_curves.png", dpi=120)

    # E3: weight each token gets under the three loss aggregations, by completion length
    L = np.arange(1, 41)
    G, lmax = 8, 40
    res["E3_token_weight"] = {"grpo (per completion mean)": (1 / (G * L)).tolist(),
                              "dapo (per token, batch of equal lengths)": [1 / (G * l) for l in L],
                              "dr_grpo (constant G*Lmax)": [1 / (G * lmax)] * len(L)}
    # the length effect shows in a mixed batch: one short and one long completion with the same advantage
    short, long_ = 5, 40
    res["E3_mixed_batch"] = {
        "grpo: weight per token short vs long": [1 / (2 * short), 1 / (2 * long_)],
        "dapo: weight per token short vs long": [1 / (short + long_)] * 2,
        "dr_grpo: weight per token short vs long": [1 / (2 * long_)] * 2}

    # E4: reward scale. With std scaling a 10x reward gives the same update; without, a 10x step.
    rng = np.random.default_rng(5)
    b = [items[i] for i in rng.choice(len(items), 16, replace=False)]
    out = {}
    for scale_std in (True, False):
        th = [grpo_step(THETA0.copy(), THETA0, b, np.random.default_rng(7), scale_std=scale_std,
                        reward_scale=s, epochs=1)[0] for s in (1.0, 10.0)]
        out[f"scale_std={scale_std}"] = float(np.abs(th[1] - THETA0).sum() / np.abs(th[0] - THETA0).sum())
    res["E4_update_ratio_reward_x10"] = out

    # E5: data selection. Damaged names are rare (lines with one: share below); oversampling those
    # lines to half of each batch is compared with drawing batches as the data come.
    hard = [it for it in items if it[2] > 0]
    res["E5_share_lines_with_damaged_name"] = len(hard) / len(items)
    rest = [it for it in items if it[2] == 0]
    mixed = hard * max(1, len(rest) // len(hard)) + rest            # about half the pool has a name
    e5 = {}
    for name, pool in (("as the data come", None), ("half of the pool has a damaged name", mixed)):
        runs = [train(items, seed=s, sample_from=pool)[1] for s in range(3)]
        e5[name] = {k: float(np.mean([r[-1][k] for r in runs])) for k in ("mean_reward", "p_fix_easy", "p_fix_hard")}
    res["E5_data_selection"] = e5

    (HERE / "results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k != "E3_token_weight"}, indent=2))


if __name__ == "__main__":
    main()
