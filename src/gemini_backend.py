"""Gemini (Google Gen AI SDK) path for run_extraction.py.

Same prompts, same numbered input, same output record format as the Anthropic
path, so locate.py, run_extraction.finalize() and unseal.py work unchanged.

What is sent (docs read 2026-11-18: aistudio.google.com/docs/structured-output,
/thinking, /batch-api; /pricing re-read 2026-11-19):
  * generateContent, system_instruction = prompts.SYSTEM, one user turn = the
    G0/G1 task template filled with the numbered page text;
  * response_mime_type "application/json" + response_json_schema = our schema
    from prompts.py, passed as is (adapt_schema() lists any change, and the list
    is saved in config.json);
  * thinking: model default (no thinking_config sent; the docs give "medium"
    as the default for gemini-4-carbon, and thinking cannot be switched off);
  * max_output_tokens: the model's non-streaming limit (32,768). It INCLUDES
    thinking tokens, so a long think can truncate the JSON (finish MAX_TOKENS).

Usage. Gemini reports prompt_token_count (includes implicitly cached tokens),
cached_content_token_count, candidates_token_count and thoughts_token_count.
Output is billed for candidates + thoughts. The record keeps these native
counts and also fills the Anthropic-style keys that finalize() sums:
  input_tokens = prompt - cached, cache_read_input_tokens = cached,
  output_tokens = candidates + thoughts, cache_creation_input_tokens = 0.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime, timezone

API_BASE = "https://generativelanguage.googleapis.com/"   # SDK default (Gemini Developer API)
API_VERSION = "v1beta"                                     # SDK default

# $ per million tokens: input, output (incl. thinking), cached input.
# From https://aistudio.google.com/docs/pricing (same page as
# ai.google.dev/gemini-api/docs/pricing), checked again 2026-11-19. These promo
# prices hold "through November 30, 2026"; from Dec 1 they double ($4 / $20 / $0.20).
# Batch requests cost 50% of these.
PRICES = {
    "gemini-4-carbon": (2.00, 10.00, 0.10),
}
PRICES_VALID_UNTIL = "2026-11-30"
PRICES_SOURCE = "https://aistudio.google.com/docs/pricing (Paid Tier, Standard; read 2026-11-19)"
MAX_OUTPUT_TOKENS = 32768


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def adapt_schema(schema: dict) -> tuple[dict, list[str]]:
    """Return the schema to send and a list of changes made. Currently none:
    response_json_schema takes our JSON Schema (object/array/string/integer,
    enum, required, additionalProperties) unchanged. If the API ever rejects a
    keyword, drop it here and append a note, so config.json records it."""
    return copy.deepcopy(schema), []


def build_params(system: str, user_text: str, schema: dict, max_output_tokens: int = MAX_OUTPUT_TOKENS) -> dict:
    """One generateContent request as a plain dict (also the inline batch format)."""
    sch, _ = adapt_schema(schema)
    return {
        "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        "config": {
            "system_instruction": system,
            "response_mime_type": "application/json",
            "response_json_schema": sch,
            "max_output_tokens": max_output_tokens,
        },
    }


def prices_for_log(model: str) -> dict:
    pi, po, pc = PRICES[model]
    return {"input": pi, "output_incl_thinking": po, "cached_input": pc, "batch_multiplier": 0.5,
            "valid_until": PRICES_VALID_UNTIL, "source": PRICES_SOURCE}


def config_for_log(model: str, max_output_tokens: int, batch: bool) -> dict:
    """Provider-specific part of config.json: SDK, endpoint, decoding and thinking settings, prices."""
    _, changes = adapt_schema({})
    return {"google_genai_sdk": sdk_version(), "api_base_url": API_BASE, "api_version": API_VERSION,
            "api": "generateContent" + (" (Batch API, inline requests)" if batch else ""),
            "generation_config": {
                "response_mime_type": "application/json",
                "response_json_schema": "prompts/schema_<G0|G1>.json, sent unchanged",
                "max_output_tokens": max_output_tokens,
                "thinking_config": None, "thinking_note": "not sent: model default (docs: thinking_level medium)",
                "temperature": None, "temperature_note": "not sent: model default",
                "top_p": None, "top_k": None, "seed": None},
            "schema_changes_for_gemini": changes,
            "prices_usd_per_mtok": prices_for_log(model)}


def cost_notes(model: str) -> dict:
    """Added to cost.json so the dollars can be recomputed from the token counts."""
    return {"prices_usd_per_mtok": prices_for_log(model),
            "token_note": "input_tokens = prompt - cached; output_tokens = candidates + thoughts (both billed "
                          "as output); cache_read_input_tokens = implicitly cached prompt tokens; USD is "
                          "computed here from these counts and prices, not read from a Google invoice"}


def model_info(client, model: str) -> dict:
    """models.get for the id: the version string and limits the API reports."""
    m = client.models.get(model=model)
    return {"name": m.name, "version": m.version, "display_name": m.display_name,
            "input_token_limit": m.input_token_limit, "output_token_limit": m.output_token_limit,
            "retrieved_at": now()}


def api_errors() -> tuple:
    from google.genai import errors
    return (errors.APIError,)


def usage_from(um: dict | None) -> dict:
    um = um or {}
    prompt = um.get("prompt_token_count") or 0
    cached = um.get("cached_content_token_count") or 0
    cand = um.get("candidates_token_count") or 0
    thoughts = um.get("thoughts_token_count") or 0
    return {"input_tokens": prompt - cached, "output_tokens": cand + thoughts,
            "cache_creation_input_tokens": 0, "cache_read_input_tokens": cached,
            "prompt_token_count": prompt, "cached_content_token_count": cached,
            "candidates_token_count": cand, "thoughts_token_count": thoughts,
            "total_token_count": um.get("total_token_count")}


def cost_of(usage: dict, model: str, batch: bool) -> float:
    pi, po, pc = PRICES[model]
    c = (usage.get("input_tokens", 0) * pi + usage.get("output_tokens", 0) * po
         + usage.get("cache_read_input_tokens", 0) * pc) / 1e6
    return c * (0.5 if batch else 1.0)


def _answer_text(d: dict) -> str:
    """Concatenate the non-thought text parts of the first candidate."""
    cands = d.get("candidates") or []
    if not cands:
        return ""
    parts = ((cands[0].get("content") or {}).get("parts")) or []
    return "".join(p.get("text") or "" for p in parts if not p.get("thought"))


def record_from_response(req: dict, resp, model: str, batch: bool) -> dict:
    """resp: a google.genai GenerateContentResponse (or anything with
    model_dump()), or an already-dumped dict. Returns the same record shape
    as run_extraction.record_from_message()."""
    if isinstance(resp, dict):
        d = resp
    else:
        d = resp.model_dump(mode="json", exclude_none=True)
    cands = d.get("candidates") or []
    finish = cands[0].get("finish_reason") if cands else None
    if finish is None and d.get("prompt_feedback"):
        finish = "PROMPT_BLOCKED:" + str((d["prompt_feedback"] or {}).get("block_reason"))
    text = _answer_text(d)
    try:
        parsed = json.loads(text) if text else None
    except json.JSONDecodeError:
        parsed = None
    usage = usage_from(d.get("usage_metadata"))
    # No usable answer and not a normal stop or a truncation: the API withheld the answer
    # (SAFETY, RECITATION, blocked prompt ...). Logged as an error so that
    # analysis.outcome_table counts it as api_error, not parse_error or "nothing found".
    error = None
    if parsed is None and finish not in ("STOP", "MAX_TOKENS"):
        error = f"no answer returned; finish_reason={finish}"
    return {"custom_id": req["custom_id"], "page_id": req["page_id"], "split": req["split"],
            "version": req["version"], "condition": req["condition"],
            "model": d.get("model_version") or model,
            "stop_reason": finish, "usage": usage, "cost_usd": cost_of(usage, model, batch),
            "parsed": parsed, "raw": d, "error": error, "received_at": now()}


def error_record(req: dict, model: str, err: str) -> dict:
    return {"custom_id": req["custom_id"], "page_id": req["page_id"], "split": req["split"],
            "version": req["version"], "condition": req["condition"], "model": model,
            "stop_reason": None, "usage": {}, "cost_usd": 0.0, "parsed": None, "raw": None,
            "error": err[:300], "received_at": now()}


def make_client(api_key: str):
    from google import genai
    from google.genai import types
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=5)))


def sdk_version() -> str:
    import google.genai
    return google.genai.__version__


def generate(client, model: str, params: dict):
    return client.models.generate_content(model=model, contents=params["contents"], config=params["config"])


def submit_batch(client, model: str, reqs: list[dict], display_name: str):
    """Inline batch (total request size must stay under 20 MB). Each request
    carries metadata.key = custom_id so responses can be matched back."""
    src = [{"contents": r["params"]["contents"], "config": r["params"]["config"],
            "metadata": {"key": r["custom_id"]}} for r in reqs]
    return client.batches.create(model=model, src=src, config={"display_name": display_name})


TERMINAL = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}


def batch_state(job) -> str:
    s = job.state
    return getattr(s, "value", None) or str(s)


def iter_batch_results(job, custom_ids: list[str]):
    """Yield (custom_id, response_or_None, error_or_None). Matches by
    metadata.key; falls back to submission order if the key is missing."""
    responses = (job.dest.inlined_responses if job.dest else None) or []
    for i, ir in enumerate(responses):
        cid = (ir.metadata or {}).get("key") or (custom_ids[i] if i < len(custom_ids) else None)
        err = None
        if ir.error is not None:
            err = f"batch error: {ir.error.model_dump(mode='json', exclude_none=True)}"
        yield cid, ir.response, err
