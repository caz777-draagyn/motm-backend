#!/usr/bin/env python3
"""
Remove tokens from given_names_male and surnames that are country / endonym /
major-city labels (e.g. Danmark, München, Århus), not plausible personal names.

Matching: NFC + casefold equals any pool country_name, EXTRA_GEO (endonyms /
exonyms), and TOKENS from name_pool_city_tokens (major cities).

ALLOWLIST: ALLOW_CASEFOLD (sovereign / exonym clashes) plus ALLOW_CITY (city =
common personal name).

Run: python scripts/remove_country_tokens_from_pools.py
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

from name_pool_city_tokens import TOKENS

_REPO = Path(__file__).resolve().parent.parent
POOL_DIR = _REPO / "data" / "name_pools"

# Native + common non-English exonyms (user nationality / free-text mistakes).
EXTRA_GEO: set[str] = {
    # --- already covered many English pool names; add what users type elsewhere ---
    "Danmark",
    "Deutschland",
    "Norge",
    "Sverige",
    "Suomi",
    "Hellas",
    "Ellada",
    "Ellas",
    "Polska",
    "Nederland",
    "Italia",
    "España",
    "Espana",
    "Österreich",
    "österreich",
    "Osterreich",
    "Schweiz",
    "Suisse",
    "Svizzera",
    "Česko",
    "Česká republika",
    "Ceska republika",
    "Türkiye",
    "Turkiye",
    # Baltic / Iceland / Faroes
    "Eesti",
    "Latvija",
    "Lietuva",
    "Ísland",
    "Føroyar",
    "Faroe",
    "Faroes",
    # German exonyms
    "Frankreich",
    "Spanien",
    "Italien",
    "Schweden",
    "Norwegen",
    "Dänemark",
    "Daenmark",
    "Niederlande",
    "Belgien",
    "Polen",
    "Ungarn",
    "Griechenland",
    "Tschechien",
    "Slowakei",
    "Rumänien",
    "Rumaenien",
    "Kroatien",
    "Serbien",
    "Bosnien",
    "Slowenien",
    "Russland",
    "Weissrussland",
    "Weißrussland",
    "Ukraine",
    "Türkei",
    "Turkei",
    "Saudi-Arabien",
    # Dutch
    "Frankrijk",
    "Duitsland",
    "Spanje",
    "Zweden",
    "Noorwegen",
    "Denemarken",
    "Griekenland",
    "Roemenie",
    "Roemenië",
    "Kroatië",
    "Tsjechië",
    "Slowakije",
    # French
    "Allemagne",
    "Espagne",
    "Italie",
    "Suède",
    "Suede",
    "Norvège",
    "Norvege",
    "Danemark",
    "Pays-Bas",
    "Belgique",
    "Pologne",
    "Roumanie",
    "Grèce",
    "Grece",
    "Tchéquie",
    "Tchequie",
    "Slovaquie",
    "Croatie",
    "Slovénie",
    "Slovenie",
    "Serbie",
    "Bosnie",
    "Turquie",
    "Arabie saoudite",
    # Spanish
    "Alemania",
    "Francia",
    "Suecia",
    "Noruega",
    "Dinamarca",
    "Países Bajos",
    "Paises Bajos",
    "Bélgica",
    "Belgica",
    "Polonia",
    "Grecia",
    "República Checa",
    "Republica Checa",
    "Chequia",
    "Eslovaquia",
    "Rumania",
    "Rumanía",
    "Croacia",
    "Eslovenia",
    "Ucrania",
    # Portuguese
    "Alemanha",
    "Franca",
    "Grécia",
    "Grecia",
    "Polónia",
    "Polonia",
    "Ucrânia",
    "Ucrania",
    # Italian
    "Germania",
    "Francia",
    "Spagna",
    "Svezia",
    "Norvegia",
    "Danimarca",
    "Paesi Bassi",
    "Belgio",
    "Turchia",
    "Repubblica Ceca",
    "Cechia",
    # Slavic (Latin script) / Balkans
    "Hrvatska",
    "Srbija",
    "Crna Gora",
    "Bosna",
    "Slovensko",
    "Slovenija",
    "Ukrajina",
    "Ukrayina",
    "Rossiya",
    "Rossija",
    "Rusija",
    "Belorus",
    "Bjelorus",
    "Shqipëria",
    "Shqiperia",
    "Magyarország",
    "Magyarorszag",
    "România",
    "Republika Srpska",
    # UK / Ireland endonyms (omit Alba — common given name; omit Britain — ALLOW)
    "Cymru",
    "Éire",
    "Eire",
    "Great Britain",
    "United Kingdom",
    # Misc ISO-style user text (omit US/UK — casefold clashes with common words)
    "Burma",
    "Myanmar",
    "Côte d'Ivoire",
    "Cote d'Ivoire",
    "Ivory Coast",
    "DR Congo",
    "DRC",
    "UAE",
    "USA",
}

# Keep even if equal to a sovereign state name (real people's names / surnames)
ALLOW_CASEFOLD: frozenset[str] = frozenset(
    {
        "georgia",
        "jordan",
        "chad",
        "israel",
        "india",
        "kenya",
        "cuba",
        "malta",
        "france",
        "england",
        "holland",
        "ireland",
        "scotland",
        "wales",
        "britain",
        "poland",
        "russia",
        "sweden",
        "norway",
        "finland",
        "germany",
        "spain",
        "italy",
        "china",
        # Avoid false positives vs exonyms (Franca, Usa, etc.)
        "franca",
        "usa",
    }
)

# City tokens we still ban but that match common given names / surnames
ALLOW_CITY: frozenset[str] = frozenset(
    {
        "paris",
        "milan",
        "milano",
        "florence",
        "firenze",
        "charlotte",
        "lincoln",
        "richmond",
        "alexandria",
        "sydney",
        "adelaide",
        "hamilton",
        "manchester",
        "birmingham",
        "kobe",
        "chandler",
        "gilbert",
        "irving",
        "garland",
        "reading",
        "verona",
        "cambridge",
        "oxford",
        # Frequent collisions with the global city list (surnames / given names)
        "medina",
        "hagen",
        "gent",
        "orlando",
        "wellington",
        "lund",
        "greve",
        "bergen",
        "lyon",
        "london",
        "phoenix",
        "dallas",
        "houston",
        "lima",
        "valencia",
        "palma",
        "vienna",
        "wien",
        "mesa",
        "henderson",
        "albuquerque",
        "cleveland",
        "stockton",
        "york",
        "braga",
        "salzburg",
        "graz",
        "linz",
        "ulm",
        "cordoba",
        "córdoba",
        "turku",
        "tampere",
        "lahti",
        "palermo",
        "roma",
        "ferrara",
        "pescara",
        "salerno",
        "messina",
        "napoli",
        "genova",
        "bari",
        "parma",
        "tours",
        "split",
        "zagreb",
        "prague",
        "praha",
        "brno",
        "samara",
        "basel",
        "tirana",
        "durres",
        "durrës",
        "nice",
        "orleans",
        "evora",
        "évora",
        "sofia",
        "biel",
        "breda",
        "essen",
        "kiel",
        "mainz",
        "metz",
        "nancy",
        "bern",
        "cardiff",
        "brighton",
        "leeds",
        "leicester",
        "liverpool",
        "coimbra",
        "aveiro",
        "oviedo",
        "vigo",
        "gijon",
        "bilbao",
        "malaga",
        "málaga",
        "alicante",
        "murcia",
        "zaragoza",
        "petersburg",
        "kazan",
        "rostov",
        "saratov",
        "ufa",
        "miami",
        "raleigh",
        "detroit",
        "baltimore",
        "portland",
        "sacramento",
        "fresno",
        "plano",
        "kano",
        "lagos",
        "cairo",
        "casablanca",
        "dakar",
        "durban",
        "havana",
        "caracas",
        "bogota",
        "bogotá",
        "medellín",
        "medellin",
        "monterrey",
        "guadalajara",
        "puebla",
        "tijuana",
        "doha",
        "dubai",
        "muscat",
        "manama",
        "basra",
        "kiev",
        "kyiv",
        "odessa",
        "odesa",
        "iasi",
        "patras",
        "belgrade",
        "beograd",
    }
)

ALLOW_ALL: frozenset[str] = ALLOW_CASEFOLD | ALLOW_CITY


def _nf(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "").strip())


def _cf(s: str) -> str:
    return _nf(s).casefold()


def _build_ban_set() -> set[str]:
    ban: set[str] = set()
    for fp in POOL_DIR.glob("country_*.json"):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        n = (data.get("country_name") or "").strip()
        if n:
            ban.add(_cf(n))
    for x in EXTRA_GEO:
        ban.add(_cf(x))
    for t in TOKENS:
        ban.add(_cf(t))
    return ban


def _scrub_list(arr: list, ban: set[str], allow: frozenset[str]) -> tuple[list, list[str]]:
    removed: list[str] = []
    out: list = []
    for item in arr:
        if not isinstance(item, str):
            out.append(item)
            continue
        cf = _cf(item)
        if cf and cf in ban and cf not in allow:
            removed.append(item)
            continue
        out.append(item)
    return out, removed


def scrub_geo_tokens_in_name_block(
    block: dict,
    ban: set[str],
    *,
    allow: frozenset[str] | None = None,
) -> list[tuple[str, str]]:
    """
    Mutate tier lists under a given_names_male- or surnames-style dict.
    Returns [(tier, original_token), ...] removed.
    """
    allow_f = allow if allow is not None else ALLOW_ALL
    log: list[tuple[str, str]] = []
    if not isinstance(block, dict):
        return log
    for tier in ("very_common", "common", "mid", "rare"):
        arr = block.get(tier)
        if not isinstance(arr, list):
            continue
        new_arr, rem = _scrub_list(arr, ban, allow_f)
        block[tier] = new_arr
        for r in rem:
            log.append((tier, r))
    return log


def main() -> None:
    ban = _build_ban_set()
    total_removed: list[tuple[str, str, str, str]] = []

    for fp in sorted(POOL_DIR.glob("country_*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Skip {fp.name}: {e}")
            continue
        changed = False
        for block in ("given_names_male", "surnames"):
            g = data.get(block)
            if not isinstance(g, dict):
                continue
            for tier in ("very_common", "common", "mid", "rare"):
                arr = g.get(tier)
                if not isinstance(arr, list):
                    continue
                new_arr, rem = _scrub_list(arr, ban, ALLOW_ALL)
                if rem:
                    g[tier] = new_arr
                    changed = True
                    for r in rem:
                        total_removed.append((fp.name, block, tier, r))
        if changed:
            fp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Removed {len(total_removed)} tokens across pools.")
    for row in total_removed:
        print(f"  {row[0]} [{row[1]}.{row[2]}] {row[3]!r}")


if __name__ == "__main__":
    main()
