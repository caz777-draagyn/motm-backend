#!/usr/bin/env python3
"""
Build custom_afghanistan_dari.json from country_AFG.json by removing
Western / Latin American / obvious non-Dari given names and non-Afghan surnames.

Does not modify country_AFG.json.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
SRC = _REPO / "data" / "name_pools" / "country_AFG.json"
DST = _REPO / "data" / "name_pools" / "custom_afghanistan_dari.json"

# Casefold keys: common English / EU / Latin American given names found in the
# source merge (not appropriate as formal Dari primary given names).
_NON_DARI_GIVEN_RAW = """
ab al alex alexandre alan albert adrian anderson andre andré andrew andy angel anthony
aaron arthur ben benjamin bill bob brian bruno bryan caio carlos charles charlie
chris christian christopher dan danny daniel dave david diego douglas eduardo
edward eric felipe fernando flavio frank gabriel gary george guilherme gustavo
hans harry henry igor jack james jamie jason jay jeff jeffrey jeremy jim joao john
johnny jonathan jorge joseph josh joshua josé júlio justin joe jon jordan kelvin kevin leandro
leonardo leo lucas luis luís luiz marc marcelo marco márcio mark martin matheus
matt matthew max michael mike nick nathan paul patrick paulo pedro peter rafael
raymond ricardo richard rob robert rodrigo roman roy ryan sam samuel scott sean
sergio simon stephen steve steven sunny thiago thomas tim tom tony victor vincent
vinicius vítor will william alexander anil angel andy aaron brian bob charlie
christian danny dan dave douglas edward eric fernando george harry henry ian
jack jeff jim johnny justin kelvin ken kevin matthew michael nick nathan patrick
robin ryan samuel scott sean simon stephen steve steven thomas tim tom tony
vincent william ivan roman jeffrey jorge flavio márcio mehmet
"""

NON_DARI_GIVEN_CF: frozenset[str] = frozenset(
    w for w in _NON_DARI_GIVEN_RAW.split() if w.strip()
)

# Surnames clearly Portuguese/Brazilian or placeholder — not Afghan Dari pool
NON_AFGHAN_SURNAME_CF: frozenset[str] = frozenset(
    {
        "afghan",
        "oliveira",
        "santos",
        "silva",
        "souza",
        "costa",
        "gomes",
        "alves",
        "rodrigues",
        "ribeiro",
        "ferreira",
        "carvalho",
        "fernandes",
        "dias",
        "almeida",
        "marques",
        "lopes",
        "araújo",
        "araujo",
        "andrade",
        "ramos",
        "pereira",
        "nascimento",
        "martins",
        "rocha",
    }
)


def _nf(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "").strip())


def _tier_split(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def _flatten(block: dict) -> list[str]:
    out: list[str] = []
    for tier in ("very_common", "common", "mid", "rare"):
        arr = block.get(tier)
        if isinstance(arr, list):
            out.extend(_nf(x) for x in arr if isinstance(x, str) and _nf(x))
    return out


def _filter_given(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        raw = _nf(n)
        if not raw:
            continue
        cf = raw.casefold()
        if cf in NON_DARI_GIVEN_CF:
            continue
        # Honorific / title / clan token mis-filed as given
        if cf in ("khan", "haji", "king", "prince"):
            continue
        if cf in seen:
            continue
        seen.add(cf)
        out.append(raw)
    return out


def _filter_surnames(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        raw = _nf(n)
        if not raw:
            continue
        cf = raw.casefold()
        if cf in NON_AFGHAN_SURNAME_CF:
            continue
        if cf in seen:
            continue
        seen.add(cf)
        out.append(raw)
    return out


def main() -> None:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    dst_meta = json.loads(DST.read_text(encoding="utf-8"))

    given_flat = _flatten(src.get("given_names_male") or {})
    sur_flat = _flatten(src.get("surnames") or {})

    given_clean = _filter_given(given_flat)
    sur_clean = _filter_surnames(sur_flat)

    out: dict = {
        "pool_id": "custom_afghanistan_dari",
        "country_code": "AFG",
        "country_name": "Afghanistan Dari",
        "given_names_male": _tier_split(given_clean),
        "surnames": _tier_split(sur_clean),
        "tier_probs": dst_meta.get("tier_probs") or src.get("tier_probs"),
        "middle_name_prob": dst_meta.get("middle_name_prob", 0.08),
        "compound_surname_prob": dst_meta.get("compound_surname_prob", 0.04),
        "surname_connector": dst_meta.get("surname_connector", "-"),
    }

    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {DST.name}: {len(given_clean)} given, {len(sur_clean)} surnames (tiers 20/30/50/rest)")


if __name__ == "__main__":
    main()
