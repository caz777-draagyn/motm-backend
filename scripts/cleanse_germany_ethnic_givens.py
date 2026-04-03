#!/usr/bin/env python3
"""
Remove non–ethnic-German signalling given names from country_GER (male givens only).
Keeps German / German-assimilated / biblical-International names typical for ethnic
German bearers; drops clearly Italian, French, Slavic, Turkish/Arabic, Anglo, etc.

Re-tiers 20 / 30 / 50 / rest preserving prior list order.

Run: python scripts/cleanse_germany_ethnic_givens.py
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_POOL = _REPO / "data" / "name_pools" / "country_GER.json"

# Polish-specific letters (distinct from German umlauts).
_POLISH_MARK = re.compile(r"[łąćęńśźżŁĄĆĘŃŚŹŻ]", re.UNICODE)

_DROP_CF: frozenset[str] = frozenset(
    {
        # Italian / Italo-Latin
        "matteo",
        "marco",
        "mario",
        "leonardo",
        "alessandro",
        "francesco",
        "giuseppe",
        "alessio",
        "antonio",
        "alberto",
        "carlo",
        "claudio",
        "domenico",
        "enrico",
        "fabio",
        "federico",
        "franco",
        "diego",
        "dario",
        "daniele",
        "edoardo",
        "gianluca",
        "giovanni",
        "lorenzo",
        "luigi",
        "massimo",
        "maurizio",
        "mauro",
        "paolo",
        "pietro",
        "riccardo",
        "roberto",
        "rocco",
        "salvatore",
        "sergio",
        "stefano",
        "vincenzo",
        "marcello",
        "enzo",
        "guido",
        "sandro",
        "angelo",
        # French / Walloon-style
        "luc",
        "louis",
        "pierre",
        "jean",
        "jacques",
        "julien",
        "olivier",
        "mathieu",
        "guillaume",
        "étienne",
        "etienne",
        "stéphane",
        "stephane",
        "christophe",
        "dominique",
        "philippe",
        "yves",
        "jérôme",
        "jerome",
        "françois",
        "francois",
        "gérard",
        "gerard",
        "maurice",
        "michel",
        "alexandre",
        "yannick",
        "cedric",
        "cédric",
        "fabrice",
        # compounds
        "jean-luc",
        "jean-pierre",
        # Dutch / Flemish signalling (less core German ethnic)
        "jeroen",
        "klaas",
        "henk",
        "jos",
        "bart",
        "piet",
        "han",
        "bas",
        # Nordic (keep Sven, Björn, Axel — core in DE; drop others)
        "morten",
        "rasmus",
        "lasse",
        "leif",
        "knut",
        "johan",
        "kalle",
        "nikolaj",
        "patrik",
        "lennart",
        "thor",
        "helge",
        "gunnar",
        "bo",
        # Slavic / East European (incl. German-spelled borrowings that read Slavic-first)
        "milan",
        "igor",
        "ivan",
        "vladimir",
        "miroslav",
        "stanislav",
        "janusz",
        "pawel",
        "piotr",
        "mateusz",
        "tomasz",
        "kamil",
        "marek",
        "marcin",
        "maciej",
        "jakub",
        "michal",
        "grzegorz",
        "bogdan",
        "petr",
        "pavel",
        "filip",
        "milos",
        "milosz",
        "nikola",
        "nicolai",
        "marian",
        "tomas",
        "rafael",
        "kristian",
        "kristof",
        "kriss",
        "kris",
        # Turkish / Arabic common-Muslim givens (non-ethnic-German focus)
        "mehmet",
        "mahmoud",
        "mohamed",
        "muhammad",
        "mustafa",
        "murat",
        "emre",
        "deniz",
        "kaan",
        "rayan",
        "ilyas",
        "ilias",
        "amir",
        "omar",
        # Anglo / Irish orthography clusters (not core German ethnicity)
        "brian",
        "james",
        "john",
        "johnny",
        "jonny",
        "anthony",
        "william",
        "joshua",
        "kenneth",
        "gordon",
        "stuart",
        "edward",
        "edwin",
        "charles",
        "bryan",
        "dustin",
        "sammy",
        "steve",
        "steven",
        "stevie",
        "lee",
        "rick",
        "rob",
        "roy",
        "jerry",
        "jeremy",
        "ken",
        "chuck",
        "danny",
        "gregory",
        "jacob",
        "toby",
        "scott",
        "derek",
        "gary",
        "larry",
        "randall",
        "randy",
        "oscar",
        # Spanish / Hispanic signalling
        "matias",
        "nicolas",
        "javier",
        "enrique",
        "juan",
        "pablo",
        "diego",
        "fernando",
        "ricardo",
        "cristian",
        "miguel",
        "gonzalo",
        "daniele",
        "dominic",
        "dominique",
        "stephen",
    }
)


def _norm_key(s: str) -> str:
    s = unicodedata.normalize("NFC", (s or "").strip())
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _tier(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def _drop_token(display: str) -> bool:
    raw = display.strip()
    if _POLISH_MARK.search(raw):
        return True
    ik = _norm_key(raw).casefold()
    if ik in _DROP_CF:
        return True
    for part in ik.replace("–", "-").split("-"):
        if part in _DROP_CF:
            return True
    return False


def main() -> None:
    data = json.loads(_POOL.read_text(encoding="utf-8"))
    g = data["given_names_male"]
    flat: list[str] = []
    for tier in ("very_common", "common", "mid", "rare"):
        flat.extend(x for x in g[tier] if isinstance(x, str))

    seen: set[str] = set()
    kept: list[str] = []
    removed = 0
    for n in flat:
        if _drop_token(n):
            removed += 1
            continue
        ik = _norm_key(n).casefold()
        if ik in seen:
            continue
        seen.add(ik)
        kept.append(n.strip())

    data["given_names_male"] = _tier(kept)
    _POOL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    g2 = data["given_names_male"]
    print(
        f"removed {removed} entries, kept {len(kept)} unique "
        f"(vc:{len(g2['very_common'])} c:{len(g2['common'])} "
        f"m:{len(g2['mid'])} r:{len(g2['rare'])})"
    )


if __name__ == "__main__":
    main()
