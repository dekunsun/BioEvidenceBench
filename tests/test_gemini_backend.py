"""Gemini record conversion, with fake responses (no API call)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import gemini_backend as gb  # noqa: E402
from locate import locate_all  # noqa: E402
from prompts import SCHEMA_G1, SYSTEM  # noqa: E402

REQ = {"custom_id": "123__expert__G1", "page_id": 123, "split": "dev",
       "version": "expert", "condition": "G1"}
RECORD_KEYS = {"custom_id", "page_id", "split", "version", "condition", "model", "stop_reason",
               "usage", "cost_usd", "parsed", "raw", "error", "received_at", "schema_deviation"}


class FakeResponse:
    """Stands in for google.genai.types.GenerateContentResponse."""

    def __init__(self, d):
        self.d = d

    def model_dump(self, mode="json", exclude_none=True):
        return self.d


def fake(text, finish="STOP", thought_text="I should look at line 1."):
    return FakeResponse({
        "candidates": [{"content": {"role": "model", "parts": [
            {"text": thought_text, "thought": True},   # thought parts must not be parsed
            {"text": text}]}, "finish_reason": finish}],
        "usage_metadata": {"prompt_token_count": 1000, "cached_content_token_count": 200,
                           "candidates_token_count": 100, "thoughts_token_count": 400,
                           "total_token_count": 1500},
        "model_version": "gemini-4-carbon-001"})


def test_record_has_same_shape_as_anthropic_records():
    rec = gb.record_from_response(REQ, fake('{"mentions": [{"field": "locality", "line": 1, "quote": "Cuba"}]}'),
                                  "gemini-4-carbon", batch=False)
    assert set(rec) == RECORD_KEYS
    assert rec["stop_reason"] == "STOP" and rec["error"] is None
    assert rec["parsed"] == {"mentions": [{"field": "locality", "line": 1, "quote": "Cuba"}]}
    assert rec["model"] == "gemini-4-carbon-001"
    # the record feeds locate.py unchanged
    out = locate_all("Hab. Cuba.", rec["condition"], rec["parsed"]["mentions"])
    assert out[0]["status"] == "exact" and out[0]["value"] == "Cuba"


def test_usage_normalised_and_cost_counts_thinking():
    rec = gb.record_from_response(REQ, fake('{"mentions": []}'), "gemini-4-carbon", batch=False)
    u = rec["usage"]
    assert (u["input_tokens"], u["cache_read_input_tokens"], u["output_tokens"]) == (800, 200, 500)
    assert u["thoughts_token_count"] == 400
    # 800 x $2 + 200 x $0.10 + (100 + 400) x $10, per 1M tokens
    assert abs(rec["cost_usd"] - (800 * 2 + 200 * 0.10 + 500 * 10) / 1e6) < 1e-12
    batch = gb.record_from_response(REQ, fake('{"mentions": []}'), "gemini-4-carbon", batch=True)
    assert abs(batch["cost_usd"] - rec["cost_usd"] / 2) < 1e-12


def test_truncated_or_unparseable_json_gives_parsed_none():
    rec = gb.record_from_response(REQ, fake('{"mentions": [{"field": "ta', finish="MAX_TOKENS"),
                                  "gemini-4-carbon", batch=False)
    assert rec["parsed"] is None and rec["stop_reason"] == "MAX_TOKENS"


def test_blocked_prompt_has_no_candidates():
    rec = gb.record_from_response(REQ, {"prompt_feedback": {"block_reason": "OTHER"},
                                        "usage_metadata": {"prompt_token_count": 10}},
                                  "gemini-4-carbon", batch=False)
    assert rec["parsed"] is None and rec["stop_reason"] == "PROMPT_BLOCKED:OTHER"


def test_params_use_our_prompt_and_schema_unchanged():
    p = gb.build_params(SYSTEM, "L1| Hab. Cuba.", SCHEMA_G1)
    assert p["config"]["system_instruction"] == SYSTEM
    assert p["config"]["response_json_schema"] == SCHEMA_G1
    assert p["contents"][0]["parts"][0]["text"] == "L1| Hab. Cuba."
    assert "thinking_config" not in p["config"]        # model default
    assert gb.adapt_schema(SCHEMA_G1) == (SCHEMA_G1, [])


def test_params_validate_against_sdk_types():
    from google.genai import types
    p = gb.build_params(SYSTEM, "L1| x", SCHEMA_G1)
    types.GenerateContentConfig(**p["config"])
    types.InlinedRequest(contents=p["contents"], config=p["config"], metadata={"key": "a"})


# ---------------------------------------------------------------- added when porting onto p4 (2026-11-19)
import gzip  # noqa: E402
import json  # noqa: E402

import pandas as pd  # noqa: E402

import analysis  # noqa: E402
import run_extraction as rx  # noqa: E402
from prompts import CONDITIONS, SCHEMA_G0  # noqa: E402


def test_withheld_answer_is_an_error_not_a_parse_error():
    # e.g. finish_reason RECITATION with no text: must not look like "nothing found"
    rec = gb.record_from_response(REQ, {"candidates": [{"finish_reason": "RECITATION"}],
                                        "usage_metadata": {"prompt_token_count": 10}},
                                  "gemini-4-carbon", batch=False)
    assert rec["parsed"] is None and rec["stop_reason"] == "RECITATION"
    assert "RECITATION" in rec["error"]
    blocked = gb.record_from_response(REQ, {"prompt_feedback": {"block_reason": "OTHER"}},
                                      "gemini-4-carbon", batch=False)
    assert blocked["error"] and blocked["cost_usd"] == 0.0
    # a normal stop with broken JSON stays a parse error (error is None), a truncation stays MAX_TOKENS
    assert gb.record_from_response(REQ, fake("not json"), "gemini-4-carbon", False)["error"] is None
    assert gb.record_from_response(REQ, fake('{"mentions": [', finish="MAX_TOKENS"),
                                   "gemini-4-carbon", False)["error"] is None


def test_both_providers_get_the_same_prompt_text_and_schema():
    pages = rx.select_pages("dev5").head(1)
    kw = dict(pages=pages, versions=["expert", "modern_dots-mocr_plain"], conditions=["G0", "G1"],
              effort="medium", max_tokens=1000)
    ant = rx.build_requests(model="claude-opus-5-5", **kw)
    gem = rx.build_requests(model="gemini-4-carbon", provider="gemini", **kw)
    assert len(ant) == len(gem) == 4
    for a, g in zip(ant, gem):
        assert {k: a[k] for k in a if k != "params"} == {k: g[k] for k in g if k != "params"}
        assert g["params"]["contents"][0]["parts"][0]["text"] == a["params"]["messages"][0]["content"]
        assert g["params"]["config"]["system_instruction"] == a["params"]["system"][0]["text"] == SYSTEM
        assert g["params"]["config"]["response_json_schema"] == CONDITIONS[g["condition"]][1]
        assert g["params"]["config"]["response_json_schema"] == a["params"]["output_config"]["format"]["schema"]
    assert gem[0]["params"]["config"]["response_json_schema"] == SCHEMA_G0


def test_config_and_cost_notes_record_settings_and_price_source():
    cfg = gb.config_for_log("gemini-4-carbon", 32768, batch=False)
    assert cfg["google_genai_sdk"] and cfg["api_version"]
    g = cfg["generation_config"]
    assert g["max_output_tokens"] == 32768 and g["temperature"] is None and g["thinking_config"] is None
    assert cfg["schema_changes_for_gemini"] == []
    pr = gb.cost_notes("gemini-4-carbon")["prices_usd_per_mtok"]
    assert (pr["input"], pr["output_incl_thinking"], pr["cached_input"]) == gb.PRICES["gemini-4-carbon"]
    assert pr["source"].startswith("https://") and pr["valid_until"]


def test_sink_seals_test_pages_and_outcomes_are_told_apart(tmp_path, monkeypatch):
    """Gemini records go through the same Sink: dev open, test only inside the gzip.
    analysis.outcome_table then gives one of the five statuses per request."""
    run = tmp_path / "run_x"
    sink = rx.Sink(run)
    cases = {  # custom_id -> (record, expected outcome)
        "1__expert__G1": gb.record_from_response({**REQ, "custom_id": "1__expert__G1"},
                                                 fake('{"mentions": [{"field": "locality", "line": 1, "quote": "Cuba"}]}'),
                                                 "gemini-4-carbon", False),
        "2__expert__G1": gb.record_from_response({**REQ, "custom_id": "2__expert__G1"}, fake('{"mentions": []}'),
                                                 "gemini-4-carbon", False),
        "3__expert__G1": gb.error_record({**REQ, "custom_id": "3__expert__G1"}, "gemini-4-carbon", "ServerError: 503"),
        "4__expert__G1": gb.record_from_response({**REQ, "custom_id": "4__expert__G1"}, fake("oops"),
                                                 "gemini-4-carbon", False),
        "5__expert__G1": gb.record_from_response({**REQ, "custom_id": "5__expert__G1"},
                                                 fake('{"mentions": [', finish="MAX_TOKENS"), "gemini-4-carbon", False),
    }
    for rec in cases.values():
        sink.write(rec)
    secret = gb.record_from_response({**REQ, "custom_id": "9__expert__G1", "split": "test"},
                                     fake('{"mentions": [{"field": "taxon", "line": 1, "quote": "SEALEDNAME"}]}'),
                                     "gemini-4-carbon", False)
    sink.write(secret)
    sink.close()
    assert sink.n == {"dev": 5, "test": 1}
    assert "SEALEDNAME" not in (run / "dev_outputs.jsonl").read_text(encoding="utf-8")
    with gzip.open(run / "sealed" / "test_outputs.jsonl.gz", "rt", encoding="utf-8") as f:
        assert json.loads(f.readline())["custom_id"] == "9__expert__G1"

    monkeypatch.setattr(analysis, "RESULTS", tmp_path)
    out = analysis.outcome_table("run_x", "dev").set_index("custom_id").outcome.to_dict()
    assert out == {"1__expert__G1": "ok", "2__expert__G1": "empty", "3__expert__G1": "api_error",
                   "4__expert__G1": "parse_error", "5__expert__G1": "truncated"}


def test_finalize_writes_cost_with_versions_and_keeps_seal(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(rx, "ROOT", tmp_path)
    run = tmp_path / "results" / "run_y"
    (tmp_path / "src.txt").write_text("Hab. Cuba.", encoding="utf-8")
    run.mkdir(parents=True)
    pd.DataFrame([{"custom_id": "123__expert__G1", "source": "src.txt"},
                  {"custom_id": "9__expert__G1", "source": "src.txt"}]).to_csv(run / "inputs.csv", index=False)
    dev = gb.record_from_response(REQ, fake('{"mentions": [{"field": "locality", "line": 1, "quote": "Cuba"}]}'),
                                  "gemini-4-carbon", False)
    test = gb.record_from_response({**REQ, "custom_id": "9__expert__G1", "page_id": 9, "split": "test"},
                                   fake('{"mentions": [{"field": "taxon", "line": 1, "quote": "SEALEDNAME"}]}'),
                                   "gemini-4-carbon", False)
    sink = rx.Sink(run)
    sink.write(dev)
    sink.write(test)
    sink.close()
    rx.finalize(run, [rx.meta_of(dev), rx.meta_of(test)], "gemini-4-carbon", batch=False,
                extra_cost=gb.cost_notes("gemini-4-carbon"))
    cost = json.loads((run / "cost.json").read_text())
    assert cost["requests"] == 2 and cost["model_versions_returned"] == {"gemini-4-carbon-001": 2}
    assert cost["tokens"]["output_tokens"] == 1000 and cost["prices_usd_per_mtok"]["source"]
    assert abs(cost["usd_total"] - round(2 * dev["cost_usd"], 4)) < 1e-9
    m = pd.read_csv(run / "dev_mentions.csv")
    assert list(m.value) == ["Cuba"] and list(m.page_id) == [123]        # dev located, test not
    assert (run / "SEALED.md").exists() and (run / "sealed" / "test_outputs.jsonl.gz").exists()
    assert "SEALEDNAME" not in capsys.readouterr().out


def test_bare_array_is_wrapped_and_flagged_other_shapes_are_parse_errors():
    """The Batch API did not enforce the schema (2026-11-19): answers are checked in code."""
    ok = gb.record_from_response(REQ, fake('[{"field": "locality", "line": 1, "quote": "Cuba"}]'),
                                 "gemini-4-carbon", batch=True)
    assert ok["parsed"] == {"mentions": [{"field": "locality", "line": 1, "quote": "Cuba"}]}
    assert ok["schema_deviation"] == "bare_array"
    assert ok["raw"]["candidates"][0]["content"]["parts"][1]["text"].startswith("[")   # raw untouched
    assert gb.record_from_response(REQ, fake('{"mentions": []}'), "gemini-4-carbon", True)["schema_deviation"] is None
    bad = ['[{"field": "place", "line": 1, "quote": "Cuba"}]',            # field not in the enum
           '[{"field": "locality", "value": "Cuba"}]',                    # G0 keys in a G1 request
           '[{"field": "locality", "line": "1", "quote": "Cuba"}]',       # line is not an integer
           '{"mentions": [], "note": "x"}', '{"items": []}', '"Cuba"', '[["locality", 1, "Cuba"]]']
    for text in bad:
        rec = gb.record_from_response(REQ, fake(text), "gemini-4-carbon", batch=True)
        assert rec["parsed"] is None and rec["schema_deviation"].startswith("invalid"), text
        assert rec["error"] is None                                      # counted as parse_error
    g0 = gb.record_from_response({**REQ, "condition": "G0"}, fake('[{"field": "date", "value": "1849"}]'),
                                 "gemini-4-carbon", batch=True)
    assert g0["parsed"] == {"mentions": [{"field": "date", "value": "1849"}]}
