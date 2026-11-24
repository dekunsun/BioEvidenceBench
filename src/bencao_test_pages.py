"""本草綱目 case: choose the independent test half-leaves and build the scan-check pack (after the freeze).

    python src/bencao_test_pages.py select   -> data/bencao/test_pages.csv (8 half-leaves; commit before anything else)
    python src/bencao_test_pages.py pack     -> scans, Kanripo texts, results/bencao_test/scan_verify_test.xlsx
    python src/bencao_test_pages.py html [out] -> verify_test.html (scans embedded) for the author's scan check

Chosen by the author on 2026-11-24 ("按你的建议，8 页，两卷各 4 页"): 4 half-leaves from 卷十二上 (Kanripo
KR3e0079_036) and 4 from 卷十二下 (KR3e0079_037), one per content stratum per volume, by a fixed random
seed, from the Kanripo text only: no model has read these pages. Strata, assigned in this order:
  names_places   the half-leaf has a 釋名 or 集解 section (alternative names, places, cited authors)
  prescriptions  it has 附方, or at least 6 dose words (兩, 錢, 分, 升, 合 used as measures are not separated;
                 a crude count of 兩/錢/升)
  note_dense     at least 60% of its characters are in small two-column notes
  prose          everything else (主治, 發明, 正誤 discussion; fewer names expected)
Excluded: the six dev half-leaves, the prompt-example half-leaves 036-1a / 2a / 2b, and half-leaves with
fewer than 120 characters (title and blank leaves).
Scans: Internet Archive item 06048793.cn (CADAL, public domain). Image n = 10 + index for 卷十二上 (as in the
pilot) and n = 104 + index for 卷十二下 (n103 is 036-47b, the last leaf of 卷十二上; n104 is 037-1a, checked
by eye on n103-n108, 2026-11-24). The author's scan check confirms each page.
"""
from __future__ import annotations

import random
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from bencao_pilot import IA, UA, get, plain  # noqa: E402

DATA, CACHE = ROOT / "data" / "bencao", ROOT / "data" / "cache" / "bencao"
OUT = ROOT / "results" / "bencao_test"
VOLUMES = {"036": 10, "037": 104}                      # Kanripo file -> IA image n of its first half-leaf
EXCLUDE = {"036-1a", "036-2a", "036-2b", "036-1b", "036-5a", "036-7b", "036-12b", "036-13a", "036-30a"}
STRATA = ["names_places", "prescriptions", "note_dense", "prose"]
SEED = 20261124


def half_leaves(vol: str) -> dict[str, str]:
    t = get(f"https://raw.githubusercontent.com/kanripo/KR3e0079/master/KR3e0079_{vol}.txt",
            CACHE / f"KR3e0079_{vol}.txt").decode("utf-8")
    parts = re.split(rf"<pb:KR3e0079_WYG_({vol}-\d+[ab])>¶\n", t)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def stratum(raw: str) -> tuple[str, float]:
    body = re.sub(r"\s|¶", "", raw)
    notes = sum(len(re.sub(r"[/\s¶]", "", m)) for m in re.findall(r"\(([^)]*)\)", raw))
    share = notes / max(1, len(re.sub(r"[()/]", "", body)))
    if "釋名" in body or "集解" in body:
        return "names_places", share
    if "附方" in body or len(re.findall(r"[兩錢升]", body)) >= 6:
        return "prescriptions", share
    if share >= 0.6:
        return "note_dense", share
    return "prose", share


def select() -> None:
    rng = random.Random(SEED)
    rows, cand = [], []
    for vol, first in VOLUMES.items():
        kr = half_leaves(vol)
        pool = {s: [] for s in STRATA}
        for i, (pb, raw) in enumerate(kr.items()):
            chars = len(re.sub(r"\s", "", plain(raw)))
            st, share = stratum(raw)
            cand.append({"half_leaf": pb, "stratum": st, "chars": chars, "note_share": round(share, 2),
                         "excluded": pb in EXCLUDE or chars < 120})
            if pb not in EXCLUDE and chars >= 120:
                pool[st].append((pb, i, chars, share))
        for st in STRATA:
            if not pool[st]:
                raise SystemExit(f"no candidate for {st} in {vol}")
            pb, i, chars, share = rng.choice(sorted(pool[st]))
            rows.append({"half_leaf": pb, "volume": "卷十二上" if vol == "036" else "卷十二下", "stratum": st,
                         "ia_item": IA, "ia_image_n": first + i, "chars": chars, "note_share": round(share, 2),
                         "candidates_in_stratum": len(pool[st]), "seed": SEED})
    DATA.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cand).to_csv(DATA / "test_candidates.csv", index=False)
    pd.DataFrame(rows).to_csv(DATA / "test_pages.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    print(pd.DataFrame(cand).query("not excluded").groupby("half_leaf", sort=False).size().shape[0], "candidates")


def pack() -> None:
    pages = pd.read_csv(DATA / "test_pages.csv")
    sheet = []
    for r in pages.itertuples():
        vol = r.half_leaf.split("-")[0]
        raw = half_leaves(vol)[r.half_leaf]
        txt = plain(raw)
        for sub, body in (("kanripo", raw), ("kanripo_plain", txt)):
            (DATA / sub).mkdir(parents=True, exist_ok=True)
            (DATA / sub / f"{r.half_leaf}.txt").write_text(body, encoding="utf-8")
        get(f"https://archive.org/download/{IA}/page/n{r.ia_image_n}_w1200.jpg", OUT / "pages" / f"{r.half_leaf}.jpg")
        for i, line in enumerate(txt.split("\n"), 1):
            sheet.append({"half_leaf": r.half_leaf, "line": i, "kanripo_text": line, "matches_scan": "",
                          "scan_reading": "", "note": ""})
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sheet).to_excel(OUT / "scan_verify_test.xlsx", index=False)
    print(OUT / "scan_verify_test.xlsx", len(sheet), "lines")


def html(dest: str | None = None) -> Path:
    """One self-contained page: each scan beside its numbered Kanripo lines, rare characters marked with
    their code point (and usual form where known), as for the pilot's verify page. Scans are embedded so the
    file can be opened on its own. bencao_pilot.py is frozen, so this is a small copy, not a change to it."""
    import base64
    import html as H
    from bencao_pilot import RARE
    pages = pd.read_csv(DATA / "test_pages.csv")

    def mark(line: str) -> str:
        out = []
        for ch in line:
            cp = ord(ch)
            if cp > 0xFFFF or 0x3400 <= cp <= 0x4DBF:
                hint = RARE.get(ch, "")
                out.append(f"<span class='rare'>{H.escape(ch)}</span><span class='hint'>〔{hint + ' ' if hint else ''}U+{cp:04X}〕</span>")
            elif ch == "〓":
                out.append("<span class='rare'>〓</span><span class='hint'>〔Kanripo: character outside Unicode〕</span>")
            else:
                out.append(H.escape(ch))
        return "".join(out)

    parts = []
    for r in pages.itertuples():
        lines = (DATA / "kanripo_plain" / f"{r.half_leaf}.txt").read_text(encoding="utf-8").split("\n")
        src = "data:image/jpeg;base64," + base64.b64encode((OUT / "pages" / f"{r.half_leaf}.jpg").read_bytes()).decode()
        lis = "".join(f"<li><span class='n'>{i}</span>{mark(l)}</li>" for i, l in enumerate(lines, 1))
        parts.append(f"<section><h2>{r.half_leaf} · {r.volume}</h2><div class='row'>"
                     f"<img src='{src}' alt='scan {r.half_leaf}'><ol>{lis}</ol></div>"
                     f"<p class='meta'>Internet Archive 06048793.cn image n{r.ia_image_n} · Commons DjVu page {r.ia_image_n + 1}</p></section>")
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>本草綱目 test set: scan check</title><style>
:root{{--bg:#fff;--fg:#1b1b1b;--muted:#666;--rule:#ddd;--hint:#a0522d}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#151515;--fg:#eee;--muted:#aaa;--rule:#333;--hint:#e0a070}}}}
:root[data-theme="dark"]{{--bg:#151515;--fg:#eee;--muted:#aaa;--rule:#333;--hint:#e0a070}}
body{{background:var(--bg);color:var(--fg);font-family:"Noto Serif CJK TC","Songti TC","HanaMinA","HanaMinB",serif;margin:0 16px 40px;max-width:1200px}}
h1{{font-size:1.3rem}} h2{{font-size:1.05rem;border-top:1px solid var(--rule);padding-top:12px}}
.row{{display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap}} img{{max-width:520px;width:100%;border:1px solid var(--rule);background:#fff}}
ol{{list-style:none;padding:0;margin:0;flex:1;min-width:280px;font-size:1.15rem;line-height:1.9}}
.n{{display:inline-block;width:2em;color:var(--muted);font-size:.85rem}} .meta{{color:var(--muted);font-size:.85rem}}
.rare{{background:rgba(160,82,45,.15);border-radius:3px}} .hint{{color:var(--hint);font-size:.75rem}}
</style></head><body><h1>本草綱目 · 测试集 8 个半叶 · 转录对照扫描</h1>
<p>第 1 行是扫描最右边一列，从右往左读；双行小注已合并（先右小行，再左小行）。差异记在 <code>scan_verify_test.xlsx</code>，做法和试点一样。转录：Kanseki Repository（CC BY-SA 4.0）；扫描：公有领域。</p>
{''.join(parts)}</body></html>"""
    out = Path(dest) if dest else OUT / "verify_test.html"
    out.write_text(page, encoding="utf-8")
    print(out, round(out.stat().st_size / 1e6, 1), "MB")
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "html":
        html(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        {"select": select, "pack": pack}[cmd]()
