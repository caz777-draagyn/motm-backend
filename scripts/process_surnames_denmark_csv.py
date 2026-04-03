#!/usr/bin/env python3
"""
Read SurnamesForTransfer.csv (surname,country), clean for Danish pool, dedupe,
tier 40 / 60 / 100 / rest, merge into data/name_pools/country_DEN.json (surnames only).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
CSV_PATH = _REPO / "SurnamesForTransfer.csv"
DEN_JSON = _REPO / "data" / "name_pools" / "country_DEN.json"

# Multi-word surnames kept (Danish / established forms in CSV)
ALLOW_SPACED = frozenset({"La Cour", "De Neergaard", "Von Eyben"})

# Junk, wrong script, celebrity noise, obvious non-name tokens
_REMOVE_A: set[str] = {
    "Danmark",
    "Denmark",
    "Copenhagen",
    "Design",
    "Media",
    "News",
    "Games",
    "Company",
    "Official",
    "Machine",
    "Magazine",
    "Music",
    "Blm",
    "Bieber",
    "Renèe",
    "Da Silva",
    "De Oliveira",
    "De Groot",
    "Van Hauen",
}

# Clear diaspora / English–world surnames not appropriate for a Danish-heritage pool
_REMOVE_A.update(
    [
        "Smith",
        "Jones",
        "Johnson",
        "Williams",
        "Brown",
        "Taylor",
        "Wilson",
        "Miller",
        "Moore",
        "Thomas",
        "Jackson",
        "White",
        "Harris",
        "Martin",
        "Thompson",
        "Garcia",
        "Martinez",
        "Robinson",
        "Clark",
        "Rodriguez",
        "Lewis",
        "Lee",
        "Walker",
        "Hall",
        "Allen",
        "Young",
        "King",
        "Wright",
        "Scott",
        "Torres",
        "Nguyen",
        "Hill",
        "Flores",
        "Green",
        "Adams",
        "Nelson",
        "Baker",
        "Rivera",
        "Campbell",
        "Mitchell",
        "Carter",
        "Roberts",
        "Gomez",
        "Phillips",
        "Evans",
        "Turner",
        "Diaz",
        "Parker",
        "Cruz",
        "Edwards",
        "Collins",
        "Reyes",
        "Stewart",
        "Morris",
        "Morales",
        "Murphy",
        "Cook",
        "Rogers",
        "Gutierrez",
        "Ortiz",
        "Morgan",
        "Cooper",
        "Peterson",
        "Bailey",
        "Reed",
        "Kelly",
        "Howard",
        "Ramos",
        "Cox",
        "Ward",
        "Richardson",
        "Watson",
        "Brooks",
        "Chavez",
        "Wood",
        "James",
        "Bennett",
        "Gray",
        "Mendoza",
        "Ruiz",
        "Hughes",
        "Price",
        "Alvarez",
        "Castillo",
        "Sanders",
        "Patel",
        "Myers",
        "Long",
        "Ross",
        "Foster",
        "Jimenez",
        "Powell",
        "Jenkins",
        "Perry",
        "Russell",
        "Sullivan",
        "Bell",
        "Coleman",
        "Butler",
        "Henderson",
        "Barnes",
        "Gonzales",
        "Fisher",
        "Vasquez",
        "Simmons",
        "Romero",
        "Jordan",
        "Patterson",
        "Alexander",
        "Hamilton",
        "Graham",
        "Reynolds",
        "Griffin",
        "Wallace",
        "Moreno",
        "West",
        "Cole",
        "Hayes",
        "Bryant",
        "Herrera",
        "Gibson",
        "Ellis",
        "Tran",
        "Medina",
        "Aguilar",
        "Stevens",
        "Murray",
        "Ford",
        "Castro",
        "Marshall",
        "Owens",
        "Harrison",
        "Fernandez",
        "Mcdonald",
        "Woods",
        "Washington",
        "Kennedy",
        "Wells",
        "Vargas",
        "Henry",
        "Chen",
        "Freeman",
        "Webb",
        "Tucker",
        "Guzman",
        "Burns",
        "Crawford",
        "Olson",
        "Simpson",
        "Porter",
        "Hunter",
        "Gordon",
        "Mendez",
        "Silva",
        "Shaw",
        "Snyder",
        "Mason",
        "Dixon",
        "Munoz",
        "Hunt",
        "Hicks",
        "Holmes",
        "Palmer",
        "Black",
        "Stone",
        "Andrews",
        "Fox",
        "Warren",
        "Mills",
        "Meyer",
        "Rice",
        "Robertson",
        "Dunn",
        "Daniels",
        "Stephens",
        "Hawkins",
        "Grant",
    ]
)

_REMOVE_A.update(
    [
        "Davies",
        "Davis",
        "Clarke",
        "Payne",
        "Pearce",
        "Duncan",
        "Barrett",
        "Griffiths",
        "Reid",
        "Costa",
        "Silva",
        "Santos",
        "Oliveira",
        "Carvalho",
        "Ferreira",
        "Martins",
        "Ramos",
        "Salazar",
        "Luna",
        "Nowak",
        "Hussain",
        "Shah",
        "Qureshi",
        "Malik",
        "Khalid",
        "Mustafa",
        "Mahmoud",
        "Ibrahim",
        "Osman",
        "Farooq",
        "Thapa",
        "Tesfay",
        "Ozturk",
        "Simsek",
        "Yildirim",
        "Zaman",
        "Yuksel",
        "Tahir",
        "Polat",
        "Kilic",
        "Said",
        "Amir",
        "Ansari",
        "Awad",
        "Aziz",
        "Azizi",
        "Habib",
        "Hamid",
        "Issa",
        "Jama",
        "Jeelani",
        "Ghorbani",
        "Hodzic",
        "Redzepi",
        "Georgiev",
        "Nikolov",
        "Stoyanov",
        "Novak",
        "Bjarnason",
        "Einarsson",
        "Gudmundsson",
        "Halldorsson",
        "Olafsson",
        "Kose",
        "Can",
        "Chan",
        "Jiang",
        "Lai",
        "Sun",
        "Tang",
        "Hou",
        "Long",
        # Given names mis-listed as surnames
        "Frank",
        "Rose",
        "Simon",
        "Louise",
        "Marie",
        "Paul",
        "Sofie",
    ]
)

REMOVE_EXACT = frozenset(_REMOVE_A)


def title_hyphenated(s: str) -> str:
    parts = s.split("-")
    out = []
    for p in parts:
        if not p:
            out.append(p)
            continue
        if p[0].islower():
            p = p[0].upper() + p[1:]
        out.append(p)
    return "-".join(out)


def normalize_surname(raw: str) -> str | None:
    s = (raw or "").strip()
    if not s:
        return None
    if " " in s and s not in ALLOW_SPACED:
        return None
    if s in REMOVE_EXACT:
        return None

    rep = {
        "Sorensen": "Sørensen",
        "Soerensen": "Sørensen",
        "Jorgensen": "Jørgensen",
        "Joergensen": "Jørgensen",
        "Ostergaard": "Østergaard",
        "Sondergaard": "Søndergaard",
        "Vestergard": "Vestergaard",
        "Nielson": "Nielsen",
        "Kjaer": "Kjær",
        "Elkjaer": "Elkjær",
        "Kjaergaard": "Kjærgaard",
    }
    if s in rep:
        s = rep[s]

    s = title_hyphenated(s)
    if s and s[0].islower():
        s = s[0].upper() + s[1:]

    if s in REMOVE_EXACT:
        return None
    return s


def main() -> None:
    if not CSV_PATH.is_file():
        print(f"Missing {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    rows: list[str] = []
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            if (row.get("country") or "").lower() != "denmark":
                continue
            name = normalize_surname(row.get("surname") or "")
            if not name:
                continue
            rows.append(name)

    seen: set[str] = set()
    out: list[str] = []
    for n in rows:
        k = n.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(n)

    ntot = len(out)
    vc = out[:40]
    co = out[40:100]
    mid = out[100:200]
    ra = out[200:]

    print(f"Total after clean+dedupe: {ntot}")
    print(f"very_common={len(vc)} common={len(co)} mid={len(mid)} rare={len(ra)}")

    data = json.loads(DEN_JSON.read_text(encoding="utf-8"))
    data["surnames"] = {
        "very_common": vc,
        "common": co,
        "mid": mid,
        "rare": ra,
    }
    DEN_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {DEN_JSON}")


if __name__ == "__main__":
    main()
