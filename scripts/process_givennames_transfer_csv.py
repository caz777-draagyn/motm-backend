#!/usr/bin/env python3
"""
Import givennamesForTransfer.csv into matching data/name_pools/country_*.json files
(`given_names_male` only).

**CSV columns:** `Name`, `Country` — `Country` must match `country_name` in a pool JSON
(case-insensitive), e.g. Albania → country_ALB.json.

Cleansing policy — **ethnic pool = credible local mainstream** (where configured):
- Global junk, country-specific quality frozensets, ethnic-mainstream frozensets (per country key),
  dedupe after normalize, spelling fixes.
- Countries **without** entries in ETHNIC_NON_MAINSTREAM / DISCARD_BY_COUNTRY still get:
  global junk, dedupe, NORMALIZE_EXACT, and NORMALIZE_COUNTRY if keyed.

See module body for ALB / AUT / BLR ethnic lists. Add new keys (CSV `Country`.casefold()) for
new countries when you want the same depth of rules.

Composition is loaded for **documentation** in the report (`FullHeritageAndNamingComposition.txt`).
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from utils.heritage_composition import load_composition_rows

CSV_PATH = _REPO / "givennamesForTransfer.csv"
REPORT_PATH = _REPO / "givennamesForTransfer_report.txt"
ETHNIC_DISCARD_REPORT_PATH = _REPO / "givennamesForTransfer_diaspora_discards.txt"
POOL_DIR = _REPO / "data" / "name_pools"

DISCARD_GLOBAL = frozenset(
    {
        "Sad",
        "Little",
        "Dark",
        "Red",
        "Silver",
        "Just",
        "News",
        "Games",
        "Design",
        "Media",
        "Official",
        "Company",
    }
)

DISCARD_BY_COUNTRY: dict[str, frozenset[str]] = {
    "albania": frozenset(
        {
            "Jona",
            "Bora",
            "Rigers",
        }
    ),
    "austria": frozenset(),
    "belarus": frozenset(
        {
            "Sveta",
            "Ivanov",
            "Al",
        }
    ),
}

# Shared strip for East/South Slavic ethnic pools: French / Anglo / Polish spellings not core local mainstream.
_SLAVIC_ETHNIC_WESTERN_STRIP: frozenset[str] = frozenset(
    {
        "Andrew",
        "Eugene",
        "Michael",
        "Nicolas",
        "Thomas",
        "John",
        "Martin",
        "Julien",
        "Christophe",
        "Anthony",
        "Pierre",
        "Yann",
        "Andy",
        "Chris",
        "George",
        "Alexandre",
        "Marc",
        "Olivier",
        "Tony",
        "James",
        "Arthur",
        "Benoît",
        "Loïc",
        "Erwan",
        "Ronan",
        "Ildar",
        "Jerome",
        "Florian",
        "Kevin",
        "Clément",
        "Murad",
        "Maxime",
        "Mathieu",
        "Lucas",
        "Nazar",
        "Stephane",
        "Romain",
        "Corentin",
        "Dan",
        "Bruno",
        "Johny",
        "Frédéric",
        "Dennis",
        "Eric",
        "Richard",
        "Vincent",
        "Emmanuel",
        "Gregory",
        "Matt",
        "Patrick",
        "Pawel",
        "Oliver",
        "Piotr",
        "Karol",
        "Tom",
        "Andrzej",
        "Angel",
        "Mikaël",
        "Mario",
        "Julian",
        "Jon",
        "Jonathan",
        "Philip",
        "Christian",
        "Jeremy",
        "Andreas",
        "Serge",
        "Victor",
    }
)

ETHNIC_NON_MAINSTREAM: dict[str, frozenset[str]] = {
    "albania": frozenset(
        {
            "William",
            "Alex",
            "Vladimir",
            "Gerald",
            "Ted",
            "Glen",
            "Donald",
            "Arnold",
            "Jurgen",
            "Spartak",
            "Franc",
            "Romeo",
        }
    ),
    "austria": frozenset(
        {
            "Mohammed",
            "Ibrahim",
            "Abdullah",
            "Hüseyin",
            "Mahmoud",
            "Hasan",
            "Fatih",
            "Emre",
            "Murat",
            "Amir",
            "Dragan",
            "Dejan",
            "Goran",
            "Aleksandar",
            "Miloš",
            "Saša",
            "Vladimir",
            "Igor",
            "Boris",
            "Milan",
            "Ivan",
            "Piotr",
            "Jakub",
            "Marek",
            "Kamil",
        }
    ),
    "belarus": _SLAVIC_ETHNIC_WESTERN_STRIP,
    # Croatian / Bulgarian ethnic pool: same Western non-mainstream strip as Belarus.
    "croatia": _SLAVIC_ETHNIC_WESTERN_STRIP,
    "bulgaria": _SLAVIC_ETHNIC_WESTERN_STRIP,
    # Bosnia and Herzegovina: intentionally no ethnic strip (multi-ethnic single pool).
}

NORMALIZE_EXACT: dict[str, str] = {
    "Antônio": "Antonio",
}

NORMALIZE_COUNTRY: dict[str, dict[str, str]] = {
    "austria": {
        "Juergen": "Jürgen",
        "Gunter": "Günther",
    },
}

_REASON_ETHNIC = "not credible ethnic mainstream (model via heritage / other country pools if needed)"


def _country_cell(row: dict[str, str]) -> str:
    for key in ("Country", "Country name", "country", "country_name"):
        v = row.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""


def discover_country_pools() -> dict[str, tuple[str, str]]:
    """
    Map CSV Country column (casefold) -> (country_code, filename).
    Uses country_name from each country_*.json under POOL_DIR.
    """
    out: dict[str, tuple[str, str]] = {}
    if not POOL_DIR.is_dir():
        return out
    for fp in sorted(POOL_DIR.glob("country_*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        name = (data.get("country_name") or "").strip()
        code = (data.get("country_code") or "").strip().upper()
        if not name or len(code) != 3 or not code.isalpha():
            continue
        k = name.casefold()
        if k not in out:
            out[k] = (code, fp.name)
    return out


def normalize_token(raw: str, country_key: str) -> str:
    s = (raw or "").strip()
    if not s:
        return s
    s = NORMALIZE_EXACT.get(s, s)
    for ck, mp in NORMALIZE_COUNTRY.items():
        if ck == country_key:
            s = mp.get(s, s)
            break
    if s and s[0].islower() and s[0].isalpha():
        s = s[0].upper() + s[1:]
    return s


def process_country(
    country_key: str, names_in_order: list[str]
) -> tuple[
    list[str],
    list[tuple[str, str]],
    list[tuple[str, str]],
    list[tuple[str, str]],
]:
    discarded_q: list[tuple[str, str]] = []
    discarded_e: list[tuple[str, str]] = []
    renames: list[tuple[str, str]] = []
    seen: set[str] = set()
    out: list[str] = []

    country_discard = DISCARD_BY_COUNTRY.get(country_key, frozenset())
    ethnic_drop = ETHNIC_NON_MAINSTREAM.get(country_key, frozenset())

    for raw in names_in_order:
        raw_stripped = (raw or "").strip()
        if not raw_stripped:
            discarded_q.append(("", "empty"))
            continue

        final = normalize_token(raw_stripped, country_key)
        if raw_stripped in NORMALIZE_EXACT:
            renames.append((raw_stripped, final))
        elif country_key in NORMALIZE_COUNTRY and raw_stripped in NORMALIZE_COUNTRY[country_key]:
            renames.append((raw_stripped, final))

        if final in DISCARD_GLOBAL:
            discarded_q.append((raw_stripped, "global junk / not a plausible given name"))
            continue
        if final in country_discard:
            discarded_q.append(
                (raw_stripped, f"not appropriate for male pool ({country_key})")
            )
            continue
        if final in ethnic_drop:
            discarded_e.append((raw_stripped, _REASON_ETHNIC))
            continue

        k = final.casefold()
        if k in seen:
            discarded_q.append((raw_stripped, f"duplicate after normalize → {final}"))
            continue
        seen.add(k)
        out.append(final)

    return out, discarded_q, discarded_e, renames


def tier_lists(names: list[str]) -> dict[str, list[str]]:
    vc = names[:20]
    co = names[20:50]
    mid = names[50:100]
    ra = names[100:]
    return {"very_common": vc, "common": co, "mid": mid, "rare": ra}


def format_composition_for_nationality(nat_code: str, rows: list) -> list[str]:
    lines: list[str] = []
    sub = [r for r in rows if r.get("nationality_code") == nat_code]
    if not sub:
        lines.append(f"No composition rows for {nat_code}.")
        return lines

    agg: dict[str, float] = defaultdict(float)
    for r in sub:
        pct = float(r["percent"]) / 100.0
        ocw = r.get("origin_country_weights") or {}
        if not ocw:
            ocw = {nat_code: 1.0}
        for cc, w in ocw.items():
            agg[str(cc).upper()] += pct * float(w)

    lines.append(
        "**Population-weighted origin country shares** (naming pool column × visual %): "
    )
    tot = sum(agg.values())
    if tot > 0:
        for cc, v in sorted(agg.items(), key=lambda x: -x[1]):
            lines.append(f"  - {cc}: {100.0 * v / tot:.2f}%")
    lines.append("")
    lines.append("**By visual bucket** (percent of nationality, naming pools):")
    for r in sorted(sub, key=lambda x: -float(x["percent"])):
        vb = r.get("visual_bucket", "")
        p = r.get("percent", 0)
        ocw = r.get("origin_country_weights") or {}
        parts = [f"{k} {v:.2f}" for k, v in sorted(ocw.items(), key=lambda x: -x[1])]
        lines.append(f"  - {vb} ({p}%): " + ", ".join(parts))
    return lines


def main() -> None:
    if not CSV_PATH.is_file():
        print(f"Missing {CSV_PATH}", file=sys.stderr)
        sys.exit(1)

    pool_by_display = discover_country_pools()
    if not pool_by_display:
        print(f"No country pools under {POOL_DIR}", file=sys.stderr)
        sys.exit(1)

    comp_rows = load_composition_rows()

    country_order: list[str] = []
    seen_c: set[str] = set()
    by_country: dict[str, list[str]] = defaultdict(list)

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name_col = row.get("Name") or row.get("name") or ""
            country_col = _country_cell(row)
            if not country_col:
                print("Row with empty country column, skipping", file=sys.stderr)
                continue
            k = country_col.casefold()
            if k not in seen_c:
                seen_c.add(k)
                country_order.append(k)
            by_country[k].append(name_col)

    report_lines: list[str] = [
        "# Given names import report",
        f"Source: {CSV_PATH.name}",
        "Tiers: top 20 very_common, next 30 common, next 50 mid, remainder rare.",
        "Countries resolved by matching `Country` column to `country_name` in `country_*.json`.",
        "",
        "## Cleansing policy",
        "- **Ethnic pool = credible local mainstream** where `ETHNIC_NON_MAINSTREAM` lists exist.",
        "- Other countries: global junk, dedupe, shared normalizations only (extend dicts in script as needed).",
        "- Composition reference below (not local_core).",
        "",
        "### Heritage composition reference",
        "",
    ]

    nat_codes_seen: list[str] = []
    for ck in country_order:
        meta = pool_by_display.get(ck)
        if not meta:
            continue
        code, _fn = meta
        if code not in nat_codes_seen:
            nat_codes_seen.append(code)

    for nat in nat_codes_seen:
        report_lines.append(f"#### {nat}")
        report_lines.extend(format_composition_for_nationality(nat, comp_rows))
        report_lines.append("")

    ethnic_report_lines: list[str] = [
        "# Removed as not credible ethnic mainstream",
        "",
        "Empty section (none) means no ethnic-mainstream list for that country key in the script.",
        "",
    ]

    skipped: list[str] = []

    for ck in country_order:
        meta = pool_by_display.get(ck)
        if not meta:
            skipped.append(ck)
            continue
        nat_code, fname = meta
        incoming = by_country[ck]
        kept, disc_q, disc_e, renames = process_country(ck, incoming)
        tiers = tier_lists(kept)

        pool_path = POOL_DIR / fname
        if not pool_path.is_file():
            print(f"Missing pool file {pool_path}", file=sys.stderr)
            skipped.append(ck)
            continue

        data = json.loads(pool_path.read_text(encoding="utf-8"))
        data["given_names_male"] = tiers
        pool_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        total_disc = len(disc_q) + len(disc_e)
        has_ethnic_cfg = bool(ETHNIC_NON_MAINSTREAM.get(ck))
        report_lines.append(f"## {ck.upper()} → {fname} ({nat_code})")
        report_lines.append(
            f"Raw rows: {len(incoming)}, kept: {len(kept)}, discarded: {total_disc} "
            f"(ethnic mainstream: {len(disc_e)}, other quality: {len(disc_q)})"
        )
        if not has_ethnic_cfg:
            report_lines.append(
                "*Ethnic mainstream filter: not configured for this country (empty list).*"
            )
        report_lines.append(
            f"Tiers: very_common={len(tiers['very_common'])} common={len(tiers['common'])} "
            f"mid={len(tiers['mid'])} rare={len(tiers['rare'])}"
        )
        report_lines.append("")
        report_lines.append("### Discarded — ethnic mainstream filter")
        if not disc_e:
            report_lines.append("(none)")
        else:
            for raw, reason in disc_e:
                report_lines.append(f"- `{raw}` → {reason}")
        report_lines.append("")
        report_lines.append("### Discarded — quality / junk / duplicates")
        if not disc_q:
            report_lines.append("(none)")
        else:
            for raw, reason in disc_q:
                report_lines.append(f"- `{raw}` → {reason}")
        report_lines.append("")
        report_lines.append("### Spelling / normalization (input → output)")
        if not renames:
            report_lines.append("(none)")
        else:
            for a, b in renames:
                report_lines.append(f"- `{a}` → `{b}`")
        report_lines.append("")

        ethnic_report_lines.append(f"## {ck.upper()} ({nat_code})")
        if not disc_e:
            ethnic_report_lines.append("(none)")
        else:
            for raw, _r in disc_e:
                ethnic_report_lines.append(f"- `{raw}`")
        ethnic_report_lines.append("")

    if skipped:
        report_lines.append("## Skipped (no matching `country_name` in country_*.json)")
        for s in skipped:
            report_lines.append(f"- `{s}`")
        report_lines.append("")

    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")
    ETHNIC_DISCARD_REPORT_PATH.write_text("\n".join(ethnic_report_lines), encoding="utf-8")
    print(f"Wrote pools + {REPORT_PATH} + {ETHNIC_DISCARD_REPORT_PATH}")
    if skipped:
        print(f"Warning: skipped countries with no pool match: {skipped}", file=sys.stderr)


if __name__ == "__main__":
    main()
