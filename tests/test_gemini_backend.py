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
               "usage", "cost_usd", "parsed", "raw", "error", "received_at"}


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
