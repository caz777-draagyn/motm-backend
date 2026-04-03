"""
Build data/name_pools/country_TJK.json as a Tajik-plausible subset of country_AFG.

Tajikistan: Persian (Tajik) + Islamic naming, overlapping Afghan Persian/Tajik communities.
Excludes: Pashtun-specific tokens, Western/Portuguese given names common in Afghan sports data,
non–Central Asian surnames (e.g. Brazilian), and the token 'Afghan'.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AFG_PATH = ROOT / "data" / "name_pools" / "country_AFG.json"
OUT_PATH = ROOT / "data" / "name_pools" / "country_TJK.json"

# Given names: clearly Western / Lusophone / Anglo first names in this dataset (not Tajik-primary).
WESTERN_GIVEN_EXCLUDE: frozenset[str] = frozenset(
    {
        "Gabriel",
        "Lucas",
        "Felipe",
        "Rafael",
        "Bruno",
        "David",
        "John",
        "Daniel",
        "James",
        "Mark",
        "Michael",
        "Marcelo",
        "Matheus",
        "Rodrigo",
        "Thiago",
        "Victor",
        "Prince",
        "Paul",
        "Pedro",
        "Carlos",
        "Igor",
        "Alex",
        "Diego",
        "Alexandre",
        "Peter",
        "Robert",
        "Joao",
        "Hans",
        "Rob",
        "Leonardo",
        "Eduardo",
        "William",
        "Vinicius",
        "Leo",
        "Frank",
        "Sergio",
        "Marco",
        "Caio",
        "Patrick",
        "Anderson",
        "Steven",
        "Luiz",
        "Gustavo",
        "Guilherme",
        "Richard",
        "Ricardo",
        "Chris",
        "Arthur",
        "Kevin",
        "Thomas",
        "Harry",
        "George",
        "Fernando",
        "José",
        "Eric",
        "Douglas",
        "Ben",
        "Flavio",
        "Nathan",
        "Andrew",
        "Stephen",
        "Charles",
        "Christopher",
        "Scott",
        "Nick",
        "Marc",
        "Mike",
        "Justin",
        "Jonathan",
        "Jack",
        "Dave",
        "Samuel",
        "Josh",
        "Danny",
        "Dan",
        "Joe",
        "Ian",
        "Christian",
        "Roman",
        "Matt",
        "Ivan",
        "Andy",
        "Alan",
        "Tony",
        "Tim",
        "Ryan",
        "Martin",
        "Jeffrey",
        "Jason",
        "Henry",
        "Anil",
        "Angel",
        "Alexander",
        "Raymond",
        "Brian",
        "Bob",
        "Aaron",
        "Vincent",
        "Simon",
        "Roy",
        "Jordan",
        "Jon",
        "Jeremy",
        "Jay",
        "Zeeshan",
        "Will",
        "Jim",
        "Gary",
        "Bryan",
        "Benjamin",
        "Adrian",
        "Matthew",
        "Ken",
        "Joshua",
        "Joseph",
        "Johnny",
        "Jeff",
        "Jamie",
        "Charlie",
        "Albert",
        "Robin",
        "Edward",
        "Bill",
        "Kelvin",
        "Sean",
        "André",
        "King",
        "Oscar",
        "Tom",
        "Steve",
        "Sam",
        "Max",
        "Luís",
        "Vítor",
        "Márcio",
        "Júlio",
        "Paulo",
        "Carlos",
        "Pedro",
        "Caio",
        "Leandro",
        "Emal",
        "Mobin",
        "Nathan",
        "Ian",
        "Alan",
        "Tony",
        "Tim",
        "Jeff",
        "Jack",
        "Josh",
        "Joe",
        "Jim",
        "Gary",
        "Dave",
        "Dan",
        "Chris",
        "Ben",
        "Bob",
        "Bill",
        "Alex",
        "Aaron",
        "Jorge",
        "Anthony",
        "Sunny",
    }
)

# Pashtun-specific or strongly Pashtun-associated given names in this pool (poor Tajik-primary fit).
PASHTUN_GIVEN_EXCLUDE: frozenset[str] = frozenset(
    {
        "Mirwais",
        "Aimal",
        "Maiwand",
        "Sabawoon",
        "Khyber",
        "Baryalai",
        "Hewad",
        "Zalmai",
        "Wais",
        "Mehmet",
    }
)

# Tokens that are not plausible standalone given names for this generator.
GIVEN_EXCLUDE_MISC: frozenset[str] = frozenset({"Ab", "Al"})

# Surnames: Brazilian / generic Global South football noise; Pashtun tribal; dataset artifact "Afghan".
SURNAME_EXCLUDE: frozenset[str] = frozenset(
    {
        "Afghan",
        "Oliveira",
        "Santos",
        "Silva",
        "Momand",
        "Zadran",
        "Stanikzai",
        "Shinwari",
        "Wardak",
        "Kakar",
        "Souza",
        "Costa",
        "Gomes",
        "Alves",
        "Rodrigues",
        "Ferreira",
        "Ribeiro",
        "Mangal",
        "Zazai",
        "Noorzai",
        "Hotak",
        "Martins",
        "Carvalho",
        "Barakzai",
        "Niazi",
        "Niazai",
        "Fernandes",
        "Dias",
        "Almeida",
        "Marques",
        "Lopes",
        "Pereira",
        "Nascimento",
        "Araújo",
        "Andrade",
        "Rocha",
        "Ramos",
    }
)


def keep_given(name: str) -> bool:
    if (
        name in WESTERN_GIVEN_EXCLUDE
        or name in PASHTUN_GIVEN_EXCLUDE
        or name in GIVEN_EXCLUDE_MISC
    ):
        return False
    return True


def keep_surname(name: str) -> bool:
    return name not in SURNAME_EXCLUDE


def main() -> None:
    with open(AFG_PATH, encoding="utf-8") as f:
        afg = json.load(f)

    out: dict = {
        "pool_id": "country_TJK",
        "country_code": "TJK",
        "country_name": "Tajikistan",
        "given_names_male": {},
        "surnames": {},
    }

    for tier in ("very_common", "common", "mid", "rare"):
        raw = afg["given_names_male"][tier]
        out["given_names_male"][tier] = [n for n in raw if keep_given(n)]
        raw_s = afg["surnames"][tier]
        out["surnames"][tier] = [n for n in raw_s if keep_surname(n)]

    # Copy tier probs and name-generation params from existing TJK stub / AFG.
    out["tier_probs"] = afg["tier_probs"]
    out["middle_name_prob"] = afg["middle_name_prob"]
    out["compound_surname_prob"] = afg["compound_surname_prob"]
    out["surname_connector"] = afg["surname_connector"]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    for tier in ("very_common", "common", "mid", "rare"):
        print(
            f"{tier}: male_given={len(out['given_names_male'][tier])} "
            f"surnames={len(out['surnames'][tier])}"
        )


if __name__ == "__main__":
    main()
