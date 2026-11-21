"""Publish the 7d research checkpoint (Gloria, 2026-11-21: "你直接发就可以"). Runs on a RunPod pod,
where the repository token exists as the RunPod secret GITHUB_TOKEN (never printed or written).

    python rl/release/publish_release.py --out <dir>

1. Download `sft_s2.tar` (asset 776877455 of the private draft `rl-ckpt-20261121-2008_sft600s2`),
   check its size against the frozen `stage4_models.json`, compute its SHA-256 and list its members.
2. Stop unless every member is a model or tokenizer file under `sft_s2/` (no other file, no link).
3. Create a draft release `rl-sft-ocr-repair-v1` at the training code commit with the model card
   (`MODEL_CARD_sft_s2.md` + the SHA-256) as notes, upload the same file, check size and digest,
   then publish it. The private drafts are left as they are.
Writes publish_result.json (URLs, sizes, SHA-256, member list) to --out.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tarfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
REPO = "dekunsun/BioEvidenceBench"
API = f"https://api.github.com/repos/{REPO}"
ASSET_ID, SIZE, NAME = 776877455, 1203578880, "sft_s2.tar"
TAG, COMMIT = "rl-sft-ocr-repair-v1", "c994ade32023c944ee47c44699b47ab915fe687f"
TITLE = "OCR line repair: Qwen3-0.6B + SFT (research checkpoint, not for automatic replacement)"
ALLOWED = {"config.json", "generation_config.json", "model.safetensors", "tokenizer.json", "tokenizer_config.json",
           "special_tokens_map.json", "vocab.json", "merges.txt", "added_tokens.json", "chat_template.jinja"}


def h(accept: str = "application/vnd.github+json") -> dict:
    return {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": accept}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    out = Path(ap.parse_args().out)
    out.mkdir(parents=True, exist_ok=True)
    res: dict = {"tag": TAG, "commit": COMMIT}

    def done(msg: str, code: int = 0):
        res["message"] = msg
        (out / "publish_result.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
        print(msg, flush=True)
        sys.exit(code)

    cfg = json.loads((ROOT / "rl" / "training" / "configs" / "stage4_models.json").read_text())
    m = next(x for x in cfg["models"] if x["label"] == "sft_s2")
    assert m["asset_id"] == ASSET_ID and m["size"] == SIZE, "model list and script disagree"

    tar = Path("/workspace") / NAME
    sha = hashlib.sha256()
    with requests.get(f"{API}/releases/assets/{ASSET_ID}", headers=h("application/octet-stream"), stream=True,
                      timeout=3600) as r:
        r.raise_for_status()
        with tar.open("wb") as f:
            for chunk in r.iter_content(1 << 22):
                f.write(chunk)
                sha.update(chunk)
    res["size"], res["sha256"] = tar.stat().st_size, sha.hexdigest()
    if res["size"] != SIZE:
        done(f"size {res['size']} differs from the tested file", 1)
    with tarfile.open(tar) as tf:
        members = tf.getmembers()
    res["members"] = [(x.name, x.size, "dir" if x.isdir() else "file" if x.isfile() else "other") for x in members]
    bad = [x.name for x in members if not (x.isdir() and x.name == "sft_s2") and not
           (x.isfile() and x.name.startswith("sft_s2/") and x.name.split("/", 1)[1] in ALLOWED)]
    if bad:
        done(f"unexpected members, not published: {bad}", 1)

    card = (ROOT / "rl" / "release" / "MODEL_CARD_sft_s2.md").read_text(encoding="utf-8")
    body = card + f"\n\n**File**: `{NAME}`, {SIZE:,} bytes, SHA-256 `{res['sha256']}`.\n"
    r = requests.post(f"{API}/releases", headers=h(), timeout=60,
                      json={"tag_name": TAG, "target_commitish": COMMIT, "name": TITLE, "body": body,
                            "draft": True, "prerelease": False})
    if r.status_code != 201:
        done(f"create release: HTTP {r.status_code}", 1)
    rel = r.json()
    res["release_id"] = rel["id"]
    with tar.open("rb") as f:
        a = requests.post(f"https://uploads.github.com/repos/{REPO}/releases/{rel['id']}/assets",
                          params={"name": NAME}, data=f, timeout=3600,
                          headers={**h(), "Content-Type": "application/octet-stream"})
    if a.status_code != 201 or a.json().get("size") != SIZE:
        done(f"upload: HTTP {a.status_code}; release left as a draft", 1)
    digest = a.json().get("digest")
    res["asset_digest"] = digest
    if digest and digest != f"sha256:{res['sha256']}":
        done("GitHub's digest differs from the downloaded file; release left as a draft", 1)
    p = requests.patch(f"{API}/releases/{rel['id']}", headers=h(), timeout=60,
                       json={"draft": False, "make_latest": "true"})
    if p.status_code != 200:
        done(f"publish: HTTP {p.status_code}; release left as a draft", 1)
    res["html_url"] = p.json()["html_url"]
    res["asset_url"] = a.json()["browser_download_url"]
    done("published")


if __name__ == "__main__":
    main()
