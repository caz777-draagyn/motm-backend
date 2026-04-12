"""
Deep-cleanse surname pools (tiered) for plausibility.

Targets: any `country_*.json` / `custom_*.json` pool where total surnames > 1000.

Balanced heuristic approach:
- remove non-plausible tokens (scripts/name_pool_text.py:is_plausible_token)
- remove obvious fragments / placeholders
- remove given-name leakage for common Western first names (conservative)
- remove extremely cross-country "global" surnames when they are clear outliers for the pool

Writes:
- overwrites `surnames` in-place
- creates backups under data/name_pools/_backup_surnames/<filename>
- writes reports under reports/surname_cleanse/<pool_id>.json
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from name_pool_text import canon_name, is_plausible_token  # noqa: E402
from utils.name_data import NAME_POOL_TIER_KEYS, tier_key_for_pool_seq  # noqa: E402

NAME_POOLS_DIR = ROOT / "data" / "name_pools"
BACKUP_DIR = NAME_POOLS_DIR / "_backup_surnames"
REPORT_DIR = ROOT / "reports" / "surname_cleanse"
FED_PATH = ROOT / "data" / "country_federation.json"

TIERS = NAME_POOL_TIER_KEYS


COMMON_PLACEHOLDER = frozenset(
    {
        "Unknown",
        "Test",
        "Example",
        "Sample",
        "N/A",
        "None",
        "Null",
    }
)

# Very common English given names that frequently leak into surname lists.
# We only drop these if they are also present in the global given-name corpus.
COMMON_GIVEN_EN = frozenset(
    {
        "Aaron",
        "Adam",
        "Alan",
        "Albert",
        "Alex",
        "Alexander",
        "Alfred",
        "Andrew",
        "Anthony",
        "Arthur",
        "Ben",
        "Benjamin",
        "Bernard",
        "Brian",
        "Bruce",
        "Carl",
        "Charles",
        "Chris",
        "Christian",
        "Christopher",
        "Colin",
        "Connor",
        "Craig",
        "Daniel",
        "David",
        "Dean",
        "Dennis",
        "Derek",
        "Dominic",
        "Duncan",
        "Edward",
        "Eric",
        "Ethan",
        "Eugene",
        "Evan",
        "Frank",
        "Gabriel",
        "Gareth",
        "Gary",
        "Geoff",
        "George",
        "Glen",
        "Glenn",
        "Gordon",
        "Graham",
        "Grant",
        "Greg",
        "Guy",
        "Harry",
        "Henry",
        "Ian",
        "Isaac",
        "Ivan",
        "Jack",
        "Jacob",
        "James",
        "Jamie",
        "Jason",
        "Jeff",
        "Jeffrey",
        "Jeremy",
        "Jim",
        "Joe",
        "Joel",
        "John",
        "Johnny",
        "Jonathan",
        "Jordan",
        "Joseph",
        "Joshua",
        "Julian",
        "Justin",
        "Karl",
        "Keith",
        "Ken",
        "Kenneth",
        "Kevin",
        "Kieran",
        "Kyle",
        "Lawrence",
        "Leo",
        "Lewis",
        "Liam",
        "Louis",
        "Luke",
        "Marc",
        "Marcus",
        "Mark",
        "Martin",
        "Matthew",
        "Max",
        "Michael",
        "Mick",
        "Mike",
        "Morgan",
        "Nathan",
        "Neil",
        "Nicholas",
        "Nick",
        "Nigel",
        "Noah",
        "Oliver",
        "Oscar",
        "Owen",
        "Patrick",
        "Paul",
        "Peter",
        "Philip",
        "Phillip",
        "Ricky",
        "Richard",
        "Rob",
        "Robbie",
        "Robert",
        "Roger",
        "Ross",
        "Roy",
        "Russell",
        "Ryan",
        "Sam",
        "Samuel",
        "Scott",
        "Sean",
        "Sebastian",
        "Shane",
        "Shawn",
        "Shaun",
        "Simon",
        "Steven",
        "Steve",
        "Stuart",
        "Terence",
        "Terry",
        "Thomas",
        "Tim",
        "Timothy",
        "Toby",
        "Tom",
        "Tommy",
        "Tony",
        "Trevor",
        "Tyler",
        "Victor",
        "Vincent",
        "Wayne",
        "William",
        "Wilson",
    }
)


DIASPORA_CODES = frozenset(
    {
        # Very mixed surname environments where global overlap is expected.
        # (We still clean these, but we avoid aggressive diaspora pruning here.)
        "USA",
        "CAN",
    }
)


def is_patronymic_surname(name: str, *, pool_code: str) -> str | None:
    """Return reason string if name looks like a patronymic to exclude for this pool."""
    n = name.strip().casefold()
    if pool_code == "ISL":
        # Iceland: patronymics are common, but user wants them filtered out.
        if n.endswith("dottir"):
            return "patronymic_dottir"
        if n.endswith("sson") or n.endswith("son"):
            return "patronymic_son"
    return None

ALLOW_LEN2_SURNAME = frozenset(
    {
        # common CJK romanized surnames / short forms
        "Ng",
        "Wu",
        "Xu",
        "Yu",
        "Li",
        "Hu",
        "He",
        "Ho",
        "Ko",
        "Ou",
        "Ma",
        "An",
        # other short but plausible in some regions
        "Al",
        "El",
    }
)


@dataclass
class Removal:
    name: str
    reason: str


def load_pool_files() -> list[Path]:
    files = []
    for pat in ("country_*.json", "custom_*.json"):
        files.extend(sorted(NAME_POOLS_DIR.glob(pat)))
    return files


def tiered_total(tiered: dict) -> int:
    return sum(len(tiered.get(t, []) or []) for t in TIERS)


def flatten_tiers(tiered: dict) -> list[str]:
    out: list[str] = []
    for t in TIERS:
        out.extend(tiered.get(t, []) or [])
    return out


def split_into_tiers(names: list[str]) -> dict[str, list[str]]:
    """Re-bucket cleansed flat list by 1-based rank (same bands as master CSV / name_data)."""
    out: dict[str, list[str]] = {k: [] for k in NAME_POOL_TIER_KEYS}
    for i, name in enumerate(names, start=1):
        out[tier_key_for_pool_seq(i)].append(name)
    return out


def dedupe_preserve_order(names: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        k = n.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(n)
    return out


def build_global_given_set(pool_files: list[Path]) -> set[str]:
    s: set[str] = set()
    for p in pool_files:
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        g = data.get("given_names_male") or {}
        for name in flatten_tiers(g):
            if isinstance(name, str) and name:
                s.add(canon_name(name))
    return s


def build_surname_pool_counts(pool_files: list[Path]) -> Counter[str]:
    c: Counter[str] = Counter()
    for p in pool_files:
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        s = data.get("surnames") or {}
        for name in flatten_tiers(s):
            if isinstance(name, str) and name:
                c[canon_name(name)] += 1
    return c


def is_fragment(name: str) -> bool:
    n = name.strip()
    if len(n) <= 1:
        return True
    if len(n) == 2 and n.isalpha() and n not in ALLOW_LEN2_SURNAME:
        return True
    if n.casefold() in {"al", "ab", "sk", "md", "jr", "sr"}:
        return True
    return False


def cleanse_surnames_for_pool(
    names: list[str],
    *,
    pool_code: str,
    global_given: set[str],
    surname_pool_counts: Counter[str],
    confed_surname_counts: Counter[str] | None,
) -> tuple[list[str], list[Removal]]:
    kept: list[str] = []
    removed: list[Removal] = []

    for raw in names:
        if not isinstance(raw, str):
            continue
        n = canon_name(raw)
        if not n:
            continue
        if n in COMMON_PLACEHOLDER:
            removed.append(Removal(n, "placeholder"))
            continue
        if not is_plausible_token(n):
            removed.append(Removal(n, "non_plausible_token"))
            continue
        if is_fragment(n):
            removed.append(Removal(n, "fragment"))
            continue

        patronymic_reason = is_patronymic_surname(n, pool_code=pool_code)
        if patronymic_reason:
            removed.append(Removal(n, patronymic_reason))
            continue

        # Given-name leakage (balanced + conservative): only for common English given names
        if n in COMMON_GIVEN_EN and n in global_given:
            removed.append(Removal(n, "given_name_leak"))
            continue

        # Global-overlap outliers: if surname appears across many pools, it may be a migrant/global name.
        # Balanced rule: remove only if extremely global AND not present in the pool's confederation
        # reference set (second signal) AND pool is not a known diaspora-heavy environment.
        # (Keeps cross-cultural pools intact; targets e.g. accidental Smith/Jones leakage in non-diaspora pools.)
        if pool_code not in DIASPORA_CODES:
            global_ct = surname_pool_counts.get(n, 0)
            confed_ct = confed_surname_counts.get(n, 0) if confed_surname_counts else 0
            # Slightly stricter: lower global threshold and allow minimal confed overlap.
            if global_ct >= 15 and confed_ct <= 1 and len(n) <= 12:
                # Keep some globally common Arabic patronymics in MENA pools by checking simple prefixes.
                if n.startswith("Al ") or n.startswith("El "):
                    kept.append(n)
                else:
                    removed.append(Removal(n, "global_overlap_outlier"))
                continue

        kept.append(n)

    kept = dedupe_preserve_order(kept)
    return kept, removed


def write_report(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def backup_pool_file(src: Path) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dst = BACKUP_DIR / src.name
    if not dst.exists():
        dst.write_bytes(src.read_bytes())


def load_confederation_map() -> dict[str, str]:
    if not FED_PATH.is_file():
        return {}
    with open(FED_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {str(k).upper(): str(v) for k, v in data.items()}


def build_confed_surname_counts(
    pool_files: list[Path], confed_map: dict[str, str]
) -> dict[str, Counter[str]]:
    """confed -> Counter(surname) across all pools in that confederation."""
    by_confed: dict[str, Counter[str]] = defaultdict(Counter)
    for p in pool_files:
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        code = str(data.get("country_code") or "").strip().upper()
        conf = confed_map.get(code)
        if not conf:
            continue
        s = data.get("surnames") or {}
        for name in flatten_tiers(s):
            if isinstance(name, str) and name:
                by_confed[conf][canon_name(name)] += 1
    return by_confed


def main() -> None:
    pool_files = load_pool_files()
    global_given = build_global_given_set(pool_files)
    surname_pool_counts = build_surname_pool_counts(pool_files)
    confed_map = load_confederation_map()
    confed_surname_counts = build_confed_surname_counts(pool_files, confed_map)

    targets: list[Path] = []
    for p in pool_files:
        try:
            data = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        s = data.get("surnames") or {}
        if tiered_total(s) > 1000:
            targets.append(p)

    print(f"Target pools (>1000 surnames): {len(targets)}")

    updated = 0
    for p in targets:
        # Re-run from the current on-disk pool state (which may already have been transliterated).
        data = json.load(open(p, encoding="utf-8"))
        pool_id = data.get("pool_id") or p.stem
        code = str(data.get("country_code") or "").strip().upper()
        conf = confed_map.get(code)
        conf_counter = confed_surname_counts.get(conf, Counter()) if conf else Counter()

        before_tiered = data.get("surnames") or {}
        before_names = flatten_tiers(before_tiered)
        before_total = len(before_names)

        kept, removed = cleanse_surnames_for_pool(
            before_names,
            pool_code=code,
            global_given=global_given,
            surname_pool_counts=surname_pool_counts,
            confed_surname_counts=conf_counter,
        )

        after_tiered = split_into_tiers(kept)
        data["surnames"] = after_tiered

        # backup + write pool
        backup_pool_file(p)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")

        # report
        by_reason: dict[str, list[str]] = defaultdict(list)
        for r in removed:
            by_reason[r.reason].append(r.name)
        report = {
            "pool_file": p.as_posix(),
            "pool_id": pool_id,
            "country_code": code,
            "before": {
                "tier_counts": {t: len(before_tiered.get(t, []) or []) for t in TIERS},
                "total": before_total,
            },
            "after": {
                "tier_counts": {t: len(after_tiered.get(t, []) or []) for t in TIERS},
                "total": sum(len(after_tiered[t]) for t in TIERS),
            },
            "removed": {
                "total": len(removed),
                "by_reason_counts": {k: len(v) for k, v in sorted(by_reason.items())},
                "sample_by_reason": {k: sorted(set(v))[:50] for k, v in sorted(by_reason.items())},
            },
        }
        write_report(REPORT_DIR / f"{pool_id}.json", report)

        updated += 1
        print(
            f"{pool_id}: {before_total} -> {report['after']['total']} "
            f"(removed {len(removed)})"
        )

    print(f"Updated pools: {updated}")
    print(f"Backups: {BACKUP_DIR.as_posix()}")
    print(f"Reports: {REPORT_DIR.as_posix()}")


if __name__ == "__main__":
    main()

