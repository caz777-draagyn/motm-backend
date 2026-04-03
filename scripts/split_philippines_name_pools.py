#!/usr/bin/env python3
"""
Cleanse country_PHI + custom Philippines name pools: drop non-plausible / junk tokens,
fix common typos, re-tier male givens 20/30/50/rest with regional emphasis for:
  - custom_philippines_tagalog.json (Luzon / Tagalog-weighted frequency)
  - custom_philippines_visayan.json (Visayas / Cebuano-weighted frequency)

Pan-Philippine names stay in both customs (overlap allowed). Tier *order* differs by pool;
country_PHI keeps neutral nationwide ordering.

Run: python scripts/split_philippines_name_pools.py
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_COUNTRY = _REPO / "data" / "name_pools" / "country_PHI.json"
_TAG = _REPO / "data" / "name_pools" / "custom_philippines_tagalog.json"
_VIS = _REPO / "data" / "name_pools" / "custom_philippines_visayan.json"

_TIER_ORDER = ("very_common", "common", "mid", "rare")
_TIER_RANK = {t: i for i, t in enumerate(_TIER_ORDER)}

_VISAYAN_BOOST_CF: frozenset[str] = frozenset(
    {
        "jun",
        "jon",
        "jomar",
        "jomel",
        "joemar",
        "jomari",
        "jom",
        "rodel",
        "rowel",
        "roel",
        "jayr",
        "rjay",
        "efren",
        "noli",
        "froilan",
        "kerwin",
        "kervin",
        "jhun",
        "jhoy",
        "jonel",
        "ruel",
        "jey",
        "jovi",
        "jovan",
        "jem",
        "jojo",
        "darwin",
        "sherwin",
        "rommel",
        "roan",
        "erwin",
        "nilo",
        "virgilio",
        "edgardo",
        "jobert",
        "jocel",
        "cholo",
        "beng",
        "rhon",
        "rudy",
        "ronie",
        "rollo",
    }
)

_TAGALOG_BOOST_CF: frozenset[str] = frozenset(
    {
        "juan",
        "jose",
        "josé",
        "miguel",
        "paolo",
        "carlo",
        "kiko",
        "bong",
        "totoy",
        "boy",
        "juanito",
        "joselito",
        "pocholo",
        "jolo",
        "macky",
        "mark",
        "john",
        "michael",
        "joshua",
        "jayson",
        "jhune",
    }
)

_REPAIR_CF: dict[str, str] = {
    "keneth": "Kenneth",
    "rafel": "Rafael",
    "miquel": "Miguel",
    "jefrey": "Jeffrey",
    "mathew": "Matthew",
    "niel": "Neil",
    "collen": "Colin",
    "jhon": "John",
}

_DROP_GIVEN_CF: frozenset[str] = frozenset(
    {
        "daddy",
        "dad",
        "babe",
        "hugot",
        "aquarius",
        "ate",
        "dear",
        "christ",
        "mang",
        "tiger",
        "jupiter",
        "ford",
        "d'",
        "pop",
        "pie",
        "mg",
        "bb",
        "ak",
        "zy",
        "zee",
        "oh",
        "wa",
        "tee",
        "mix",
        "nad",
        "rez",
        "tri",
        "tyo",
        "tantan",
        "agung",
        "angga",
        "bayu",
        "abhishek",
        "rajesh",
        "rahul",
        "rohit",
        "sanjay",
        "tomeu",
        "jordi",
        "xisco",
        "francesc",
        "llorenç",
        "llorenc",
        "guillem",
        "jaume",
        "borja",
        "pere",
        "bjorn",
        "ludwig",
        "heinrich",
        "heinz",
        "salve",
        "reyes",
        "maris",
        "riza",
        "mica",
        "vice",
        "ang",
        "an",
        "pa",
        "myk",
        "madz",
        "nix",
        "reg",
        "rej",
        "nic",
        "nik",
        "dimas",
        "naufal",
        "aditya",
        "rahmat",
        "rashid",
        "reza",
        "samir",
        "asad",
        "anwar",
        "aziz",
        "kamal",
        "karim",
        "faris",
        "ferdy",
        "nam",
        "alter",
        "just",
        "tin",
        "mikee",
    }
)

# Two-letter givens kept only if in this set (e.g. Bo, Yu).
_ALLOW_LEN2_CF: frozenset[str] = frozenset({"bo", "cy", "ty", "yu", "ky", "ai", "jc"})

_INITIALISM_CF: frozenset[str] = frozenset(
    {"cj", "mj", "aj", "rj", "ej", "pj", "jb", "jj", "tj", "lj", "jl"}
)

_DROP_SURNAME_CF: frozenset[str] = frozenset(
    {
        "mae",
        "marie",
        "joy",
        "ann",
        "anne",
        "grace",
        "rose",
        "jane",
        "kim",
        "may",
        "john",
        "nicole",
        "david",
        "manuel",
    }
)

# Pre-2025 pool frequency order (very → common → mid → rare), minus bad tokens above.
_PH_SURNAME_LEGACY_ORDER: tuple[str, ...] = (
    "Garcia",
    "Santos",
    "Reyes",
    "Cruz",
    "Mendoza",
    "Lopez",
    "Ramos",
    "Fernandez",
    "Gonzales",
    "Tan",
    "Perez",
    "Flores",
    "Rodríguez",
    "Sanchez",
    "Bautista",
    "Villanueva",
    "Martínez",
    "De Guzman",
    "Lim",
    "Lee",
    "Rivera",
    "Castillo",
    "Torres",
    "Hernandez",
    "Castro",
    "Gomez",
    "Santiago",
    "Ramirez",
    "Aquino",
    "Jimenez",
    "De Leon",
    "Morales",
    "Francisco",
    "Tolentino",
    "Gutierrez",
    "Gonzalez",
    "Diaz",
    "Chua",
    "Mercado",
    "Sy",
    "Soriano",
    "Miranda",
    "Padilla",
    "Go",
    "Alvarez",
    "Navarro",
    "Marquez",
    "Romero",
    "Aguilar",
    "Dizon",
    "Enriquez",
    "Ruiz",
    "Valdez",
    "Martin",
    "Moreno",
    "Pineda",
    "Pascual",
    "Domingo",
    "Chan",
    "Angeles",
    "Bernardo",
    "Javier",
    "Ferrer",
    "Rosales",
    "Sarmiento",
    "Ocampo",
    "Velasco",
    "Salazar",
    "Salvador",
    "Manalo",
    "Alcantara",
    "Ong",
    "Dy",
    "Evangelista",
    "Muñoz",
    "Mariano",
    "Ignacio",
    "Cortez",
    "Yu",
    "Cabrera",
    "Corpuz",
    "Concepcion",
    "Suarez",
    "Ortiz",
)

_POOL_META_KEYS = (
    "tier_probs",
    "middle_name_prob",
    "compound_surname_prob",
    "surname_connector",
)


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "").strip())


def _strip_marks(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _norm_key(s: str) -> str:
    return _strip_marks(_nfc(s)).casefold()


_SURNAME_LEGACY_INDEX: dict[str, int] = {
    _norm_key(x): i for i, x in enumerate(_PH_SURNAME_LEGACY_ORDER)
}


def _valid_token(n: str) -> bool:
    if not n or len(_nfc(n)) < 2:
        return False
    for part in re.split(r"[\s–-]", n.replace("–", "-")):
        if not part:
            continue
        if not all((c.isalpha() or c in "'.-" + "´") for c in part):
            return False
    return True


def _flatten_tiered(d: dict[str, list]) -> list[str]:
    out: list[str] = []
    for t in _TIER_ORDER:
        for x in d.get(t) or []:
            if isinstance(x, str):
                out.append(x)
    return out


def _identity_rank_from_raw(gm: dict) -> dict[str, float]:
    """norm_key(repaired) -> tier band (0…3). Same band lets regional boosts reorder."""
    id_rank: dict[str, float] = {}
    for tier in _TIER_ORDER:
        band = float(_TIER_RANK[tier])
        for raw in gm.get(tier) or []:
            if not isinstance(raw, str):
                continue
            s = _nfc(raw)
            cf = _norm_key(s)
            if cf in _REPAIR_CF:
                cf = _norm_key(_REPAIR_CF[cf])
            id_rank[cf] = min(id_rank.get(cf, 1e9), band)
    return id_rank


def _clean_givens_male(
    raw_flat: list[str], id_rank: dict[str, float]
) -> tuple[list[str], dict[str, str]]:
    chosen: dict[str, str] = {}
    for raw in raw_flat:
        s0 = _nfc(raw)
        if not s0:
            continue
        cf = _norm_key(s0)
        if cf in _DROP_GIVEN_CF:
            continue
        if cf in _REPAIR_CF:
            s0 = _nfc(_REPAIR_CF[cf])
            cf = _norm_key(s0)
        if cf in _INITIALISM_CF:
            continue
        if len(cf) == 2 and cf not in _ALLOW_LEN2_CF:
            continue
        if not _valid_token(s0):
            continue
        if cf not in chosen or len(s0) >= len(chosen[cf]):
            chosen[cf] = s0

    def neutral_key(display: str) -> tuple[float, str]:
        ik = _norm_key(display)
        return (id_rank.get(ik, 9999.0), display.casefold())

    ordered = sorted(chosen.values(), key=neutral_key)
    return ordered, chosen


def _clean_surnames(raw_flat: list[str]) -> list[str]:
    """Dedupe, drop junk, sort by legacy PH frequency then stable name."""
    seen: dict[str, str] = {}
    for raw in raw_flat:
        s0 = _nfc(raw)
        if not s0:
            continue
        cf = _norm_key(s0)
        if cf in _DROP_SURNAME_CF:
            continue
        if len(cf) < 2:
            continue
        if not _valid_token(s0):
            continue
        if cf not in seen or len(s0) >= len(seen[cf]):
            seen[cf] = s0

    def sur_key(display: str) -> tuple[int, str]:
        ik = _norm_key(display)
        return (_SURNAME_LEGACY_INDEX.get(ik, 10_000), display.casefold())

    return sorted(seen.values(), key=sur_key)


def _tier_list(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def _rank_for_pool(names: list[str], id_rank: dict[str, float], boost_cf: frozenset[str]) -> list[str]:
    def k(n: str) -> tuple[float, int, str]:
        cf = _norm_key(n)
        br = id_rank.get(cf, 9999.0)
        boost_hit = 1 if cf in boost_cf else 0
        # Stronger regional names sort earlier inside the same source tier band.
        return (br, -boost_hit, cf)

    return sorted(names, key=k)


def main() -> None:
    country = json.loads(_COUNTRY.read_text(encoding="utf-8"))
    tag_m = json.loads(_TAG.read_text(encoding="utf-8"))
    vis_m = json.loads(_VIS.read_text(encoding="utf-8"))

    gm = country["given_names_male"]
    id_rank = _identity_rank_from_raw(gm)
    flat_m = _flatten_tiered(gm)

    ordered_m, _ = _clean_givens_male(flat_m, id_rank)
    tier_country = _tier_list(ordered_m)

    tag_order = _rank_for_pool(ordered_m, id_rank, _TAGALOG_BOOST_CF)
    vis_order = _rank_for_pool(ordered_m, id_rank, _VISAYAN_BOOST_CF)

    sur_flat = _flatten_tiered(country["surnames"])
    ordered_sur = _clean_surnames(sur_flat)
    tier_sur = _tier_list(ordered_sur)

    country["given_names_male"] = tier_country
    country["surnames"] = tier_sur

    tag_m["given_names_male"] = _tier_list(tag_order)
    vis_m["given_names_male"] = _tier_list(vis_order)
    tag_m["surnames"] = tier_sur
    vis_m["surnames"] = tier_sur

    for pool in (tag_m, vis_m):
        for k in _POOL_META_KEYS:
            if k in country:
                pool[k] = country[k]

    _COUNTRY.write_text(
        json.dumps(country, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _TAG.write_text(json.dumps(tag_m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _VIS.write_text(
        json.dumps(vis_m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(
        f"Male givens: {len(ordered_m)}; surnames: {len(ordered_sur)} "
        f"(tiers vc+co+mid+rare counts: "
        f"{len(tier_country['very_common'])},{len(tier_country['common'])},"
        f"{len(tier_country['mid'])},{len(tier_country['rare'])})"
    )


if __name__ == "__main__":
    main()
