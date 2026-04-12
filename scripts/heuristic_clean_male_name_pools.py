#!/usr/bin/env python3
"""
Heuristic cleanup of country_*.json and custom_*.json name pools (male-oriented).

Removes from given_names_male / surnames:
 1) Junk: placeholders, digits, non-Latin tokens, obvious English dictionary words, bad punctuation
 2) Common female given names (and Japan-leaning romanizations in JPN pool)
 3) Implausible leakage: e.g. Polish -ska/-cka surnames (female forms), Icelandic dóttir patronymics

Skips: data/name_pools/old/, data/name_pools/_backup*/

Backs up changed files to data/name_pools/_backup_heuristic_male_clean/<filename>
Writes report to reports/heuristic_male_clean/summary.json

Run from repo root: python scripts/heuristic_clean_male_name_pools.py
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from name_pool_text import canon_name, is_plausible_token  # noqa: E402
from utils.name_data import NAME_POOL_TIER_KEYS  # noqa: E402

NAME_POOLS_DIR = ROOT / "data" / "name_pools"
BACKUP_DIR = NAME_POOLS_DIR / "_backup_heuristic_male_clean"
REPORT_DIR = ROOT / "reports" / "heuristic_male_clean"

TIERS = NAME_POOL_TIER_KEYS

PLACEHOLDERS = frozenset(
    {
        "unknown",
        "test",
        "example",
        "sample",
        "n/a",
        "none",
        "null",
        "tbd",
        "todo",
        "xxx",
        "name",
        "surname",
        "firstname",
        "lastname",
        "male",
        "female",
        "deceased",
        "anonymous",
    }
)

# Whole-string match (casefold) — scraper / column-header junk only (avoid real given names
# like An, Son, May, Will, Can, Kim, Rose, King, …).
ENGLISH_JUNK = frozenset(
    {
        "the",
        "and",
        "or",
        "of",
        "to",
        "for",
        "from",
        "with",
        "without",
        "unknown",
        "other",
        "same",
        "different",
        "total",
        "average",
        "percent",
        "number",
        "data",
        "list",
        "table",
        "figure",
        "page",
        "vol",
        "volume",
        "edition",
        "copyright",
        "reserved",
        "rights",
        "inc",
        "ltd",
        "llc",
        "company",
        "street",
        "road",
        "avenue",
        "lane",
        "drive",
        "po",
        "box",
        "apt",
        "unit",
        "building",
        "floor",
        "room",
        "city",
        "town",
        "state",
        "county",
        "region",
        "country",
        "nation",
        "world",
        "mr",
        "mrs",
        "ms",
        "miss",
        "dr",
        "prof",
        "sir",
        "lady",
        "lord",
        "captain",
        "major",
        "general",
        "colonel",
        "private",
        "soldier",
        "baby",
        "child",
        "daughter",
        "father",
        "mother",
        "brother",
        "sister",
        "husband",
        "wife",
        "widow",
        "married",
        "single",
        "divorced",
        "living",
        "dead",
        "note",
        "notes",
        "ref",
        "source",
        "see",
        "year",
        "years",
        "age",
        "aged",
        "born",
        "birth",
        "death",
        "died",
    }
)

# Multi-word entries: drop if any token is a clear female given (compound first names)
# (Avoid scanning ENGLISH_JUNK per-token — breaks "An", "Van", etc.)

# Common female given names (and frequent unisex-as-female in Western contexts) — casefold canonical
# Expanded but conservative on ambiguous (e.g. keep "Jean", "Francis" variants minimal)
FEMALE_GIVEN: Set[str] = {
    x.casefold()
    for x in """
Mary Patricia Linda Barbara Elizabeth Jennifer Maria Susan Margaret Dorothy Lisa Nancy Karen
Betty Helen Sandra Donna Carol Ruth Sharon Michelle Laura Sarah Kimberly Deborah Jessica Shirley
Cynthia Angela Melissa Brenda Amy Anna Rebecca Virginia Kathleen Pamela Martha Debra Amanda
Stephanie Carolyn Christine Marie Janet Catherine Frances Ann Joyce Diane Alice Julie Heather
Teresa Doris Gloria Evelyn Cheryl Mildred Katherine Joan Ashley Judith Rose Janice Kelly
Nicole Judy Christina Kathy Theresa Beverly Denise Tammy Irene Jane Lori Rachel Marilyn
Kathryn Louise Sara Anne Jacqueline Wanda Bonnie Julia Ruby Tina Phyllis Norma Paula Diana Annie
Lillian Emily Peggy Crystal Gladys Rita Dawn Florence Megan Lauren Emma Olivia Sophia
Isabella Mia Charlotte Amelia Harper Evelyn Abigail Emily Ella Madison Scarlett Victoria Grace
Chloe Camila Penelope Layla Zoe Nora Lily Eleanor Hannah Lillian Addison Aubrey Ellie
Stella Natalie Leah Hazel Violet Aurora Savannah Audrey Brooklyn Bella Clara Skylar Lucy
Paisley Everly Anna Caroline Genesis Aaliyah Kinsley Allison Maya Willow Naomi Elena
Sarah Hannah Brianna Hailey Alexa Maria Vanessa Natalie Jasmine Isabelle Kylie Makayla
Gabriella Autumn Ariana Payton Ruby Sophie Sydney Bailey Jenna Destiny Shelby
Kaitlyn Brooke Paige Trinity Lydia Kendall Ryleigh Teagan
Fatima Aisha Zainab Mariam Khadija Amira Yasmin Layla Hana Noor Salma Samira Nadia Leila
Zahra Safiya Iman Hanan Rania Dina Lina Maha Huda Souad Noura Farah Yasmeen
Ines Carmen Rosa Lucia Pilar Dolores Mercedes Angeles Cristina Beatriz Silvia Marta Elena
Paula Raquel Monica Irene Rocio Teresa Laura Sofia Martina Julia Alba Carla Sara
Nina Greta Heidi Ingrid Ursula Petra Sabine Monika Birgit Karin Susanne Angelika
Chiara Giulia Francesca Valentina Alessia Martina Elena Serena Elisa Giorgia Beatrice
Svetlana Olga Tatiana Irina Natalia Marina Yulia Oksana Galina Ludmila Vera Larisa Ekaterina
Anastasia Daria Polina Ksenia Irina Yelena
Priya Anjali Kavya Divya Meera Pooja Neha Riya Sneha Swati Shruti Kavita Radha Lakshmi Sita
Deepika Aishwarya Kareena Sonam Alia Kiara Disha Shraddha Anushka Kajol Madhuri Rekha Sushmita
Yuki Sakura Hana Mio Yui Riko Nanami Misaki Ayaka Nana Momoka Haruka Hinako Sayuri
""".split()
}

# Pools where English-style surnames are expected — do not strip FEMALE_GIVEN from surnames here.
FEMALE_SURNAME_LEAK_SKIP_CODES = frozenset(
    {"USA", "CAN", "AUS", "ENG", "SCO", "WAL", "NIR", "NZL", "IRL", "RSA", "JAM", "TTO", "BRB"}
)

# In other countries, female given names in the surname list are usually scraper leakage (e.g. Charlotte
# in Denmark). Allow these because they are also common real surnames in Anglophone / global usage.
FEMALE_ALLOWED_AS_SURNAME: Set[str] = {
    x.casefold()
    for x in """
Rose Kelly Morgan Jordan Taylor Madison Riley Avery Jamie Casey Payton Reese
Lynn Lee Ann Anne Marie Mary Jean Joan Alice Joyce Carol Diane Judith Frances
Hope Faith Grace Joy April May June Summer Autumn Winter
Bailey Hunter Parker Spencer Carson Whitney Haley Courtney Lindsay Tracy Stacy
Mackenzie Mckenna Kerry Carey Jody Virginia Georgia Carolina
Maria Elena Sara Nina Nora Iris Ruth Ivy Ada Ida Edna Ella Claire Sage Reed Page
Barry Terry Perry Murray Stanley Shirley Beverly Holly Molly Sally Peggy Jenny
Young Kennedy Victoria Andrea Anna
""".split()
}

# Japan: romanizations often used for girls / strong female lean in recent birth data — male pool cleanup
JPN_FEMALE_LEANING: Set[str] = {
    x.casefold()
    for x in """
Aoi Hina Yui Rin Sakura Hinata Mei Riko Nanami Misaki Ayaka Momoka Haruka Hinako
Sayuri Yume Koharu Ichika Honoka Kaede Momo Hikari Akari Nanoha Yuna
Miyu Nonoka Yuzu Saki Natsuki Kotomi Rina Maaya Shiori Kaori Tomomi Asuka
""".split()
}

# Pools where Icelandic patronymic filtering applies (surnames)
ISL_CODES = frozenset({"ISL"})

# Polish female surname endings (male pool should not use wife's line form as default)
POL_CODES = frozenset({"POL"})

_RE_BAD_CHARS = re.compile(r"[@#%&*+=|\\/<>{}[\]^_~`0-9]|\.com|\.org|http|www\.|mailto:", re.I)
_RE_MULTI_SPACE = re.compile(r"\s+")


def pool_files() -> List[Path]:
    out: List[Path] = []
    for pat in ("country_*.json", "custom_*.json"):
        for p in sorted(NAME_POOLS_DIR.glob(pat)):
            if "_backup" in p.parts:
                continue
            if "old" in p.parts:
                continue
            out.append(p)
    return out


def get_country_code(data: dict) -> str:
    return str(data.get("country_code") or "").strip().upper()


def normalize_key(s: str) -> str:
    return canon_name(s).casefold()


def should_drop_givens_male(name: str, *, country_code: str, pool_id: str) -> Optional[str]:
    raw = name.strip()
    if not raw:
        return "empty"
    if _RE_BAD_CHARS.search(raw):
        return "bad_chars_or_url"
    if not is_plausible_token(raw):
        return "not_latin_plausible"
    cf = normalize_key(raw)
    if cf in PLACEHOLDERS:
        return "placeholder"
    if cf in ENGLISH_JUNK:
        return "english_junk_word"
    parts = _RE_MULTI_SPACE.split(raw.strip())
    if len(parts) > 1:
        for tok in parts:
            if normalize_key(tok) in FEMALE_GIVEN:
                return "female_token_in_compound"
    if cf in FEMALE_GIVEN:
        return "female_given"
    if country_code == "JPN" and cf in JPN_FEMALE_LEANING:
        return "jpn_female_leaning"
    return None


def should_drop_surname(name: str, *, country_code: str) -> Optional[str]:
    raw = name.strip()
    if not raw:
        return "empty"
    if _RE_BAD_CHARS.search(raw):
        return "bad_chars_or_url"
    if not is_plausible_token(raw):
        return "not_latin_plausible"
    cf = normalize_key(raw)
    if cf in PLACEHOLDERS:
        return "placeholder"
    # Female given names mis-tagged as surnames (e.g. Charlotte in Denmark). Skip for Anglophone /
    # diaspora pools where the same strings are often real surnames.
    if country_code not in FEMALE_SURNAME_LEAK_SKIP_CODES:
        if cf in FEMALE_GIVEN and cf not in FEMALE_ALLOWED_AS_SURNAME:
            return "female_given_surname_leak"
    # Do not apply ENGLISH_JUNK to surnames — many tokens are real surnames (King, Lane, Street, …).
    # Icelandic matronymic (female line)
    if country_code in ISL_CODES:
        low = raw.casefold()
        if low.endswith("dóttir") or low.endswith("dottir"):
            return "isl_dottir"
    # Polish feminine surname forms
    if country_code in POL_CODES:
        low = raw.casefold()
        if len(low) >= 4 and (low.endswith("ska") or low.endswith("cka")):
            return "pol_feminine_surname"
    # Czech/Slovak -ová (ASCII ova common in transliteration)
    if country_code in frozenset({"CZE", "SVK"}):
        low = raw.casefold()
        if len(low) >= 5 and low.endswith("ova") and not low.endswith("nova"):
            # avoid Mendoza-style false positives: Czech female surnames often Consonant+ova
            if re.search(r"[bcdfghjklmnpqrstvwxz]ova$", low):
                return "cz_sk_feminine_ova"
    # Very short surnames: keep if passes plausible (is_plausible_token already len>=2)
    return None


def clean_tier_list(
    names: List[Any],
    *,
    field: str,
    country_code: str,
    pool_id: str,
    reasons: Dict[str, int],
    samples: Dict[str, List[str]],
) -> Tuple[List[str], int]:
    if not isinstance(names, list):
        return [], 0
    out: List[str] = []
    removed = 0
    for item in names:
        if not isinstance(item, str):
            removed += 1
            reasons["non_string"] += 1
            continue
        if field == "given":
            reason = should_drop_givens_male(item, country_code=country_code, pool_id=pool_id)
        else:
            reason = should_drop_surname(item, country_code=country_code)
        if reason:
            removed += 1
            reasons[reason] += 1
            if len(samples[reason]) < 8:
                samples[reason].append(item[:80])
            continue
        out.append(item)
    # dedupe preserve order (casefold)
    seen: Set[str] = set()
    deduped: List[str] = []
    for n in out:
        k = n.casefold()
        if k in seen:
            reasons["dedupe"] += 1
            removed += 1
            continue
        seen.add(k)
        deduped.append(n)
    return deduped, removed


def clean_pool(data: dict, pool_path: Path) -> Tuple[dict, Dict[str, Any]]:
    country_code = get_country_code(data)
    pool_id = str(data.get("pool_id") or pool_path.stem)
    stats: Dict[str, Any] = {
        "pool_id": pool_id,
        "country_code": country_code,
        "given_removed": 0,
        "surname_removed": 0,
        "reasons": defaultdict(int),
        "samples": defaultdict(list),
    }
    out = dict(data)

    for field_key, field_label in (("given_names_male", "given"), ("surnames", "surname")):
        tiered = out.get(field_key)
        if not isinstance(tiered, dict):
            continue
        new_tiered: Dict[str, List[str]] = {}
        for tier in TIERS:
            arr = tiered.get(tier) or []
            cleaned, nrem = clean_tier_list(
                arr,
                field=field_label,
                country_code=country_code,
                pool_id=pool_id,
                reasons=stats["reasons"],
                samples=stats["samples"],
            )
            new_tiered[tier] = cleaned
            if field_label == "given":
                stats["given_removed"] += nrem
            else:
                stats["surname_removed"] += nrem
        if any(tiered.get(t) != new_tiered.get(t) for t in TIERS):
            out[field_key] = new_tiered

    stats["reasons"] = dict(stats["reasons"])
    stats["samples"] = {k: v for k, v in stats["samples"].items()}
    return out, stats


def main() -> int:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    files = pool_files()
    summary: Dict[str, Any] = {"files": [], "totals": defaultdict(int)}

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
        except (json.JSONDecodeError, OSError) as e:
            summary["files"].append({"path": str(path.relative_to(ROOT)), "error": str(e)})
            continue

        if not isinstance(data, dict):
            continue

        new_data, stats = clean_pool(data, path)
        total_removed = stats["given_removed"] + stats["surname_removed"]
        if total_removed == 0:
            summary["files"].append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "skipped": True,
                    "pool_id": stats["pool_id"],
                }
            )
            continue

        # backup original once
        backup_path = BACKUP_DIR / path.name
        if not backup_path.is_file():
            shutil.copy2(path, backup_path)

        path.write_text(
            json.dumps(new_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        summary["totals"]["files_changed"] += 1
        summary["totals"]["given_removed"] += stats["given_removed"]
        summary["totals"]["surname_removed"] += stats["surname_removed"]

        summary["files"].append(
            {
                "path": str(path.relative_to(ROOT)),
                "pool_id": stats["pool_id"],
                "given_removed": stats["given_removed"],
                "surname_removed": stats["surname_removed"],
                "reasons": stats["reasons"],
                "samples": stats["samples"],
            }
        )

    summary["totals"] = dict(summary["totals"])
    (REPORT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Processed {len(files)} pool files.")
    print(f"Changed: {summary['totals'].get('files_changed', 0)}")
    print(f"Given removed: {summary['totals'].get('given_removed', 0)}")
    print(f"Surnames removed: {summary['totals'].get('surname_removed', 0)}")
    print(f"Report: {REPORT_DIR / 'summary.json'}")
    print(f"Backups (first run only per filename): {BACKUP_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
