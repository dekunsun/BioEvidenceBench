"""
Before committing, replace description text whose rights we cannot confirm with a
placeholder that keeps the page id, length and SHA-1 (so the run stays checkable).

Kept verbatim: BHL pages whose item CopyrightStatus is "Public domain..." or
NOT_IN_COPYRIGHT (BHL item table). Redacted: BHL pages "In copyright" (CC BY-NC-SA)
or "Not provided", and all EcoFlora text (third-party site, licence not checked).

Usage: python adept_repro/scripts/redact_texts.py --rights adept_repro/outputs/rights_check.csv \
          adept_repro/outputs/descriptions_achillea_millefolium adept_repro/outputs/traits_leersia_hexandra
"""
import argparse
import hashlib
from pathlib import Path

import pandas as pd
import yaml

OK = ("public domain", "not_in_copyright")


def placeholder(text, why):
    return f"[redacted: {why}; {len(text)} chars; sha1={hashlib.sha1(text.encode()).hexdigest()}]"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rights", type=Path, required=True)
    ap.add_argument("dirs", nargs="+", type=Path)
    args = ap.parse_args()
    rights = pd.read_csv(args.rights).drop_duplicates("PageID")
    status = dict(zip(rights.PageID.astype(str), rights.CopyrightStatus.fillna("unknown")))

    def why_not(source, source_id):
        if source != "bhl":
            return f"{source} text, licence not checked"
        s = status.get(str(int(source_id)), "unknown")
        return None if s.lower().startswith(OK) else f"BHL CopyrightStatus '{s.strip()}'"

    for d in args.dirs:
        y = d / "bhl_descriptions.yaml"
        if y.exists():
            items = yaml.full_load(y.open()) or []
            for it in items:
                if (w := why_not("bhl", it["source_id"])):
                    it["text"] = placeholder(it["text"], w)
            y.write_text(yaml.dump(items, explicit_start=True, default_flow_style=False))
        c = d / "descriptions.csv"
        if c.exists():
            df = pd.read_csv(c)
            df["text"] = [placeholder(t, w) if (w := why_not(s, i)) else t
                          for t, s, i in zip(df.text, df.source, df.source_id.fillna(0))]
            df.to_csv(c, index=False)
        print("redacted", d)


if __name__ == "__main__":
    main()
