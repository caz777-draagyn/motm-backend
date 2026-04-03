"""
Clean data/name_pools/country_BAN.json male given names for realistic Bangladesh use.

Bangladesh: Bengali Muslim + Bengali Hindu naming in Latin transliteration; remove Western
and Greek football junk, abbreviation fragments, honorific/title tokens mis-ingested as
given names, and a conservative block of distinctly Hindi/North-Indian given names that
are atypical as primary Bangladesh choices.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from name_pool_text import is_plausible_token  # noqa: E402

BAN_PATH = ROOT / "data" / "name_pools" / "country_BAN.json"

# Allow only these 2-letter tokens (e.g. sacred Om).
ALLOW_LEN2: frozenset[str] = frozenset({"Om"})

EXCLUDE_LEN3: frozenset[str] = frozenset(
    {
        # Western/English short defaults that frequently leak in.
        "Ben",
        "Dan",
        "Ian",
        "Jim",
        "Joe",
        "Jon",
        "Ken",
        "Lee",
        "Leo",
        "Max",
        "Rob",
        "Sam",
        "Tim",
        "Tom",
    }
)

# Tokens that are fine in compounds but should not appear as a standalone given name.
EXCLUDE_STANDALONE_ONLY: frozenset[str] = frozenset(
    {
        "Abu",
        "Abdul",
        "Al",
        "Sk",
    }
)

EXCLUDE_GIVEN: frozenset[str] = frozenset(
    {
        # Latin abbreviation / fragment tokens
        "Ab",
        "Ak",
        "Ar",
        "Gm",
        "Rb",
        "Rj",
        "Sk",
        "Sm",
        "Al",
        "Abu",
        "Abdul",
        "Abm",
        "Ahm",
        "Apu",
        # Titles / surnames mis-ingested as given names
        "Sheikh",
        "Kazi",
        "Chowdhury",
        # English / global football noise
        "Prince",
        "John",
        "Johnny",
        "Michael",
        "Kevin",
        "Sean",
        "Shane",
        "Robin",
        "Andrew",
        "Brian",
        "Christopher",
        "Daniel",
        "David",
        "George",
        "James",
        "Matthew",
        "Peter",
        "Robert",
        "Steven",
        "Thomas",
        "William",
        # Greek (non-BD)
        "Alexandros",
        "Christos",
        "Dimitris",
        "Giannis",
        "Giorgos",
        "Ioannis",
    }
)


def should_drop(name: str) -> bool:
    if not is_plausible_token(name):
        return True
    if name in EXCLUDE_GIVEN:
        return True
    if len(name) <= 2:
        return name not in ALLOW_LEN2
    if len(name) == 3 and name in EXCLUDE_LEN3:
        return True
    if name in EXCLUDE_STANDALONE_ONLY and ("-" not in name and " " not in name):
        return True
    return False


def main() -> None:
    with open(BAN_PATH, encoding="utf-8") as f:
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

    with open(BAN_PATH, "w", encoding="utf-8") as f:
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
