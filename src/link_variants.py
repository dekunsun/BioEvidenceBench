"""Exploratory: is the linking loss a property of linking, or of our deliberately naive linker?
(DEVIATIONS.md; decided after the test pages were unsealed.)

    python src/link_variants.py [--no-llm]

Same Butler test links, same arms as src/link_taxa.py (the gold mention text, and Opus G1 on
the expert, modern-OCR and legacy-OCR text), four linkers:
  printed    the pre-registered plain lookup: GBIF species/match, name only
  expanded   printed, after expanding an abbreviated genus from earlier names on the page
  hinted     GBIF match told the name is an animal; an abbreviated genus expanded from the page
             AND the previous page; when GBIF gives a higher rank or a homonym, the single
             accepted bird record with that exact name at the rank the name's form implies is
             taken (the same rule src/expand_links.py uses for the gold keys)
  llm        Claude (Opus 5.5) reads the printed name, the text around it and the end of the
             previous page, and returns the name it believes is currently accepted (or abstains);
             that name is then looked up as in `hinted`. Context comes from the same text
             version the name was extracted from, so OCR damage is not cleaned up for it.
The linkers never see gold columns (printed_rank, keys): the rank they expect comes from the
form of the name. Scored with link_taxa.outcome / summarise.
Writes results/linking_variants/.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone

import pandas as pd
import requests

import link_taxa as lt
from common import DATA, ROOT, TEXT
from score import char_map, load_gold, map_span, page_text, score_run_detail

OUT = ROOT / "results" / "linking_variants"
RUN = "20261119-2052_claude-opus-5-5_test_batch"
VERSIONS = ["expert", "modern_dots-mocr", "legacy"]
MODEL, PRICES = "claude-opus-5-5", (4.0, 20.0)       # USD per MTok in / out (run_extraction.PRICES)
BOOK_TITLE = "Butler, Birds of Great Britain and Ireland, vol. 2 (1907)"

LLM_SYSTEM = """You link taxon names printed in a historical natural-history book to the name in current use.
You get the name exactly as it was read from the page (it may contain OCR errors or be abbreviated),
the text around it and the end of the previous page, read the same way.
Return the scientific name that the printed name refers to as it is accepted today, at the rank
printed (a species name stays a species, a genus a genus, a family a family). If the printed name
is an old synonym, give the currently accepted name. If the genus is abbreviated, work out the genus
from the context. If you cannot tell which taxon is meant, abstain: a wrong name is worse than none."""

LLM_SCHEMA = {"type": "object", "additionalProperties": False,
              "properties": {"accepted_name": {"type": ["string", "null"]},
                             "rank": {"type": "string", "enum": ["species", "subspecies", "genus", "subfamily",
                                                                 "family", "unknown"]},
                             "abstain": {"type": "boolean"},
                             "note": {"type": "string"}},
              "required": ["accepted_name", "rank", "abstain", "note"]}


# ---------------------------------------------------------------- helpers
def form_rank(name: str) -> str:
    """The rank a name's form implies; never uses the gold."""
    w = lt.clean_name(name).split()
    if len(w) >= 2:
        return "species"
    if w and re.search(r"(idae|inae)$", w[0].lower()):
        return "family" if w[0].lower().endswith("idae") else "subfamily"
    return "genus"


_pages = pd.read_csv(DATA / "gt_pages.csv")
_seq = {(r.BarCode, r.SequenceOrder): r.PageID for r in _pages.itertuples()}
_prev = {r.PageID: _seq.get((r.BarCode, r.SequenceOrder - 1)) for r in _pages.itertuples()}


def version_text(version: str, page_id) -> str:
    if page_id is None:
        return ""
    try:
        return page_text(version, int(page_id))
    except FileNotFoundError:
        p = TEXT / version / f"{int(page_id)}.txt"
        return p.read_text(encoding="utf-8") if p.exists() else ""


def context(version: str, page_id: int, start: int, end: int, width: int = 400) -> tuple[str, str]:
    """(text around the mention's place in this version, end of the previous page in this version)."""
    expert, txt = page_text("expert", page_id), version_text(version, page_id)
    span = map_span(char_map(expert, txt), start, end) or (0, 0)
    around = txt[max(0, span[0] - width):span[1] + width]
    return around, version_text(version, _prev.get(page_id))[-1200:]


def expand_with_previous(name: str, earlier: list[str], prev_text: str) -> str:
    out, did = lt.expand_abbreviation(name, earlier)
    if did:
        return out
    words = re.findall(r"\b[A-Z][a-z]{2,}\s+[a-z]{3,}", prev_text)
    return lt.expand_abbreviation(name, words)[0]


class Cache:
    def __init__(self, path):
        self.path = path
        self.rows = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                self.rows[r["key"]] = r["value"]

    def get(self, key, make):
        if key not in self.rows:
            self.rows[key] = make()
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"key": key, "value": self.rows[key],
                                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                                   ensure_ascii=False) + "\n")
        return self.rows[key]


def gbif_hinted(name: str, rank: str, cache: Cache) -> dict:
    if not name:
        return {"matchType": "NONE"}
    r = cache.get(f"{name}|{rank}", lambda: requests.get(
        lt.GBIF_MATCH, params={"name": name, "kingdom": "Animalia", "verbose": "true"}, timeout=30,
        headers={"User-Agent": "bioevidencebench-linking-eval"}).json())
    if (r.get("rank") or "").lower() == rank and r.get("class") == "Aves":
        return r
    cands = [a for a in [r] + r.get("alternatives", [])
             if (a.get("canonicalName") or "").lower() == name.lower() and (a.get("rank") or "").lower() == rank
             and a.get("class") == "Aves" and a.get("status") in ("ACCEPTED", "SYNONYM", "HOMOTYPIC_SYNONYM",
                                                                  "HETEROTYPIC_SYNONYM")]
    acc = [a for a in cands if a.get("status") == "ACCEPTED"]
    pick = acc if len(acc) == 1 else cands if len(cands) == 1 else []
    return pick[0] if pick else r


def llm_link(client, name: str, around: str, prev: str, cache: Cache, spend: list) -> dict:
    user = (f"Book: {BOOK_TITLE}\n\nPrinted name (as read): {name}\n\n<previous_page_end>\n{prev}\n"
            f"</previous_page_end>\n\n<text_around_the_name>\n{around}\n</text_around_the_name>")

    def call():
        m = client.messages.create(model=MODEL, max_tokens=4000, system=LLM_SYSTEM,
                                   messages=[{"role": "user", "content": user}],
                                   output_config={"effort": "medium",
                                                  "format": {"type": "json_schema", "schema": LLM_SCHEMA}})
        text = "".join(b.text for b in m.content if b.type == "text")
        u = m.usage
        return {"answer": json.loads(text), "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                "stop_reason": m.stop_reason, "model": m.model}
    key = json.dumps([name, around, prev], ensure_ascii=False)
    fresh = key not in cache.rows
    v = cache.get(key, call)
    if fresh:
        spend.append((v["input_tokens"] * PRICES[0] + v["output_tokens"] * PRICES[1]) / 1e6)
    return v["answer"]


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--max-usd", type=float, default=5.0)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    links = lt.load_links(ROOT / "gold" / "gold_links_gloria.csv")
    split = pd.read_csv(DATA / "sample_split.csv").query("split == 'test' and book == 'Butler'")
    links = links[links.page_id.isin(set(split.PageID))]
    gold_path = ROOT / "gold" / "gold_mentions_gloria_test.csv"
    gold = load_gold(gold_path)
    d = score_run_detail(RUN, gold_path, "test")
    go, po = d["gold_outcomes"], d["pred_outcomes"]
    run = lt.run_arm(links, go[(go.condition == "G1") & go.version.isin(VERSIONS)],
                     po[(po.condition == "G1") & po.version.isin(VERSIONS)])
    arms = pd.concat([lt.gold_arm(links, gold), run], ignore_index=True)

    plain = lt.GbifCache(ROOT / "results" / "linking_test" / "gbif_responses.jsonl")
    hint_cache, llm_cache = Cache(OUT / "gbif_hinted.jsonl"), Cache(OUT / "llm_calls.jsonl")
    client, spend = None, []
    if not a.no_llm:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["EVAL_ANTHROPIC_API_KEY"], max_retries=4)

    out = []
    for r in arms.to_dict("records"):
        base = {k: v for k, v in r.items() if k != "earlier"}
        status, rank_p, key = r["resolution_status"], r["printed_rank"], r["accepted_usage_key"]
        if not r["extracted"]:
            for lk in ("printed", "expanded", "hinted", "llm"):
                out.append(base | {"linker": lk, "query": "", "outcome": lt.outcome(status, rank_p, key, None)})
            continue
        around, prev = context(r["version"], r["page_id"], r["start"], r["end"])
        printed = lt.clean_name(r["name"])
        expanded, _ = lt.expand_abbreviation(r["name"], r["earlier"])
        hinted_q = expand_with_previous(r["name"], r["earlier"], prev)
        preds = {"printed": (printed, lt.summarise_response(plain.match(printed))),
                 "expanded": (expanded, lt.summarise_response(plain.match(expanded))),
                 "hinted": (hinted_q, lt.summarise_response(gbif_hinted(hinted_q, form_rank(hinted_q), hint_cache)))}
        if client is not None:
            if sum(spend) > a.max_usd:
                raise SystemExit(f"Spend cap ${a.max_usd} reached.")
            ans = llm_link(client, r["name"], around, prev, llm_cache, spend)
            q = (ans.get("accepted_name") or "").strip() if not ans.get("abstain") else ""
            rk = ans.get("rank") if ans.get("rank") not in (None, "unknown") else form_rank(q)
            preds["llm"] = (q, lt.summarise_response(gbif_hinted(q, rk, hint_cache)) if q
                            else lt.summarise_response({"matchType": "NONE"}))
            base = base | {"llm_answer": json.dumps(ans, ensure_ascii=False)}
        for lk, (q, pred) in preds.items():
            out.append(base | {"linker": lk, "query": q, "name_form": lt.name_form(r["text"]),
                               "outcome": lt.outcome(status, rank_p, key, pred)} | pred)
    scored = pd.DataFrame(out)
    summary = lt.summarise(scored, ["run", "version", "linker"])
    scored.to_csv(OUT / "outcomes.csv", index=False)
    summary.to_csv(OUT / "summary.csv", index=False)
    cols = ["run", "version", "linker", "gold_resolved", "correct", "wrong_taxon", "partial_only", "no_link",
            "not_extracted", "overclaim", "correct_abstain", "link_recall", "link_recall_lo", "link_recall_hi",
            "link_precision", "lost_at_linking", "lost_before_linking"]
    lines = ["# Linker variants on Butler's test links (exploratory)", "",
             "Decided after the test pages were unsealed (DEVIATIONS.md). Same links and arms as "
             "`results/linking_test/`; `printed` and `expanded` reproduce it. Subfamily names are not scored.", "",
             summary[cols].to_markdown(index=False), "",
             f"New LLM spend this run: ${sum(spend):.3f} (cached calls cost nothing again)."]
    (OUT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "config.json").write_text(json.dumps({
        "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "run": RUN, "versions": VERSIONS,
        "llm_model": MODEL, "llm_effort": "medium", "llm_system": LLM_SYSTEM, "llm_schema": LLM_SCHEMA,
        "gbif_hinted_params": "name, kingdom=Animalia, verbose=true; single accepted Aves record at the form's rank",
        "new_llm_usd": round(sum(spend), 4)}, indent=2), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
