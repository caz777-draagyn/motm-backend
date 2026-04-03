#!/usr/bin/env python3
"""
Clean country_POR male given names (Portugal-plausible), add ~150 names,
re-tier 20 / 30 / 50 / rest by estimated frequency.

Run: python scripts/refresh_portugal_given_names.py
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_POOL = _REPO / "data" / "name_pools" / "country_POR.json"

_REMOVE_CF: frozenset[str] = frozenset(
    {
        "antônio",
        "rubén",
        "levi",
        "little",
        "lil",
        "thiago",
        "matheus",
        "luiz",
        "juan",
        "javier",
        "javi",
        "alejandro",
        "pablo",
        "borja",
        "gonzalo",
        "guillermo",
        "enrique",
        "julián",
        "juan-carlos",
        "juan-josé",
        "pepe",
        "xavi",
        "miguel-angel",
        "hector",
        "ramón",
        "fran",
        "paco",
        "fabiano",
        "edward",
        "marc",
        "gabriele",
        "remi",
        "guido",
        "lionel",
        "teddy",
        "jonathan",
        "douglas",
        "cris",
        "anderson",
        "wilson",
        "christian",
        "mickael",
        "angel",
        "ângel",
        "adrián",
        "adrian",
        "martín",
        "francis",
        "dany",
        "gui",
        "alfonso",
        "pau",
        "santo",
        "toni",
        "marlon",
        "andrés",
        "hêrnani",
        "felipe",
        "dani",
        "edu",
        "manu",
        "rafa",
        "andres",
        "juan-jose",
        "julian",
        "ramon",
    }
)

# Preferred display for casefold key (dedupe Spanish/Brazilian spellings).
_PREF: dict[str, str] = {
    "nelson": "Nélson",
    "oscar": "Óscar",
    "vinicius": "Vinícius",
    "rubén": "Rúben",
    "antônio": "António",
    "joao-manuel": "João-Manuel",
    "leandro": "Leandro",
    "luis-filipe": "Luís-Filipe",
    "luis-carlos": "Luís-Carlos",
    "josé-luis": "José-Luís",
}


def _norm(s: str) -> str:
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


# Full rarity order (most common first). Duplicates removed when building list.
def _build_master_order() -> list[str]:
    blocks: list[list[str]] = [
        # Ultra-common (national)
        [
            "João",
            "Francisco",
            "Rodrigo",
            "Martim",
            "Santiago",
            "Afonso",
            "Tomás",
            "Gabriel",
            "Duarte",
            "Miguel",
            "Pedro",
            "Tiago",
            "Guilherme",
            "Lucas",
            "Lourenço",
            "Rafael",
            "Dinis",
            "Simão",
            "Gonçalo",
            "André",
            "Diogo",
            "Matias",
            "Bernardo",
            "Salvador",
            "Vicente",
            "Vasco",
            "Tomé",
            "Mateus",
            "Daniel",
            "David",
            "Ricardo",
            "Nuno",
            "Rui",
            "Paulo",
            "Bruno",
            "Carlos",
            "José",
            "António",
            "Manuel",
            "Mário",
            "Hugo",
            "Filipe",
            "Rúben",
            "Jorge",
            "Alexandre",
            "Fábio",
            "Marco",
            "Sérgio",
            "Fernando",
            "Vítor",
            "Henrique",
            "Leonardo",
            "Frederico",
            "Gustavo",
            "Samuel",
            "Artur",
            "Marcelo",
            "Eduardo",
            "Hélder",
            "Nélson",
            "Renato",
            "Cláudio",
            "Cristiano",
            "Emanuel",
            "Jaime",
            "Roberto",
            "Marcos",
            "Luís",
            "Óscar",
            "Ivo",
            "Joel",
            "Alberto",
            "Márcio",
            "Rogério",
            "Telmo",
            "Álvaro",
            "Joaquim",
            "Júlio",
            "Adriano",
            "Leandro",
            "Flávio",
            "César",
            "Edgar",
            "Vitório",
            "Sebastião",
            "Micael",
            "Victor",
            "Alex",
            "Diego",
            "Martin",
            "Hernâni",
            "Cristian",
            "Vinícius",
            "Manel",
            "Zé",
            "Tito",
            "Orlando",
            "Osvaldo",
            "Norberto",
            "Rodolfo",
            "Romeu",
            "Raúl",
            "Gil",
            "Gerson",
            "Ivan",
            "Isaac",
            "Ismael",
            "Iúri",
            "Augusto",
            "Domingos",
            "Humberto",
            "Octávio",
            "Alfredo",
            "Armindo",
            "Arlindo",
            "Celso",
            "Cristóvão",
            "Emílio",
            "Ernesto",
            "Eurico",
            "Gilberto",
            "Gualter",
            "Hélio",
            "Ilídio",
            "Josué",
            "Leonel",
            "Lino",
            "Lúcio",
            "Maurício",
            "Mílton",
            "Moisés",
            "Quim",
            "Sílvio",
            "Válter",
            "Xavier",
            "Élio",
            "Abel",
            "Abílio",
            "Adelino",
            "Adão",
            "Agostinho",
            "Amadeu",
            "Américo",
            "Amílcar",
            "Aníbal",
            "Arnaldo",
            "Aurélio",
            "Ângelo",
            "Baltazar",
            "Basílio",
            "Belchior",
            "Bento",
            "Boaventura",
            "Caetano",
            "Camilo",
            "Cândido",
            "Cipriano",
            "Clemente",
            "Cosme",
            "Custódio",
            "Damião",
            "Delfim",
            "Edmundo",
            "Egídio",
            "Elísio",
            "Estêvão",
            "Eugénio",
            "Eusébio",
            "Fausto",
            "Feliciano",
            "Felício",
            "Félix",
            "Fernão",
            "Firmino",
            "Florêncio",
            "Fortunato",
            "Frutuoso",
            "Gaspar",
            "Gaudêncio",
            "Genésio",
            "Gregório",
            "Hermínio",
            "Hermenegildo",
            "Hilário",
            "Hipólito",
            "Honório",
            "Isidro",
            "Jacinto",
            "Januário",
            "Jerónimo",
            "Jordão",
            "Lázaro",
            "Macário",
            "Marcelino",
            "Mariano",
            "Melchior",
            "Máximo",
            "Modesto",
            "Natanael",
            "Nestor",
            "Noé",
            "Olavo",
            "Osório",
            "Pascoal",
            "Patrício",
            "Paulino",
            "Plácido",
            "Polícarpo",
            "Querubim",
            "Quintino",
            "Quirino",
            "Ramiro",
            "Romão",
            "Romualdo",
            "Sabino",
            "Saturnino",
            "Serafim",
            "Sereno",
            "Severino",
            "Silvério",
            "Silvino",
            "Simplício",
            "Tadeu",
            "Teodoro",
            "Teotónio",
            "Timóteo",
            "Tristão",
            "Ulisses",
            "Urbano",
            "Valdemar",
            "Venâncio",
            "Veríssimo",
            "Viriato",
            "Vital",
            "Xisto",
            "Zacarias",
            "Aldo",
            "Anselmo",
            "Apolinário",
            "Aristides",
            "Belmiro",
            "Bonifácio",
            "Casimiro",
            "Cesário",
            "Cirilo",
            "Damiano",
            "Dário",
            "Dárcio",
            "Deodato",
            "Dionísio",
            "Diógenes",
            "Eleutério",
            "Elpídio",
            "Epifânio",
            "Ezequiel",
            "Fabrício",
            "Fidel",
            "Gentil",
            "Graciano",
            "Heitor",
            "Igor",
            "Isaltino",
            "Jair",
            "Narciso",
            "Nelito",
            "Olímpio",
            "Pio",
            "Umberto",
            "Venceslau",
            "Idalécio",
            "Aureliano",
            "Damásio",
            "Abelardo",
            "Acácio",
            "Acúlio",
            "Adolfo",
            "Adrião",
            "Albertino",
            "Alcino",
            "Alípio",
            "Almino",
            "Antero",
            "Argemiro",
            "Arménio",
            "Baldemar",
            "Bartolomeu",
            "Bernardino",
            "Brás",
            "Calisto",
            "Carmelo",
            "Dalmiro",
            "Elias",
            "Eufrásio",
            "Felisberto",
            "Firmo",
            "Heliodoro",
            "Horácio",
            "Inácio",
            "Jeremias",
            "Leocádio",
            "Ludgero",
            "Maximiliano",
            "Benjamim",
            "Jesus",
            "Martinho",
            "Sandro",
            "João-Pedro",
            "João-Miguel",
            "João-Carlos",
            "João-Tiago",
            "João-Filipe",
            "João-Nuno",
            "João-Paulo",
            "João-Luís",
            "José-Carlos",
            "José-Manuel",
            "José-Miguel",
            "José-Pedro",
            "José-António",
            "José-Alberto",
            "José-Luís",
            "José-Maria",
            "Luís-Miguel",
            "Luís-Pedro",
            "Luís-Filipe",
            "Nuno-Miguel",
            "Paulo-Jorge",
            "Pedro-Miguel",
            "Rui-Pedro",
            "Rui-Miguel",
            "Rui-Manuel",
            "Rui-Filipe",
            "Carlos-Alberto",
            "Mário-Rui",
            "Bruno-Miguel",
            "António-José",
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


def _clean_from_pool(flat: list[str]) -> dict[str, str]:
    """Accent-stripped identity key -> preferred display (Óscar vs Oscar merge)."""
    m: dict[str, str] = {}
    for raw in flat:
        n0 = _norm(raw)
        if not n0:
            continue
        ik = n0.casefold()
        if ik in _REMOVE_CF:
            continue
        cand = unicodedata.normalize("NFC", raw.strip())
        if not re.match(r"^[\w\-ÁÉÍÓÚÀÂÊÔÇÃÕáéíóúàâêôçãõ]+$", cand):
            continue
        if ik in _PREF:
            m[ik] = _PREF[ik]
        elif ik not in m:
            m[ik] = cand
        elif len(cand) > len(m[ik]):
            m[ik] = cand
    return m


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

    # Master order + additions; orphan = in file but not in master list (by identity key).
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
    g = data["given_names_male"]
    print(
        f"given names: {len(out)} "
        f"(very:{len(g['very_common'])} common:{len(g['common'])} "
        f"mid:{len(g['mid'])} rare:{len(g['rare'])})"
    )


if __name__ == "__main__":
    main()
