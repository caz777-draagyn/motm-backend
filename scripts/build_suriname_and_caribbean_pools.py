#!/usr/bin/env python3
"""
Build believable male given-name pools for:
  - country_SUR (Suriname national: Dutch + Caribbean creole / maroon-adjacent; no Javanese/LatAm/Hindustani)
  - custom_suriname_hindustani (Indo-Surinamese / Hindustani)
  - custom_dutch_caribbean (ABC islands / Dutch Caribbean)
  - custom_french_caribbean (French Antilles / French Caribbean)

Goal: 250–300 *male given names* per pool with tiering 20/30/50/rest.
Surnames are also populated (smaller but believable) to keep pools functional.

Run:
  python scripts/build_suriname_and_caribbean_pools.py
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from name_pool_text import canon_name, is_plausible_token

REPO = Path(__file__).resolve().parent.parent
NAME_POOLS = REPO / "data" / "name_pools"


TIERS = ("very_common", "common", "mid", "rare")
TIER_BAND = {t: i for i, t in enumerate(TIERS)}


def flatten_names(pool: dict, key: str) -> list[str]:
    out: list[str] = []
    d = pool.get(key) or {}
    for t in TIERS:
        for x in d.get(t) or []:
            if isinstance(x, str):
                out.append(x)
    return out


@dataclass(frozen=True)
class Source:
    path: Path
    weight: float
    key: str  # "given_names_male" or "surnames"


def _ranked_unique_from_sources(
    sources: list[Source],
    *,
    limit: int,
    drop_cf: frozenset[str],
    allow_cf: frozenset[str] | None = None,
    allow_hyphen: bool = True,
) -> list[str]:
    scored: dict[str, tuple[float, str]] = {}

    for src in sources:
        data = json.loads(src.path.read_text(encoding="utf-8"))
        d = data.get(src.key) or {}
        idx = 0
        for tier in TIERS:
            band = float(TIER_BAND[tier])
            for raw in d.get(tier) or []:
                if not isinstance(raw, str):
                    continue
                idx += 1
                c = canon_name(raw)
                if not c or not is_plausible_token(c):
                    continue
                if not allow_hyphen and "-" in c:
                    continue
                cf = c.casefold()
                if cf in drop_cf:
                    continue
                if allow_cf is not None and cf not in allow_cf:
                    continue
                # Lower is better: tier band dominates, then position; source weight breaks ties.
                score = band * 10_000 + idx
                # weight: prefer higher weight sources slightly
                score -= min(0.9, max(0.0, src.weight)) * 100

                prev = scored.get(cf)
                if prev is None or score < prev[0]:
                    scored[cf] = (score, c)

    ordered = [v[1] for v in sorted(scored.values(), key=lambda x: (x[0], x[1].casefold()))]
    return ordered[:limit]


def tier(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


# Global drops (junk and obvious wrong-region givens).
DROP_GIVEN_CF: frozenset[str] = frozenset(
    {
        # junk
        "dad",
        "daddy",
        "baby",
        "babe",
        "king",
        "queen",
        "junior",
        "jr",
        "sr",
        "mr",
        "ms",
        "dr",
        "ii",
        "iii",
        "iv",
        # overly generic fragments / initials
        "al",
        "aj",
        "cj",
        "dj",
        "ej",
        "jj",
        "jr",
        "mj",
        "pj",
        "rj",
        "tj",
        # clearly non-name tokens seen in other pools
        "shop",
        "island",
    }
)

# Extra drops for Indo-Surinamese Hindustani pool: keep it ethnically Indian/Urdu/Hindi
# rather than pan-urban global/Christian anglophone.
DROP_HINDUSTANI_EXTRA_CF: frozenset[str] = frozenset(
    {
        "aaron",
        "adrian",
        "aiden",
        "alex",
        "anthony",
        "antonio",
        "benjamin",
        "brian",
        "carlos",
        "charles",
        "christian",
        "christopher",
        "daniel",
        "david",
        "dylan",
        "ethan",
        "gabriel",
        "george",
        "henry",
        "ian",
        "isaac",
        "jack",
        "jaden",
        "jayden",
        "jason",
        "jesus",
        "joel",
        "john",
        "jonathan",
        "joseph",
        "joshua",
        "justin",
        "kevin",
        "kyle",
        "liam",
        "louis",
        "lucas",
        "mark",
        "martin",
        "mason",
        "michael",
        "nicholas",
        "nigel",
        "noah",
        "nathan",
        "oliver",
        "oscar",
        "patrick",
        "paul",
        "peter",
        "rayan",
        "raymond",
        "richard",
        "robert",
        "ryan",
        "samuel",
        "sean",
        "shane",
        "simon",
        "stephen",
        "steven",
        "thomas",
        "victor",
        "vincent",
        "william",
        "zachary",
        "zack",
        "zach",
    }
)

DROP_SURNAME_CF: frozenset[str] = frozenset(
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
    }
)

# Common Muslim/Arabic-origin givens that are broadly used across many Suriname
# subgroups (so don't auto-strip them from national SUR just because they exist in India).
# Hindustani pool still uses India-only filtering; Javanese Surinamese use
# custom_indonesia_javanese — so country_SUR no longer keeps these on the national mix.
ISLAMIC_KEEP_CF: frozenset[str] = frozenset(
    {
        "muhammad",
        "muhamad",
        "mohammad",
        "mohamed",
        "muhammed",
        "mohammed",
        "ahmad",
        "ahmed",
        "achmad",
        "abdul",
        "abdullah",
        "ali",
        "ibrahim",
        "yusuf",
        "umar",
        "omar",
        "usman",
        "hassan",
        "hasan",
        "ismail",
        "amin",
    }
)

# Strip from country_SUR givens (Javanese/Hindustani heritage rows use their own pools).
SUR_NATIONAL_GIVEN_EXTRA_DROP_CF: frozenset[str] = frozenset(
    {
        # Islamic / Arabic (national pool = Dutch + creole + maroon)
        *ISLAMIC_KEEP_CF,
        "ridwan",
        "taufik",
        "maulana",
        "adhitya",
        "abdillah",
        "abdoel",
        "akhmad",
        "husein",
        "teguh",
        "afif",
        "yoga",
        "yogi",
        "yudi",
        "satria",
        "petrus",
        "gregorius",
        "antonius",
        "stefanus",
        "johanes",
        "paulus",
        # Indonesian / Malay spill (if any)
        "agus",
        "andi",
        "budi",
        "bayu",
        "rizki",
        "rizky",
        "aan",
        "dian",
        "hendra",
        "angga",
        "arief",
        "asep",
        "dimas",
        "eko",
        "joko",
        "ketut",
        "putra",
        "rizal",
        "heru",
        "heri",
        "dede",
        "dedi",
        "gede",
        "edi",
        "deni",
        "tri",
        "iwan",
        "rio",
        "agust",
        "adityo",
        "adik",
        "adis",
        "adly",
        "adriel",
        "adryan",
        "agan",
    }
)


def build() -> None:
    # Source pools available in-repo.
    p_sur = NAME_POOLS / "country_SUR.json"
    p_hind = NAME_POOLS / "custom_suriname_hindustani.json"
    p_dc = NAME_POOLS / "custom_dutch_caribbean.json"
    p_fc = NAME_POOLS / "custom_french_caribbean.json"

    ned = NAME_POOLS / "country_NED.json"
    fra = NAME_POOLS / "country_FRA.json"
    hai = NAME_POOLS / "country_HAI.json"
    tto = NAME_POOLS / "country_TTO.json"
    ind = NAME_POOLS / "country_IND.json"

    # Precompute India-given whitelist (keeps Hindustani pool ethnic).
    ind_data = json.loads(ind.read_text(encoding="utf-8"))
    ind_givens_cf = frozenset(canon_name(x).casefold() for x in flatten_names(ind_data, "given_names_male"))

    # Hindustani: India-only + tiny Indo-Caribbean assist, but *only* names that are in India list.
    hind_givens = _ranked_unique_from_sources(
        [
            Source(ind, 1.0, "given_names_male"),
            Source(tto, 0.6, "given_names_male"),
        ],
        limit=300,
        drop_cf=DROP_GIVEN_CF | DROP_HINDUSTANI_EXTRA_CF,
        allow_cf=ind_givens_cf,
    )
    # Hindustani surnames: use Indian surnames (country_IND) if present, else fallback to none.
    hind_surnames = _ranked_unique_from_sources(
        [
            Source(ind, 1.0, "surnames"),
            Source(tto, 0.3, "surnames"),
        ],
        limit=220,
        drop_cf=DROP_SURNAME_CF,
        allow_hyphen=False,
    )

    # Dutch Caribbean: NED + Caribbean anglophone influence (TTO) + Haiti small.
    dutchcar_givens = _ranked_unique_from_sources(
        [
            Source(ned, 1.0, "given_names_male"),
            Source(tto, 0.55, "given_names_male"),
            Source(hai, 0.20, "given_names_male"),
        ],
        limit=300,
        drop_cf=DROP_GIVEN_CF,
    )
    dutchcar_surnames = _ranked_unique_from_sources(
        [
            Source(ned, 1.0, "surnames"),
            Source(tto, 0.55, "surnames"),
            Source(hai, 0.20, "surnames"),
        ],
        limit=230,
        drop_cf=DROP_SURNAME_CF,
        allow_hyphen=False,
    )

    # French Caribbean: FRA + Haiti (strong creole reality) + small TTO.
    frenchcar_givens = _ranked_unique_from_sources(
        [
            Source(fra, 1.0, "given_names_male"),
            Source(hai, 0.8, "given_names_male"),
            Source(tto, 0.25, "given_names_male"),
        ],
        limit=300,
        drop_cf=DROP_GIVEN_CF,
    )
    frenchcar_surnames = _ranked_unique_from_sources(
        [
            Source(fra, 1.0, "surnames"),
            Source(hai, 0.8, "surnames"),
            Source(tto, 0.25, "surnames"),
        ],
        limit=230,
        drop_cf=DROP_SURNAME_CF,
        allow_hyphen=False,
    )

    # Suriname national: heavily Dutch + Afro-Caribbean creole / maroon-adjacent (HAI, TTO).
    # No Indonesia/Javanese (separate heritage + custom_indonesia_javanese), no LatAm spill,
    # no India/Hindustani (custom_suriname_hindustani). Islamic names belong in those lines.
    sur_indic_drop_cf = frozenset(x for x in ind_givens_cf if x not in ISLAMIC_KEEP_CF)
    sur_sources_g = [
        Source(ned, 1.0, "given_names_male"),
        Source(hai, 0.82, "given_names_male"),
        Source(tto, 0.78, "given_names_male"),
    ]
    sur_givens = _ranked_unique_from_sources(
        sur_sources_g,
        limit=300,
        drop_cf=DROP_GIVEN_CF
        | sur_indic_drop_cf
        | SUR_NATIONAL_GIVEN_EXTRA_DROP_CF,
    )
    sur_sources_s = [
        Source(ned, 1.0, "surnames"),
        Source(hai, 0.82, "surnames"),
        Source(tto, 0.78, "surnames"),
    ]
    sur_surnames = _ranked_unique_from_sources(
        sur_sources_s,
        limit=240,
        drop_cf=DROP_SURNAME_CF,
        allow_hyphen=False,
    )

    def _load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    sur = _load(p_sur)
    hind = _load(p_hind)
    dc = _load(p_dc)
    fc = _load(p_fc)

    sur["given_names_male"] = tier(sur_givens)
    sur["surnames"] = tier(sur_surnames)
    sur["pool_id"] = "country_SUR"

    hind["given_names_male"] = tier(hind_givens)
    hind["surnames"] = tier(hind_surnames)

    dc["given_names_male"] = tier(dutchcar_givens)
    dc["surnames"] = tier(dutchcar_surnames)

    fc["given_names_male"] = tier(frenchcar_givens)
    fc["surnames"] = tier(frenchcar_surnames)

    p_sur.write_text(json.dumps(sur, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    p_hind.write_text(json.dumps(hind, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    p_dc.write_text(json.dumps(dc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    p_fc.write_text(json.dumps(fc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _n(d: dict) -> int:
        return sum(len(d["given_names_male"][t]) for t in TIERS)

    def _sn(d: dict) -> int:
        return sum(len(d["surnames"][t]) for t in TIERS)

    print(
        f"SUR givens={_n(sur)} surnames={_sn(sur)} | "
        f"SUR_hind givens={_n(hind)} surnames={_sn(hind)} | "
        f"DutchCarib givens={_n(dc)} surnames={_sn(dc)} | "
        f"FrenchCarib givens={_n(fc)} surnames={_sn(fc)}"
    )


if __name__ == "__main__":
    build()
