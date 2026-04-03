"""
Clean data/name_pools/country_BRA.json male given names for realistic Brazilian use.

Pass 1: Latin plausibility, short-token rules, explicit junk / import exclusions.
Pass 2: Replace the rare tier with names that appear in Portugal or Argentina pools
        OR match Brazilian Portuguese morphological patterns (accents, -inho, -son,
        nh/lh, etc.). This cuts ~3k rare entries down to ~1.2k without discarding
        typical Brazilian -son / -inho inventions that are not listed in POR/ARG.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from name_pool_text import is_plausible_token  # noqa: E402

BRA_PATH = ROOT / "data" / "name_pools" / "country_BRA.json"
POR_PATH = ROOT / "data" / "name_pools" / "country_POR.json"
ARG_PATH = ROOT / "data" / "name_pools" / "country_ARG.json"

# Plausible 3-letter male given names used in Brazil.
ALLOW_LEN3: frozenset[str] = frozenset(
    {
        "Dan",
        "Dom",
        "Elo",
        "Fan",
        "Fio",
        "Gio",
        "Gil",
        "Gui",
        "Igo",
        "Ian",
        "Ivo",
        "Ito",
        "Jan",
        "Jim",
        "Jon",
        "Jey",
        "Kel",
        "Leo",
        "Nel",
        "Ney",
        "Pio",
        "Rey",
        "Rio",
        "Ron",
        "Rui",
        "Sam",
        "Sim",
        "Teo",
        "Tim",
        "Tom",
        "Ton",
        "Udo",
        "Ugo",
        "Wel",
        "Yan",
    }
)

# Junk, non–Latin American imports, geography-as-name, meme tokens.
EXCLUDE_GIVEN: frozenset[str] = frozenset(
    {
        "Muriel",
        "Giullian",
        "Kazuo",
        "Jotaro",
        "Kuro",
        "Kratos",
        "Ryo",
        "Kiim",
        "Tao",
        "Chao",
        "Yao",
        "Yam",
        "Hito",
        "Kaleo",
        "Kalel",
        "Furkan",
        "Khadim",
        "Irfan",
        "Houston",
        "Clinton",
        "Lebron",
        "Graham",
        "Gordon",
        "Ashton",
        "Declan",
        "Brendan",
        "Byron",
        "Logan",
        "Lennon",
        "Dragon",
        "Demon",
        "Iron",
        "Geo",
        "Kylian",
        "Krystian",
        "Goias",
        "Russo",
        "Castelo",
        "Camargo",
        "Gran",
        "Los",
        "Oso",
        "Amo",
        "Can",
        "Con",
        "Son",
        "Kim",
        "Mao",
        "Mon",
        "Nan",
        "Neo",
        "Matteus",
    }
)


def load_all_male(path: Path) -> set[str]:
    d = json.loads(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for tier in d["given_names_male"]:
        out.update(d["given_names_male"][tier])
    return out


def br_morphology_ok(name: str) -> bool:
    """Brazilian-typical spelling patterns (not exhaustive)."""
    nlow = name.lower()
    if re.search(r"[ãõçáéíóúâêôà]", name):
        return True
    if re.search(
        r"(son|inho|zinho|ão|aldo|ildo|evaldo|ilton|sson|orinho)$",
        nlow,
    ):
        return True
    if "nh" in nlow or "lh" in nlow:
        return True
    return False


def should_drop_pass1(name: str) -> bool:
    if not is_plausible_token(name):
        return True
    if name in EXCLUDE_GIVEN:
        return True
    if len(name) <= 2:
        return True
    if len(name) == 3 and name not in ALLOW_LEN3:
        return True
    return False


def main() -> None:
    por_names = load_all_male(POR_PATH)
    arg_names = load_all_male(ARG_PATH)
    por_arg = por_names | arg_names

    with open(BRA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    removed_p1: list[str] = []
    for tier in ("very_common", "common", "mid", "rare"):
        kept: list[str] = []
        for n in data["given_names_male"][tier]:
            if should_drop_pass1(n):
                removed_p1.append(n)
            else:
                kept.append(n)
        data["given_names_male"][tier] = kept

    # Pass 2: shrink rare using POR ∪ ARG + Brazilian morphology.
    rare_before = len(data["given_names_male"]["rare"])
    rare_kept = sorted(
        {
            n
            for n in data["given_names_male"]["rare"]
            if n in por_arg or br_morphology_ok(n)
        }
    )
    data["given_names_male"]["rare"] = rare_kept

    with open(BRA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    u1 = sorted(set(removed_p1))
    print(f"Pass 1: removed {len(removed_p1)} entries ({len(u1)} unique).")
    print(
        f"Pass 2: rare {rare_before} -> {len(rare_kept)} "
        f"(drop {rare_before - len(rare_kept)})."
    )
    for tier in ("very_common", "common", "mid", "rare"):
        print(f"  {tier}: {len(data['given_names_male'][tier])}")
    print("Pass 1 sample removed:", ", ".join(u1[:35]))
    if len(u1) > 35:
        print(f"  ... +{len(u1) - 35} more")


if __name__ == "__main__":
    main()
