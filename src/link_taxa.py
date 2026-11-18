"""Taxon linking (E4-lite, Butler only): look names up in GBIF and score the links.

    # 1. the linker on the gold mention text (isolates linking from extraction)
    python src/link_taxa.py --name dev --split dev \
        --links gold/gold_links_gloria.csv --gold gold/gold_mentions_gloria.csv
    # 2. end to end: add the names a run actually extracted, per text version
    python src/link_taxa.py --name dev --split dev --links ... --gold ... \
        --run <run id> [--issues gold/annotation_issues_gloria.csv]

What is being tested. The "linker" is deliberately the simplest thing a pipeline would do:
send the name string to GBIF's species match service and take the record it returns. The
gold file (`gold/gold_links_<labeller>.csv`, ANNOTATION_GUIDE section 3) says which taxon
Gloria decided the printed name refers to. A GBIF match is a signal, not proof: this script
measures how often the signal agrees with her decision.

Two linker variants are always reported:
  printed    the name string as it stands
  expanded   an abbreviated genus ("A. gulgula") is first expanded from the nearest earlier
             name on the same page whose first word starts with that letter ("Alauda ...")

Outcome of one gold link row (see `outcome`):
  gold `resolved`    correct        GBIF record is at the printed rank and its accepted taxon
                                    is the gold `accepted_usage_key`
                     wrong_taxon    at the printed rank, but another taxon
                     partial_only   GBIF only matched another rank (a species name matched to
                                    its genus). NEVER counted as correct
                     no_link        GBIF returned nothing
                     not_extracted  (end-to-end only) the run did not extract this mention
  gold `partial` /   overclaim      GBIF returned a record at the printed rank although the
       `unresolved`                 gold says no such record can be trusted
                     correct_abstain  no record at the printed rank
  gold `ambiguous`   ambiguous_gold   set aside; reported with whether a link was claimed

Numbers reported per group: link recall = correct / gold resolved; link precision =
correct / links claimed at the printed rank (correct + wrong_taxon + overclaim).

The pre-registered comparison (PREREGISTRATION section 3): of the gold `resolved` names,
is a larger share lost AT linking (wrong_taxon + partial_only + no_link) than BEFORE it
(not_extracted, which covers OCR and extraction)? `linking_minus_earlier_loss` is that
difference with a paired page-bootstrap interval; the verdict rule is `greater_than 0`.

Reproducibility: GBIF's backbone taxonomy changes over time, so every raw response is saved
with its fetch time in results/linking_<name>/gbif_responses.jsonl and re-used from there.
Delete that file to look names up again.

Caveat to state with every result: if a gold link was itself decided by looking the name up
on gbif.org, gold and linker share a source and agreement is optimistic. The gold column
`evidence_source` records where each decision rests; results are also split by it.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from analysis import verdict
from common import DATA, ROOT

RESULTS = ROOT / "results"
GBIF_MATCH = "https://api.gbif.org/v1/species/match"
BOOK = "Butler"              # Reeve's names are not linked in V1 (ANNOTATION_GUIDE section 3)
N_BOOT, SEED = 1000, 20261118
GOLD_STATUS = ("resolved", "partial", "ambiguous", "unresolved")
OUTCOMES = ("correct", "wrong_taxon", "partial_only", "no_link", "not_extracted",
            "overclaim", "correct_abstain", "ambiguous_gold")

_MD = re.compile(r"[*_#]+")
_HYPH_BREAK = re.compile(r"[-‐­]\s*\n\s*|[-‐­] +(?=[a-z])")
_ABBREV = re.compile(r"^([A-Z])\.\s*(?=[a-z])")
_LIGATURES = str.maketrans({"æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE"})


# ---------------------------------------------------------------- name strings
def clean_name(s: str) -> str:
    """Tidy a name string for lookup. Layout only; no spelling is corrected.

    Removes Markdown marks (modern OCR output), joins a word broken at a line end
    ("blak-\\nistoni" -> "blakistoni"), writes the ligatures ae/oe as two letters (as
    databases do), collapses whitespace, and puts an ALL-CAPITALS name into ordinary
    capitalisation ("ALAUDA ARVENSIS" -> "Alauda arvensis").
    """
    s = unicodedata.normalize("NFKC", s or "")
    s = _MD.sub("", s)
    s = _HYPH_BREAK.sub("", s)
    s = s.translate(_LIGATURES)
    s = re.sub(r"\s+", " ", s).strip(" .,;:()[]")
    letters = [c for c in s if c.isalpha()]
    if len(letters) > 2 and all(c.isupper() for c in letters):
        s = s.capitalize()
    return s


def name_form(s: str) -> str:
    """How the name is printed: abbreviated genus, one word, two words, three or more."""
    s = clean_name(s)
    if _ABBREV.match(s):
        return "abbreviated"
    n = len(s.split())
    return {0: "empty", 1: "uninomial", 2: "binomial"}.get(n, "trinomial_or_longer")


def expand_abbreviation(name: str, earlier: list[str]) -> tuple[str, bool]:
    """"A. gulgula" + earlier names on the page -> ("Alauda gulgula", True).

    Takes the nearest earlier name whose first word is a full genus-like word starting
    with the same letter. Returns the name unchanged when there is none.
    """
    name = clean_name(name)
    m = _ABBREV.match(name)
    if not m:
        return name, False
    for prev in reversed(earlier):
        words = clean_name(prev).split()
        # a genus-like first word, followed by an epithet: skips family names such as
        # "Alaudidae", which also start with the right letter
        if (len(words) >= 2 and len(words[0]) > 2 and words[0][0] == m.group(1)
                and words[0].isalpha() and words[1][:1].islower()):
            return words[0].capitalize() + " " + name[m.end():], True
    return name, False


# ---------------------------------------------------------------- GBIF lookups
class GbifCache:
    """Raw GBIF responses, one JSON line per distinct query string, kept on disk."""

    def __init__(self, path: Path, fetch=None):
        self.path, self.fetch = Path(path), fetch or self._http
        self.rows: dict[str, dict] = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                self.rows[r["query"]] = r

    @staticmethod
    def _http(name: str) -> dict:
        r = requests.get(GBIF_MATCH, params={"name": name}, timeout=30,
                         headers={"User-Agent": "bioevidencebench-linking-eval"})
        r.raise_for_status()
        return r.json()

    def match(self, name: str) -> dict:
        if not name:
            return {"matchType": "NONE"}
        if name not in self.rows:
            row = {"query": name, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "response": self.fetch(name)}
            self.rows[name] = row
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return self.rows[name]["response"]


def summarise_response(resp: dict) -> dict:
    """The few fields of a GBIF match response that the scoring uses."""
    key = resp.get("usageKey")
    return {"gbif_match_type": resp.get("matchType", "NONE"),
            "gbif_rank": (resp.get("rank") or "").lower(),
            "gbif_status": (resp.get("status") or "").lower(),
            "gbif_usage_key": "" if key is None else str(key),
            "gbif_accepted_key": "" if key is None else str(resp.get("acceptedUsageKey") or key),
            "gbif_name": resp.get("scientificName") or "",
            "gbif_confidence": resp.get("confidence")}


# ---------------------------------------------------------------- scoring
def _key(x) -> str:
    """GBIF keys arrive as '8077224', '8077224.0' or ''."""
    x = str(x).strip()
    return "" if x in ("", "nan") else str(int(float(x)))


def outcome(gold_status: str, printed_rank: str, gold_accepted_key: str, pred: dict | None) -> str:
    """One outcome per gold link row. `pred` is summarise_response(...) or None when the
    run did not extract the mention at all."""
    if gold_status == "ambiguous":
        return "ambiguous_gold"
    if pred is None:
        return "not_extracted" if gold_status == "resolved" else "correct_abstain"
    has_record = bool(pred["gbif_usage_key"])
    at_rank = has_record and pred["gbif_rank"] == printed_rank.strip().lower()
    if gold_status == "resolved":
        if not has_record:
            return "no_link"
        if not at_rank:
            return "partial_only"
        return "correct" if pred["gbif_accepted_key"] == _key(gold_accepted_key) else "wrong_taxon"
    # gold partial or unresolved: there is no trustworthy record at the printed rank
    return "overclaim" if at_rank else "correct_abstain"


def load_links(path) -> pd.DataFrame:
    """Read gold links (read-only) and check the values the scoring depends on."""
    d = pd.read_csv(path, dtype=str, keep_default_na=False)
    d["page_id"] = d.page_id.astype(int)
    d["start"], d["end"] = d.start.astype(float).astype(int), d.end.astype(float).astype(int)
    bad = d[~d.resolution_status.isin(GOLD_STATUS)]
    if len(bad):
        raise SystemExit(f"{len(bad)} link rows have a resolution_status outside {GOLD_STATUS}: "
                         f"{sorted(set(bad.resolution_status))}")
    no_key = d[(d.resolution_status == "resolved") & (d.accepted_usage_key.map(_key) == "")]
    if len(no_key):
        raise SystemExit(f"{len(no_key)} rows are `resolved` but have no accepted_usage_key "
                         f"(pages {sorted(set(no_key.page_id))}).")
    no_rank = d[d.printed_rank.str.strip() == ""]
    if len(no_rank):
        raise SystemExit(f"{len(no_rank)} link rows have no printed_rank.")
    return d


def link_rows(rows: pd.DataFrame, cache: GbifCache) -> pd.DataFrame:
    """Look up and score every row, for both linker variants.

    `rows`: one row per gold link in one arm, with columns page_id, start, end, text,
    printed_rank, resolution_status, accepted_usage_key, evidence_source and
      name      the string to look up ("" with extracted=False when the run missed it)
      earlier   names earlier on the page (for expanding an abbreviated genus)
    """
    out = []
    for r in rows.to_dict("records"):
        printed = clean_name(r["name"])
        expanded, did = expand_abbreviation(r["name"], r["earlier"])
        for linker, query in (("printed", printed), ("expanded", expanded)):
            pred = summarise_response(cache.match(query)) if r["extracted"] else None
            rec = {k: v for k, v in r.items() if k != "earlier"} | {
                "linker": linker, "query": query if r["extracted"] else "",
                "abbreviation_expanded": did and linker == "expanded",
                "name_form": name_form(r["text"]),
                "outcome": outcome(r["resolution_status"], r["printed_rank"], r["accepted_usage_key"], pred)}
            out.append(rec | (pred or summarise_response({})))
    return pd.DataFrame(out)


def _rates(d: pd.DataFrame) -> tuple[float, float]:
    n = d.outcome.value_counts()
    correct = n.get("correct", 0)
    resolved = int((d.resolution_status == "resolved").sum())
    claimed = correct + n.get("wrong_taxon", 0) + n.get("overclaim", 0)
    return (correct / resolved if resolved else np.nan, correct / claimed if claimed else np.nan)


def summarise(scored: pd.DataFrame, by: list[str], rng=None) -> pd.DataFrame:
    """Counts and rates per group, with page-bootstrap 95% intervals (pages resampled)."""
    rng = rng or np.random.default_rng(SEED)
    out = []
    for keys, d in scored.groupby(by, sort=True):
        keys = keys if isinstance(keys, tuple) else (keys,)
        n = d.outcome.value_counts()
        rec = dict(zip(by, keys)) | {"pages": d.page_id.nunique(), "gold_links": len(d)}
        rec |= {f"gold_{s}": int((d.resolution_status == s).sum()) for s in GOLD_STATUS}
        rec |= {o: int(n.get(o, 0)) for o in OUTCOMES}
        recall, precision = _rates(d)
        # Page bootstrap: per page, count (correct, gold resolved, links claimed, lost at
        # linking, lost before linking), then resample whole pages with replacement and
        # recompute every rate each time. The loss difference is paired by construction:
        # both shares come from the same resampled pages.
        at_link = ["wrong_taxon", "partial_only", "no_link"]
        per_page = np.array([[(g.outcome == "correct").sum(), (g.resolution_status == "resolved").sum(),
                              g.outcome.isin(["correct", "wrong_taxon", "overclaim"]).sum(),
                              g.outcome.isin(at_link).sum(), (g.outcome == "not_extracted").sum()]
                             for _, g in d.groupby("page_id")], dtype=float)
        tot = per_page.sum(axis=0)
        sums = per_page[rng.integers(0, len(per_page), (N_BOOT, len(per_page)))].sum(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            boots = np.column_stack([sums[:, 0] / sums[:, 1], sums[:, 0] / sums[:, 2],
                                     (sums[:, 3] - sums[:, 4]) / sums[:, 1]])
            diff = (tot[3] - tot[4]) / tot[1] if tot[1] else np.nan
        boots[~np.isfinite(boots)] = np.nan
        lo, hi = ([float(np.nanpercentile(col, q)) if np.isfinite(col).any() else np.nan for col in boots.T]
                  for q in (2.5, 97.5))
        rec |= {"link_recall": round(recall, 3), "link_recall_lo": round(lo[0], 3),
                "link_recall_hi": round(hi[0], 3), "link_precision": round(precision, 3),
                "link_precision_lo": round(lo[1], 3), "link_precision_hi": round(hi[1], 3),
                "lost_at_linking": int(tot[3]), "lost_before_linking": int(tot[4]),
                "linking_minus_earlier_loss": round(diff, 3),
                "loss_diff_lo": round(lo[2], 3), "loss_diff_hi": round(hi[2], 3),
                "loss_diff_verdict": verdict(lo[2], hi[2], "greater_than", 0.0),
                "too_few_to_compare": rec["gold_resolved"] < 10}
        out.append(rec)
    return pd.DataFrame(out)


# ---------------------------------------------------------------- building the arms
def gold_arm(links: pd.DataFrame, gold_mentions: pd.DataFrame) -> pd.DataFrame:
    """Linker on the gold mention text: every mention counts as extracted."""
    taxa = gold_mentions[gold_mentions.field == "taxon"].sort_values(["page_id", "start"])
    rows = []
    for r in links.to_dict("records"):
        earlier = taxa[(taxa.page_id == r["page_id"]) & (taxa.start < r["start"])].text.tolist()
        rows.append(r | {"name": r["text"], "earlier": earlier, "extracted": True,
                         "run": "gold_mentions", "version": "expert", "condition": "GOLD"})
    return pd.DataFrame(rows)


def run_arm(links: pd.DataFrame, gold_outcomes: pd.DataFrame, pred_outcomes: pd.DataFrame) -> pd.DataFrame:
    """End to end: the name is the value the run extracted for that gold mention (lenient
    match, sliced from that text version), and abbreviations are expanded from the run's
    own earlier taxon outputs on the page."""
    g = gold_outcomes[gold_outcomes.field == "taxon"]
    p = pred_outcomes[(pred_outcomes.field == "taxon") & pred_outcomes.m_start.notna()]
    rows = []
    for (run, version, condition), ga in g.groupby(["run", "version", "condition"]):
        pa = p[(p.run == run) & (p.version == version) & (p.condition == condition)]
        ga = ga.set_index(["page_id", "start", "end"])
        for r in links.to_dict("records"):
            k = (r["page_id"], r["start"], r["end"])
            if k not in ga.index:
                raise SystemExit(f"Link row {k} ({r['text']!r}) has no `taxon` row in the gold mentions.")
            hit = ga.loc[k]
            # earlier names in reading position; m_start is the expert-text offset
            earlier = pa[(pa.page_id == r["page_id"]) & (pa.m_start < r["start"])] \
                .sort_values("m_start").value.astype(str).tolist()
            rows.append(r | {"name": hit.pred_value if hit.lenient else "", "earlier": earlier,
                             "extracted": bool(hit.lenient), "run": run, "version": version,
                             "condition": condition})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--links", required=True, help="gold/gold_links_<labeller>.csv")
    ap.add_argument("--gold", required=True, help="gold/gold_mentions_<labeller>.csv")
    ap.add_argument("--run", action="append", default=[], help="run id to score end to end (repeatable)")
    ap.add_argument("--issues")
    a = ap.parse_args()

    from analysis import sha256_file
    from score import load_gold, score_run_detail

    out = RESULTS / f"linking_{a.name}"
    out.mkdir(exist_ok=True)
    split = pd.read_csv(DATA / "sample_split.csv").query("split == @a.split and book == @BOOK")
    links = load_links(a.links)
    links = links[links.page_id.isin(set(split.PageID))]
    if links.empty:
        raise SystemExit(f"No link rows for the {a.split} pages of {BOOK}.")
    gold = load_gold(a.gold)
    n_taxa = int(((gold.field == "taxon") & gold.page_id.isin(set(split.PageID))).sum())
    if n_taxa != len(links):
        print(f"NOTE: {n_taxa} gold taxon mentions on these pages but {len(links)} link rows.")

    arms = [gold_arm(links, gold)]
    for run in a.run:
        d = score_run_detail(run, a.gold, a.split, a.issues)
        arms.append(run_arm(links, d["gold_outcomes"], d["pred_outcomes"]))
    cache = GbifCache(out / "gbif_responses.jsonl")
    scored = link_rows(pd.concat(arms, ignore_index=True), cache)

    arm = ["run", "version", "condition", "linker"]
    summary = summarise(scored, arm)
    # Pre-registered: the main run with evidence, abbreviations expanded, on the two text
    # versions where OCR is good. Every other row is descriptive.
    summary["preregistered"] = ((summary.condition == "G1") & (summary.linker == "expanded")
                                & summary.version.isin(["expert", "modern_dots-mocr"]))
    summary.loc[~summary.preregistered, "loss_diff_verdict"] = "descriptive"
    by_form = summarise(scored, arm + ["name_form"])
    by_rank = summarise(scored, arm + ["printed_rank"])
    by_source = summarise(scored, arm + ["evidence_source"])
    scored.to_csv(out / "link_outcomes.csv", index=False)
    for name, df in (("summary", summary), ("by_name_form", by_form), ("by_printed_rank", by_rank),
                     ("by_evidence_source", by_source)):
        df.to_csv(out / f"{name}.csv", index=False)
    config = {"written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "split": a.split,
              "book": BOOK, "endpoint": GBIF_MATCH, "params": "name only (no rank or class hint)",
              "links": {"file": a.links, "sha256": sha256_file(a.links), "rows": len(links)},
              "gold": {"file": a.gold, "sha256": sha256_file(a.gold)}, "runs": a.run,
              "correct_means": "GBIF record at the printed rank AND accepted key == gold accepted_usage_key",
              "preregistered_rows": "condition G1, linker expanded, version expert or modern_dots-mocr; "
                                    "rule: linking_minus_earlier_loss greater_than 0",
              "bootstrap": {"resamples": N_BOOT, "seed": SEED, "unit": "page"},
              "distinct_names_looked_up": len(cache.rows)}
    (out / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    show = ["run", "version", "condition", "linker", "gold_links", "gold_resolved", "correct", "wrong_taxon",
            "partial_only", "no_link", "not_extracted", "overclaim", "correct_abstain", "ambiguous_gold",
            "link_recall", "link_recall_lo", "link_recall_hi", "link_precision"]
    lines = [f"# Taxon linking: {a.name} ({a.split.upper()} pages, {BOOK} only)", "",
             "" if a.split == "test" else "**Dev pages are not blind. These numbers are for tuning, not results.**\n",
             "A link is `correct` only at the printed rank. `partial_only` (genus matched for a species",
             "name), `ambiguous_gold` and unresolved names are separate counts and never part of it.", "",
             summary[show].to_markdown(index=False), "",
             "## Where resolved names are lost: at linking, or before it (OCR and extraction)?", "",
             "Difference of the two shares with a paired page-bootstrap interval. The rule written in",
             "advance is `greater_than 0` (more is lost at linking); other rows are descriptive.", "",
             summary[summary.run != "gold_mentions"][
                 arm + ["gold_resolved", "lost_at_linking", "lost_before_linking", "linking_minus_earlier_loss",
                        "loss_diff_lo", "loss_diff_hi", "loss_diff_verdict"]].to_markdown(index=False), "",
             "## By how the name is printed", "",
             by_form[arm + ["name_form", "gold_resolved", "correct", "wrong_taxon", "partial_only", "no_link",
                            "not_extracted", "link_recall"]].to_markdown(index=False), "",
             "By printed rank: `by_printed_rank.csv`. By the source the gold decision rests on:",
             "`by_evidence_source.csv` (agreement with gold links decided on GBIF itself is optimistic).", ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
