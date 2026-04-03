"""
Clean data/name_pools/country_COL.json male given names for Colombian-appropriate use.

Removes obvious junk (Spanish common words, animals, memes), mis-ingested surnames,
Portuguese–Brazil orthography typical of import football lists, and a few non–Americas
imports. Keeps Italian / English / local spellings (Jhon, Yeison, Brayan, etc.).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COL_PATH = ROOT / "data" / "name_pools" / "country_COL.json"

# Valid 3-letter tokens to keep when len(name) == 3.
ALLOW_LEN3: frozenset[str] = frozenset(
    {
        "Dan",
        "Gio",
        "Ian",
        "Ivo",
        "Jan",
        "Jey",
        "Jim",
        "Jon",
        "Leo",
        "Mel",
        "Rey",
        "Rio",
        "Ron",
        "Sam",
        "Teo",
        "Tim",
        "Tom",
        "Ugo",
        "Yan",
        "Yon",
        "Oto",
    }
)

# Longer names and 3-letter junk not covered by length rules.
EXCLUDE_GIVEN: frozenset[str] = frozenset(
    {
        # 2-letter / fragments
        "An",
        "Do",
        "Ro",
        "Él",
        # 3-letter junk (also caught by rule if not in ALLOW_LEN3)
        "Amo",
        "Bam",
        "Can",
        "Con",
        "Dey",
        "Don",
        "Dos",
        "Fco",
        "Geo",
        "Gon",
        "Hey",
        "Jos",
        "Key",
        "Lao",
        "Ley",
        "Los",
        "Mao",
        "Neo",
        "Ney",
        "Oso",
        "Ram",
        "Son",
        "Sos",
        "Tío",
        "Uno",
        "Yao",
        # Word-like / meme / myth / animals
        "Zeus",
        "Dios",
        "Perro",
        "Oso",
        "Gato",
        "Toro",
        "Narco",
        "Mango",
        "Draco",
        "Apolo",
        "Arcangel",
        "Frodo",
        "Bilbo",
        "Travel",
        "Dinero",
        "Clinton",
        "Washington",
        "Dragon",
        "Astro",
        "Como",
        "Dios",
        "Perro",
        "Gato",
        "Toro",
        "Narco",
        "Mango",
        "Furkan",
        "Yao",
        # Portuguese–Brazil spellings / football imports in this dataset
        "Diogo",
        "Matheus",
        "Mateus",
        "Rogério",
        "Gonçalo",
        "Hélio",
        "Willian",
        "Ederson",
        "Denilson",
        "Rivaldo",
        "Romario",
        "Ronaldo",
        "Domingos",
        "Afonso",
        "Frederico",
        # Mis-ingested surnames as given names
        "Castro",
        "Arias",
        "Guzman",
        "Guerrero",
        "Moreno",
        "Romero",
        # Slurs / nonsense labels
        "Indio",
        # Scandinavian orthography (outliers in this list)
        "Andersson",
        "Nilsson",
        # Odd dictionary / chat fragments
        "Sólo",
        "Memo",
        "Gato",
        "Tío",
        "Niño",
        "Los",
        "Geo",
        "Gon",
        "Grego",
        "Gordo",
        "Perro",
        "Oso",
        "Toro",
        "Gato",
        "Dios",
        "Zeus",
        "Draco",
        "Apolo",
        "Frodo",
        "Bilbo",
        "Travel",
        "Dinero",
        "Clinton",
        "Washington",
        "Dragon",
        "Astro",
        "Como",
        "Can",
        "Son",
        "Key",
        "Iron",
        "Geo",
        "Los",
        "Todo",
        "Toto",
        "Moreno",
        "Guerrero",
        "Guzman",
        "Arias",
        "Castro",
        "Romero",
        "Ronaldo",
        "Romario",
        "Rivaldo",
        "Matheus",
        "Mateus",
        "Rogério",
        "Diogo",
        "Gonçalo",
        "Willian",
        "Ederson",
        "Denilson",
        "Furkan",
        "Indio",
        "Narco",
        "Mango",
        "Frodo",
        "Bilbo",
        "Furkan",
        "Yao",
        # Residual junk / odd imports in rare tier
        "Latino",
        "Maestro",
        "Gran",
        "Rommel",
        "Enderson",
        "Tian",
        "Johnson",
        "Harrison",
        "Riley",
        "Morgan",
        "Stevenson",
        "Cameron",
    }
)


def should_drop(name: str) -> bool:
    if name in EXCLUDE_GIVEN:
        return True
    if len(name) <= 2:
        return True
    if len(name) == 3 and name not in ALLOW_LEN3:
        return True
    return False


def main() -> None:
    with open(COL_PATH, encoding="utf-8") as f:
        data = json.load(f)

    removed: list[str] = []
    for tier in ("very_common", "common", "mid", "rare"):
        kept: list[str] = []
        for n in data["given_names_male"][tier]:
            if should_drop(n):
                removed.append(n)
            else:
                kept.append(n)
        data["given_names_male"][tier] = kept

    with open(COL_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    u = sorted(set(removed))
    print(f"Removed {len(removed)} given-name entries ({len(u)} unique).")
    for tier in ("very_common", "common", "mid", "rare"):
        print(f"  {tier}: {len(data['given_names_male'][tier])}")
    print("Sample removed:", ", ".join(u[:45]))
    if len(u) > 45:
        print(f"  ... +{len(u) - 45} more")


if __name__ == "__main__":
    main()
