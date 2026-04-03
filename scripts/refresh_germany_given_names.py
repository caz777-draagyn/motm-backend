#!/usr/bin/env python3
"""
Clean country_GER male given names for an ethnic-German-oriented master
ordering, dedupe orthography, re-tier 20/30/50/rest.

Run: python scripts/refresh_germany_given_names.py
Optional hard filter: python scripts/cleanse_germany_ethnic_givens.py
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_POOL = _REPO / "data" / "name_pools" / "country_GER.json"

# Exact raw tokens to drop (typos / unambiguously wrong for this pool).
_RAW_DROP: frozenset[str] = frozenset(
    {
        "Davidé",
        "Michèle",
    }
)

_REMOVE_CF: frozenset[str] = frozenset(
    {
        "nicola",
        "alexis",
        "nicki",
        "al",
        "pat",
        "ed",
        "nic",
        "mo",
        "bob",
        "will",
        "siggi",
        "pit",
        "oli",
        "bobby",
        "larry",
        "derek",
        "craig",
        "graham",
        "jeffrey",
        "gary",
        "ken",
        "phil",
        "jay",
    }
)

_PREF: dict[str, str] = {
    "oscar": "Oskar",
    "lucas": "Lukas",
    "mathias": "Matthias",
    "philip": "Philipp",
    "phillip": "Philipp",
    "philllip": "Philipp",
    "joerg": "Jörg",
    "juergen": "Jürgen",
    "søren": "Sören",
    "ralph": "Ralf",
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or "").strip())
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _valid_token(n: str) -> bool:
    if not n or len(n) < 2:
        return False
    for part in re.split(r"[\s–-]", n.replace("–", "-")):
        if not part:
            continue
        if not all((c.isalpha() or c in "'.") for c in part):
            return False
    return bool(n.replace("-", "").replace("–", ""))


def _tier(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }

_SHORTKEEP_CF: frozenset[str] = frozenset(
    {"jo", "uwe", "kay", "jan", "tom", "tim", "ben", "bo", "ari", "leo", "noa", "ian", "teo"}
)


def _clean_from_pool(flat: list[str]) -> dict[str, str]:
    """Identity key (accent-stripped) -> preferred display."""
    m: dict[str, str] = {}
    for raw in flat:
        rs = raw.strip()
        if rs in _RAW_DROP:
            continue
        n0 = _norm(rs)
        if not n0:
            continue
        ik = n0.casefold()
        if ik in _REMOVE_CF:
            continue
        if len(ik) <= 2 and ik not in _SHORTKEEP_CF:
            continue
        cand = unicodedata.normalize("NFC", rs.strip())
        if not _valid_token(cand):
            continue
        if ik in _PREF:
            m[ik] = _PREF[ik]
        elif ik not in m:
            m[ik] = cand
        elif len(cand) > len(m[ik]) or cand in _PREF.values():
            m[ik] = max((m[ik], cand), key=len)
    return m


def _build_master_order() -> list[str]:
    blocks: list[list[str]] = [
        [
            "Noah",
            "Leon",
            "Paul",
            "Ben",
            "Jonas",
            "Finn",
            "Elias",
            "Luca",
            "Luis",
            "Jakob",
            "Felix",
            "Henry",
            "Emil",
            "Anton",
            "Liam",
            "Theo",
            "Oskar",
            "Maximilian",
            "Lukas",
            "Alexander",
            "Michael",
            "Thomas",
            "Daniel",
            "David",
            "Christian",
            "Elias",
            "Andreas",
            "Stefan",
            "Sebastian",
            "Martin",
            "Markus",
            "Matthias",
            "Florian",
            "Tim",
            "Jan",
            "Oliver",
            "Julian",
            "Max",
            "Philipp",
            "Moritz",
            "Jakob",
            "Niklas",
            "Tom",
            "Simon",
            "Fabian",
            "Luis",
            "Leonard",
            "Aaron",
            "Samuel",
            "Jannik",
            "Erik",
            "Anton",
            "Benjamin",
            "Johannes",
            "Linus",
            "Kilian",
            "Jonathan",
            "Marlon",
            "Mats",
            "Mattis",
            "Justus",
            "Jannes",
            "Malte",
            "Karl",
            "Carl",
            "Oskar",
            "Bruno",
            "Hugo",
            "Gabriel",
            "Vincent",
            "Valentin",
            "Levi",
            "Tobias",
            "Sven",
            "Jens",
            "Robert",
            "Marcel",
            "Marc",
            "Patrick",
            "Dominik",
            "Nico",
            "Nils",
            "Lars",
            "Mika",
            "Kai",
            "Henrik",
            "Hendrik",
            "Robin",
            "Leopold",
            "Lorenz",
            "Magnus",
            "Theodor",
            "Frederik",
            "Frederic",
            "Raphael",
            "Till",
            "Torben",
            "Peer",
            "Ole",
            "Bastian",
            "Benedikt",
            "Bernhard",
            "Detlef",
            "Dietmar",
            "Dirk",
            "Dennis",
            "Carsten",
            "Karsten",
            "Christoph",
            "Christopher",
            "Stephan",
            "Steffen",
            "Thorsten",
            "Torsten",
            "Frank",
            "Wolfgang",
            "Jürgen",
            "Jörg",
            "Bernd",
            "Uwe",
            "René",
            "Holger",
            "Volker",
            "Manfred",
            "Manuel",
            "Rainer",
            "Heiko",
            "Pascal",
            "Joachim",
            "Hans",
            "Georg",
            "Günter",
            "Günther",
            "Gerhard",
            "Werner",
            "Klaus",
            "Franz",
            "Walter",
            "Horst",
            "Harald",
            "Norbert",
            "Herbert",
            "Ulrich",
            "Helmut",
            "Rolf",
            "Roland",
            "Rüdiger",
            "Reinhard",
            "Heinz",
            "Heinrich",
            "Wolfram",
            "Wilhelm",
            "Wilfried",
            "Ludwig",
            "Konrad",
            "Kurt",
            "Otto",
            "Josef",
            "Hubert",
            "Gregor",
            "Friedrich",
            "Ernst",
            "Erwin",
            "Erich",
            "Edmund",
            "Dieter",
            "Axel",
            "Armin",
            "Arne",
            "Achim",
            "André",
            "Björn",
            "Clemens",
            "Claus",
            "Damian",
            "Eike",
            "Elmar",
            "Emmanuel",
            "Ferdinand",
            "Fiete",
            "Fynn",
            "Gerrit",
            "Gerald",
            "Gernot",
            "Hannes",
            "Hanno",
            "Hagen",
            "Hartmut",
            "Hellmut",
            "Hermann",
            "Immanuel",
            "Ingmar",
            "Johann",
            "Jochen",
            "Klemens",
            "Lothar",
            "Maik",
            "Marvin",
            "Mirco",
            "Mirko",
            "Niclas",
            "Norbert",
            "Olaf",
            "Quirin",
            "Raimund",
            "Reiner",
            "Richard",
            "Roger",
            "Roman",
            "Ronald",
            "Ronny",
            "Ruben",
            "Sören",
            "Thilo",
            "Timo",
            "Tino",
            "Udo",
            "Ulf",
            "Uli",
            "Viktor",
            "Victor",
            "Wieland",
            "Zacharias",
            "Alfred",
            "Albert",
            "Artur",
            "Charlie",
            "Chris",
            "Denis",
            "Eddie",
            "Eric",
            "Fritz",
            "Harry",
            "Heiner",
            "Henning",
            "Ingo",
            "Kay",
            "Kevin",
            "Lutz",
            "Mark",
            "Marcus",
            "Mike",
            "Norman",
            "Olli",
            "Rico",
            "Sam",
            "Tony",
            "Niels",
            "Willi",
            "Arthur",
            "Adam",
            "Adrian",
            "Andy",
            "Anselm",
            "August",
            "Burkhard",
            "Cornelius",
            "Dietrich",
            "Eberhard",
            "Egon",
            "Engelbert",
            "Falk",
            "Fridolin",
            "Gottfried",
            "Guntram",
            "Hilmar",
            "Isidor",
            "Jannis",
            "Jonte",
            "Kaspar",
            "Lambert",
            "Ludger",
            "Meinhard",
            "Ottmar",
            "Quentin",
            "Reinhold",
            "Rupert",
            "Siegfried",
            "Sigmund",
            "Tassilo",
            "Theobald",
            "Tilman",
            "Valerian",
            "Veit",
            "Vinzenz",
            "Walther",
            "Wendelin",
        ],
        [
            "Hans-Peter",
            "Hans-Jürgen",
            "Hans-Jörg",
            "Karl-Heinz",
            "Karl-Otto",
        ],
    ]
    out: list[str] = []
    seen: set[str] = set()
    for block in blocks:
        for n in block:
            cf = n.casefold()
            if cf in seen:
                continue
            seen.add(cf)
            out.append(n)
    return out


def main() -> None:
    data = json.loads(_POOL.read_text(encoding="utf-8"))
    g = data["given_names_male"]
    flat: list[str] = []
    for tier in ("very_common", "common", "mid", "rare"):
        flat.extend(x for x in g[tier] if isinstance(x, str))

    kept_map = _clean_from_pool(flat)
    master = _build_master_order()
    master_ik = {_norm(n).casefold() for n in master}
    pos = {_norm(n).casefold(): i for i, n in enumerate(master)}

    final: list[str] = list(master)
    for ik, disp in kept_map.items():
        if ik not in master_ik:
            final.append(disp)

    final = sorted(
        final,
        key=lambda x: (pos.get(_norm(x).casefold(), 50_000), x.casefold()),
    )

    seen2: set[str] = set()
    out: list[str] = []
    for n in final:
        ik = _norm(n).casefold()
        if ik in seen2:
            continue
        seen2.add(ik)
        out.append(n)

    data["given_names_male"] = _tier(out)
    _POOL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    g2 = data["given_names_male"]
    print(
        f"given names: {len(out)} (very:{len(g2['very_common'])} common:{len(g2['common'])} "
        f"mid:{len(g2['mid'])} rare:{len(g2['rare'])})"
    )


if __name__ == "__main__":
    main()
