"""
Split Singapore (SIN) name pool into custom pools:
- custom_singapore_malay
- custom_singapore_chinese
- custom_singapore_indian

We keep only names that plausibly belong to one of those buckets, using existing
Malaysia custom pools as seed lists and light heuristics for Singapore-specific
romanizations (e.g. Chinese given-name syllables like Wei/Jun/Yong).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from name_pool_text import is_plausible_token  # noqa: E402

SIN_PATH = ROOT / "data" / "name_pools" / "country_SIN.json"

MAS_MALAY_PATH = ROOT / "data" / "name_pools" / "custom_malaysia_malay.json"
MAS_CHINESE_PATH = ROOT / "data" / "name_pools" / "custom_malaysia_chinese.json"
MAS_INDIAN_PATH = ROOT / "data" / "name_pools" / "custom_malaysia_indian.json"
IND_PATH = ROOT / "data" / "name_pools" / "country_IND.json"
PAK_PATH = ROOT / "data" / "name_pools" / "country_PAK.json"

OUT_MALAY = ROOT / "data" / "name_pools" / "custom_singapore_malay.json"
OUT_CHINESE = ROOT / "data" / "name_pools" / "custom_singapore_chinese.json"
OUT_INDIAN = ROOT / "data" / "name_pools" / "custom_singapore_indian.json"

TIERS = ("very_common", "common", "mid", "rare")


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _tiered_empty() -> dict[str, list[str]]:
    return {t: [] for t in TIERS}


def _tiered_extend(dst: dict[str, list[str]], tier: str, name: str) -> None:
    dst[tier].append(name)


def _dedupe_preserve_order(xs: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in xs:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


WESTERN_GIVEN = frozenset(
    {
        # common Western short-forms found in country_SIN; we only keep them if seeded
        # via the SG Chinese (English) bucket.
        "Paul",
        "David",
        "Chris",
        "James",
        "Mark",
        "John",
        "Andrew",
        "Michael",
        "Ben",
        "Sam",
        "Tom",
        "Steve",
        "Alex",
        "Jack",
        "Richard",
        "Peter",
        "Daniel",
        "Andy",
        "Simon",
        "Ian",
        "Matt",
        "Adam",
        "Lee",
        "Dan",
        "Mike",
        "Stephen",
        "Matthew",
        "Jason",
        "Martin",
        "Dave",
        "Joe",
        "Ryan",
        "Rob",
        "Luke",
        "Kevin",
        "Nick",
        "Gary",
        "Jonathan",
        "Jamie",
        "Neil",
        "Josh",
        "Alan",
        "Darren",
        "Thomas",
        "Robert",
        "Steven",
        "Phil",
        "George",
        "Liam",
        "Tim",
    }
)

# Singapore Chinese romanization / monosyllables frequently appear as short given names.
CHINESE_SYLLABLES = frozenset(
    {
        "Wei",
        "Jun",
        "Yong",
        "Ming",
        "Hui",
        "Jie",
        "Xin",
        "Xuan",
        "Xiang",
        "Jian",
        "Zhi",
        "Shu",
        "Tian",
        "Yuan",
        "Chao",
        "Cha",
        "Chai",
    }
)

SINGAPORE_CHINESE_SURNAMES = frozenset(
    {
        "Tan",
        "Lim",
        "Lee",
        "Ng",
        "Wong",
        "Chan",
        "Goh",
        "Ong",
        "Koh",
        "Teo",
        "Ho",
        "Chua",
        "Chen",
        "Ang",
        "Tay",
        "Low",
        "Yeo",
        "Wang",
        "Chong",
        "Chia",
        "Yap",
        "Lin",
        "Leong",
        "Loh",
    }
)

MALAY_PREFIX_RE = re.compile(
    r"^(Mohd|Mohamad|Mohamed|Muhamad|Muhammad|Mohammad|Abdul|Abdullah|Ahmad|Syed)\b",
    re.IGNORECASE,
)

INDIAN_HINT_RE = re.compile(r"(Singh|Kumar|Nair|Raj|Khan)$", re.IGNORECASE)

MALAY_EXCLUDE_GIVEN = frozenset({"Prince"})

INDIAN_MORPH_RE = re.compile(
    r"("
    r"bh|dh|kh|ph|sh|"
    r"aa|ee|ii|oo|uu|"
    r"abhi|gaur|rohit|rahul|"
    r"sanj|sand|"
    r"prakash|"
    r"jit|deep|"
    r"kesh|nath|"
    r"venkat|subra|"
    r"vish|krish|"
    r"naray|"
    r"ravi|hari|"
    r"anil|aditya|amit"
    r")",
    re.IGNORECASE,
)


def classify_given(
    name: str,
    *,
    malay_seed: set[str],
    chinese_seed: set[str],
    indian_seed: set[str],
) -> str | None:
    if not is_plausible_token(name):
        return None

    if (name in malay_seed or MALAY_PREFIX_RE.match(name)) and name not in MALAY_EXCLUDE_GIVEN:
        return "malay"

    if name in indian_seed or INDIAN_HINT_RE.search(name):
        return "indian"

    # Everything else that is plausible is treated as Singapore Chinese bucket:
    # - English given names are extremely common among SG Chinese
    # - Chinese syllables / short forms also land here
    if name in chinese_seed or name in CHINESE_SYLLABLES or name in WESTERN_GIVEN:
        return "chinese"

    # Default remainder to Chinese to avoid dropping plausible SG names.
    return "chinese"


def classify_surname(
    name: str,
    *,
    malay_seed: set[str],
    chinese_seed: set[str],
    indian_seed: set[str],
) -> str | None:
    if not is_plausible_token(name):
        return None
    if name in chinese_seed or name in SINGAPORE_CHINESE_SURNAMES:
        return "chinese"
    if name in indian_seed:
        return "indian"
    if name in malay_seed or MALAY_PREFIX_RE.match(name):
        return "malay"
    return None


def main() -> None:
    sin = _load(SIN_PATH)
    mas_malay = _load(MAS_MALAY_PATH)
    mas_chinese = _load(MAS_CHINESE_PATH)
    mas_indian = _load(MAS_INDIAN_PATH)
    ind = _load(IND_PATH)
    pak = _load(PAK_PATH)

    malay_given_seed = {
        n
        for t in TIERS
        for n in mas_malay.get("given_names_male", {}).get(t, [])
        if is_plausible_token(n)
    }
    malay_surname_seed = {
        n
        for t in TIERS
        for n in mas_malay.get("surnames", {}).get(t, [])
        if is_plausible_token(n)
    }

    chinese_given_seed = {
        n
        for t in TIERS
        for n in mas_chinese.get("given_names_male", {}).get(t, [])
        if is_plausible_token(n)
    }
    chinese_surname_seed = {
        n
        for t in TIERS
        for n in mas_chinese.get("surnames", {}).get(t, [])
        if is_plausible_token(n)
    }

    sin_given_set: set[str] = set()
    for t in TIERS:
        for n in sin.get("given_names_male", {}).get(t, []):
            if is_plausible_token(n):
                sin_given_set.add(n)

    indian_surname_seed = {
        n
        for t in TIERS
        for n in mas_indian.get("surnames", {}).get(t, [])
        if is_plausible_token(n)
    }
    # SG-Indian reference, restricted to names present in Singapore pool.
    ind_pak_given: set[str] = set()
    for ref in (ind, pak):
        for t in TIERS:
            for n in ref.get("given_names_male", {}).get(t, []):
                if is_plausible_token(n):
                    ind_pak_given.add(n)
    indian_given_seed: set[str] = set()
    for n in sin_given_set:
        if n in malay_given_seed or MALAY_PREFIX_RE.match(n):
            continue
        if n in chinese_given_seed or n in CHINESE_SYLLABLES:
            continue
        if n in WESTERN_GIVEN:
            continue
        if (n in ind_pak_given and (INDIAN_HINT_RE.search(n) or INDIAN_MORPH_RE.search(n))) or INDIAN_HINT_RE.search(
            n
        ):
            indian_given_seed.add(n)

    out = {
        "malay": {"given": _tiered_empty(), "surname": _tiered_empty()},
        "chinese": {"given": _tiered_empty(), "surname": _tiered_empty()},
        "indian": {"given": _tiered_empty(), "surname": _tiered_empty()},
    }

    dropped_given: list[str] = []
    for tier in TIERS:
        for n in sin.get("given_names_male", {}).get(tier, []):
            bucket = classify_given(
                n,
                malay_seed=malay_given_seed,
                chinese_seed=chinese_given_seed,
                indian_seed=indian_given_seed,
            )
            if bucket is None:
                dropped_given.append(n)
            else:
                _tiered_extend(out[bucket]["given"], tier, n)

    dropped_surname: list[str] = []
    for tier in TIERS:
        for n in sin.get("surnames", {}).get(tier, []):
            bucket = classify_surname(
                n,
                malay_seed=malay_surname_seed,
                chinese_seed=chinese_surname_seed,
                indian_seed=indian_surname_seed,
            )
            if bucket is None:
                dropped_surname.append(n)
            else:
                _tiered_extend(out[bucket]["surname"], tier, n)

    for bucket in out:
        for tier in TIERS:
            out[bucket]["given"][tier] = _dedupe_preserve_order(out[bucket]["given"][tier])
            out[bucket]["surname"][tier] = _dedupe_preserve_order(out[bucket]["surname"][tier])

    common_meta = {
        "country_code": "SIN",
        "tier_probs": sin.get("tier_probs", {}),
        "middle_name_prob": sin.get("middle_name_prob", 0.15),
        "compound_surname_prob": sin.get("compound_surname_prob", 0.05),
        "surname_connector": sin.get("surname_connector", "-"),
    }

    pools = {
        "malay": {
            "pool_id": "custom_singapore_malay",
            "country_name": "Singapore Malay",
            "given_names_male": out["malay"]["given"],
            "surnames": out["malay"]["surname"],
            **common_meta,
        },
        "chinese": {
            "pool_id": "custom_singapore_chinese",
            "country_name": "Singapore Chinese",
            "given_names_male": out["chinese"]["given"],
            "surnames": out["chinese"]["surname"],
            **common_meta,
        },
        "indian": {
            "pool_id": "custom_singapore_indian",
            "country_name": "Singapore Indian",
            "given_names_male": out["indian"]["given"],
            "surnames": out["indian"]["surname"],
            **common_meta,
        },
    }

    for path, payload in (
        (OUT_MALAY, pools["malay"]),
        (OUT_CHINESE, pools["chinese"]),
        (OUT_INDIAN, pools["indian"]),
    ):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")

    print("Wrote:")
    print("  -", OUT_MALAY.as_posix())
    print("  -", OUT_CHINESE.as_posix())
    print("  -", OUT_INDIAN.as_posix())
    print()
    for bucket in ("malay", "chinese", "indian"):
        g_total = sum(len(pools[bucket]["given_names_male"][t]) for t in TIERS)
        s_total = sum(len(pools[bucket]["surnames"][t]) for t in TIERS)
        print(f"{bucket}: given={g_total} surname={s_total}")
    print()
    print(f"dropped: given={len(dropped_given)} surname={len(dropped_surname)}")
    if dropped_given:
        u = sorted(set(dropped_given))
        print("sample dropped given:", ", ".join(u[:40]))
        if len(u) > 40:
            print(f"  ... +{len(u)-40} more")
    if dropped_surname:
        u = sorted(set(dropped_surname))
        print("sample dropped surname:", ", ".join(u[:40]))
        if len(u) > 40:
            print(f"  ... +{len(u)-40} more")


if __name__ == "__main__":
    main()

