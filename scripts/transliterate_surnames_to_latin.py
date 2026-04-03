"""
Pre-pass: transliterate any non-Latin-script surname tokens into Latin.

Why:
- Some pools contained Cyrillic/Greek/etc. tokens; the intention is to keep surnames
  in Latin transliteration, not native script.

Behavior:
- For each pool file in data/name_pools/{country_*,custom_*}.json:
  - If a backup exists under data/name_pools/_backup_surnames/<filename>, use that as
    the baseline surnames source (so we can recover entries that were removed solely
    due to script).
  - Otherwise, use the current file.
- For each surname token:
  - If it contains any alphabetic non-LATIN characters, transliterate using Unidecode.
  - Keep original tokens that are already Latin.
  - Canonicalize with scripts/name_pool_text.py:canon_name.
  - Dedupe case-insensitively.
- Preserve the original tier sizes by concatenating tiers, transforming, then re-splitting
  into 40/60/100/rest.

Outputs:
- Overwrites `surnames` in the pool JSON.
- Writes a report under reports/surname_transliteration/<pool_id>.json with samples.
"""

from __future__ import annotations

import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from unidecode import unidecode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from name_pool_text import canon_name  # noqa: E402

NAME_POOLS_DIR = ROOT / "data" / "name_pools"
BACKUP_DIR = NAME_POOLS_DIR / "_backup_surnames"
REPORT_DIR = ROOT / "reports" / "surname_transliteration"

TIERS = ("very_common", "common", "mid", "rare")


def _is_non_latin_alpha(ch: str) -> bool:
    if not ch.isalpha():
        return False
    return not unicodedata.name(ch, "").startswith("LATIN")


def _needs_translit(s: str) -> bool:
    return any(_is_non_latin_alpha(ch) for ch in s)


def _dedupe_preserve_order(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        k = n.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(n)
    return out


def _flatten(tiered: dict) -> list[str]:
    out: list[str] = []
    for t in TIERS:
        out.extend(tiered.get(t, []) or [])
    return out


def _split_40_60_100(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:40],
        "common": names[40:100],
        "mid": names[100:200],
        "rare": names[200:],
    }


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    pool_files = sorted(NAME_POOLS_DIR.glob("country_*.json")) + sorted(
        NAME_POOLS_DIR.glob("custom_*.json")
    )

    updated = 0
    for p in pool_files:
        # choose baseline (backup if exists)
        baseline_path = BACKUP_DIR / p.name
        src_path = baseline_path if baseline_path.is_file() else p

        data = json.load(open(p, encoding="utf-8"))
        src = json.load(open(src_path, encoding="utf-8"))
        pool_id = data.get("pool_id") or p.stem

        surnames_src = src.get("surnames") or {}
        before = _flatten(surnames_src)

        changed: list[tuple[str, str]] = []
        out_names: list[str] = []
        for raw in before:
            if not isinstance(raw, str) or not raw.strip():
                continue
            s = raw.strip()
            if _needs_translit(s):
                tr = unidecode(s)
                tr = canon_name(tr)
                if tr and tr != canon_name(s):
                    changed.append((s, tr))
                if tr:
                    out_names.append(tr)
            else:
                out_names.append(canon_name(s))

        out_names = _dedupe_preserve_order([n for n in out_names if n])

        # If nothing was transliterated and we weren't using a backup baseline, skip.
        if not changed and src_path == p:
            continue

        data["surnames"] = _split_40_60_100(out_names)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

        report = {
            "pool_file": p.as_posix(),
            "pool_id": pool_id,
            "baseline": src_path.as_posix(),
            "before_total": len(before),
            "after_total": sum(len(data["surnames"][t]) for t in TIERS),
            "changed_pairs_total": len(changed),
            "changed_pairs_sample": [
                (a.encode("unicode_escape").decode("ascii"), b) for a, b in changed[:60]
            ],
        }
        with open(REPORT_DIR / f"{pool_id}.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.write("\n")

        updated += 1

    print(f"Updated pools: {updated}")
    print(f"Reports: {REPORT_DIR.as_posix()}")


if __name__ == "__main__":
    main()

