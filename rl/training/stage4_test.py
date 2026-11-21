"""Module 7b, stage 4: answers of the frozen models on the locked test sets. Runs on the GPU pod.

    python rl/training/stage4_test.py --out <dir>

Reads `configs/stage4_models.json` (written and committed with TEST_PROTOCOL.md before this runs):
each model is the base model or a checkpoint chosen on dev in stage 3, stored as a draft GitHub
release asset. For every model: download, then `stage3_p0.py eval` on the locked test sets with the
evaluation decoding and 8 answers per line (pass@1 uses answers 0-3, pass@8 all 8). Writes the
answers and their scores; the analysis runs afterwards on CPU (`analyze_test_7b.py`). Nothing is
chosen here: every model and set is fixed in the config.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tarfile
import time
from pathlib import Path

import common_7b as C

CFG = C.ROOT / "rl" / "training" / "configs" / "stage4_models.json"
REPO = "dekunsun/BioEvidenceBench"


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def download(asset_id: int, dest: Path) -> None:
    import requests
    h = {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/octet-stream"}
    with requests.get(f"https://api.github.com/repos/{REPO}/releases/assets/{asset_id}", headers=h,
                      stream=True, timeout=3600) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(1 << 22):
                f.write(chunk)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--ckpt-root", default="/workspace/ckpt4")
    args = ap.parse_args()
    out, ck = Path(args.out), Path(args.ckpt_root)
    out.mkdir(parents=True, exist_ok=True)
    ck.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(CFG.read_text())
    status = {"config": cfg, "models": {}}
    for m in cfg["models"]:
        label, t0 = m["label"], time.time()
        if m.get("asset_id"):
            tar = ck / m["asset_name"]
            try:
                download(m["asset_id"], tar)
            except Exception as e:  # noqa: BLE001 (message has no secret)
                status["models"][label] = {"error": f"download: {type(e).__name__}"}
                log(f"{label}: download failed")
                continue
            if tar.stat().st_size != m["size"]:
                status["models"][label] = {"error": "download size differs"}
                continue
            with tarfile.open(tar) as tf:
                tf.extractall(ck, filter="data")
            model = str(ck / m["asset_name"].removesuffix(".tar"))
        else:
            model = C.MODEL_ID
        code = subprocess.run([sys.executable, str(Path(__file__).with_name("stage3_p0.py")), "eval", "--model", model,
                               "--label", label, "--out", str(out / label), "--sets", ",".join(m["sets"]),
                               "--k", str(cfg["k"])], stdout=(out / "eval.log").open("a"),
                              stderr=subprocess.STDOUT).returncode
        status["models"][label] = {"exit": code, "seconds": round(time.time() - t0, 1)}
        log(f"{label}: exit {code}")
        (out / "stage4_status.json").write_text(json.dumps(status, indent=1))
    bad = [k for k, v in status["models"].items() if v.get("exit") != 0]
    if bad:
        sys.exit(f"failed: {bad}")


if __name__ == "__main__":
    main()
