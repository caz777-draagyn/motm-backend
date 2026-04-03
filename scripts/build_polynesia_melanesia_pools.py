#!/usr/bin/env python3
"""
Populate custom_polynesia.json and custom_melanesia.json with broad regional male givens + surnames.

Polynesian: curated names across Samoa, Tonga, Cook, Tahitian, Hawaiian, Māori patterns.
Melanesian: merges country_PNG.json with extra Melanesian / Pacific supplement names.

Tiering: 20 / 30 / 50 / rest (target ~260 givens, ~96 surnames).

Run: python scripts/build_polynesia_melanesia_pools.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from name_pool_text import canon_name, is_plausible_token

REPO = Path(__file__).resolve().parent.parent
NP = REPO / "data" / "name_pools"

TIERS = ("very_common", "common", "mid", "rare")

DROP_CF: frozenset[str] = frozenset(
    {
        "junior",
        "cj",
        "mj",
        "jr",
        "sr",
        "mr",
        "ms",
        "dr",
        "ii",
        "iii",
        "iv",
        "dad",
        "baby",
        "king",
        "queen",
        "shop",
        "girl",
        "joan",
        "mae",
        "rose",
        "joy",
        "anne",
        "nicole",
        "claire",
        "marie",
        "kim",
    }
)


def flatten_names(pool: dict, key: str) -> list[str]:
    out: list[str] = []
    d = pool.get(key) or {}
    for t in TIERS:
        for x in d.get(t) or []:
            if isinstance(x, str):
                out.append(x)
    return out


def dedupe_first(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in names:
        c = canon_name(raw)
        if not c or not is_plausible_token(c):
            continue
        cf = c.casefold()
        if cf in DROP_CF:
            continue
        if cf in seen:
            continue
        seen.add(cf)
        out.append(c)
    return out


def tier(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def _load_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]


# --- Curated Polynesian male givens (one name per line; scripts/data/polynesian_givens.txt) ---
# Fallback minimal set if file missing (ensures script never outputs empty).
_POLY_FALLBACK: tuple[str, ...] = (
    "Sione",
    "Viliami",
    "Tevita",
    "Siaosi",
    "Malo",
    "Tui",
    "Tau",
    "Pita",
    "Paulo",
    "Manu",
    "Semisi",
    "Salesi",
    "Leki",
    "Kaleo",
    "Kai",
    "Keoni",
    "Kekoa",
    "Iona",
    "Tama",
    "Tane",
    "Wiremu",
    "Tamati",
    "Hone",
    "Rewi",
    "Taniela",
    "Iosefo",
    "Solomone",
    "Filimoni",
    "Ulaiasi",
    "Savenaca",
    "Mikaele",
    "Ariki",
    "Maui",
    "Kaleb",
    "Lilo",
    "Niko",
    "Temo",
    "Sailosi",
    "Timoci",
    "Epeli",
    "Waisea",
    "Inoke",
    "Seru",
    "Peni",
    "Akapusi",
    "Pio",
    "Tomasi",
    "Meli",
    "Sekope",
    "Samiuela",
)


def _polynesian_givens() -> list[str]:
    p = Path(__file__).resolve().parent / "data" / "polynesian_givens.txt"
    raw = _load_lines(p)
    if len(raw) < 100:
        raw = list(_POLY_FALLBACK)
    return dedupe_first(raw)[:280]


def _melanesian_givens(png: dict) -> list[str]:
    png_g = dedupe_first(flatten_names(png, "given_names_male"))
    sup_path = Path(__file__).resolve().parent / "data" / "melanesian_supplement_givens.txt"
    sup = _load_lines(sup_path)
    # Supplement first so tier() surfaces Pacific / regional names before PNG's Anglo-heavy head.
    merged = dedupe_first(sup + png_g)
    return merged[:280]


def _polynesian_surnames() -> list[str]:
    p = Path(__file__).resolve().parent / "data" / "polynesian_surnames.txt"
    raw = _load_lines(p)
    if len(raw) < 40:
        raw = [
            "Faumuina",
            "Tuiletua",
            "Savea",
            "Tuivai",
            "Schmidt",
            "Williams",
            "Tuala",
            "Leota",
            "Mauga",
            "Alo",
            "Tui",
            "Taufa",
            "Fale",
            "Vaa",
            "Liu",
            "Chan",
            "Lee",
            "Young",
            "Brown",
            "Smith",
        ]
    return dedupe_first(raw)[:96]


def _melanesian_surnames(png: dict) -> list[str]:
    png_s = dedupe_first(flatten_names(png, "surnames"))
    sup_path = Path(__file__).resolve().parent / "data" / "melanesian_supplement_surnames.txt"
    sup = _load_lines(sup_path)
    merged = dedupe_first(sup + png_s)
    return merged[:96]


def _meta() -> dict:
    return {
        "tier_probs": {
            "given": {"very_common": 0.45, "common": 0.32, "mid": 0.18, "rare": 0.05},
            "surname": {"very_common": 0.42, "common": 0.33, "mid": 0.20, "rare": 0.05},
        },
        "middle_name_prob": 0.12,
        "compound_surname_prob": 0.06,
        "surname_connector": "-",
    }


def main() -> None:
    png_path = NP / "country_PNG.json"
    png = json.loads(png_path.read_text(encoding="utf-8"))

    poly_g = _polynesian_givens()
    mel_g = _melanesian_givens(png)
    poly_s = _polynesian_surnames()
    mel_s = _melanesian_surnames(png)

    poly_doc = {
        "pool_id": "custom_polynesia",
        "country_code": "TAH",
        "country_name": "Polynesia",
        "given_names_male": tier(poly_g),
        "surnames": tier(poly_s),
        **_meta(),
    }
    mel_doc = {
        "pool_id": "custom_melanesia",
        "country_code": "PNG",
        "country_name": "Melanesia",
        "given_names_male": tier(mel_g),
        "surnames": tier(mel_s),
        **_meta(),
    }

    (NP / "custom_polynesia.json").write_text(
        json.dumps(poly_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (NP / "custom_melanesia.json").write_text(
        json.dumps(mel_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def n(d: dict) -> int:
        return sum(len(d["given_names_male"][t]) for t in TIERS)

    def ns(d: dict) -> int:
        return sum(len(d["surnames"][t]) for t in TIERS)

    print(f"custom_polynesia: givens={n(poly_doc)} surnames={ns(poly_doc)}")
    print(f"custom_melanesia: givens={n(mel_doc)} surnames={ns(mel_doc)}")


if __name__ == "__main__":
    main()
