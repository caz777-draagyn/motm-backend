#!/usr/bin/env python3
"""
FirstEurope.csv → sorted CSV with QC suggestion columns (no rows removed).

- Input:  repo root FirstEurope.csv (semicolon-delimited; male-only source).
- Output: FirstEurope_qc.csv (original columns + QC columns),
          FirstEurope_qc_summary.txt (counts).

Sorting: Country code, Country Rank ascending, then Frequency descending.

QC model:
  * qc_global_junk — one shared junk set (case-insensitive on Name / Name ASCII).
  * qc_country_quality, qc_country_ethnic — every Country code present in the
    file is evaluated; lists come from first_europe_qc_data.py (default empty
    set). n/a only if Country code is blank. No list is borrowed from another country.
  * qc_duplicate_within_country — first row wins in sort order for
    (Country code, canonical name key); later rows discard.
  * name_canonical — trim + global exact map + per-country exact map + title fix.

Per-country quality/ethnic sets live in first_europe_qc_data.py (ISO2 keys).
HR/BG ethnic lists are intentionally absent until curated separately from BY.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO = _SCRIPT_DIR.parent
for _p in (_REPO, _SCRIPT_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from first_europe_qc_data import (  # noqa: E402
    ETHNIC_DISCARD_BY_COUNTRY,
    QUALITY_DISCARD_BY_COUNTRY,
)

INPUT_CSV = _REPO / "FirstEurope.csv"
OUTPUT_CSV = _REPO / "FirstEurope_qc.csv"
REPORT_PATH = _REPO / "FirstEurope_qc_summary.txt"

# --- Global junk (lowercased for lookup) ------------------------------------
_RAW_JUNK = {
    "sad",
    "little",
    "dark",
    "red",
    "silver",
    "just",
    "news",
    "games",
    "design",
    "media",
    "official",
    "company",
    "read",
    "auto",
    "white",
    "travel",
    "machine",
    "magazine",
    "music",
}

JUNK_GLOBAL: frozenset[str] = frozenset(_RAW_JUNK)

# Exact replacements before country maps (any country).
NORMALIZE_EXACT: dict[str, str] = {
    "Antônio": "Antonio",
}

# Per ISO 3166-1 alpha-2 code from CSV. Do not reuse another country's dict.
NORMALIZE_BY_COUNTRY: dict[str, dict[str, str]] = {
    "AT": {
        "Juergen": "Jürgen",
        "Gunter": "Günther",
    },
    # Example: add DK-only exact pairs; avoid blind ae→æ (hits e.g. \"Michael\").
}

# Per-country quality / ethnic sets: scripts/first_europe_qc_data.py (ISO2 keys).


def _parse_int(s: str, default: int = 0) -> int:
    try:
        return int((s or "").strip())
    except ValueError:
        return default


def _title_fix(s: str) -> str:
    if s and s[0].islower() and s[0].isalpha():
        return s[0].upper() + s[1:]
    return s


def canonical_name(raw: str, iso2: str) -> str:
    s = (raw or "").strip()
    if not s:
        return s
    s = NORMALIZE_EXACT.get(s, s)
    cmap = NORMALIZE_BY_COUNTRY.get(iso2.upper(), {})
    s = cmap.get(s, s)
    return _title_fix(s)


def canonical_key(canonical: str) -> str:
    return canonical.casefold()


def junk_verdict(name: str, name_ascii: str) -> str:
    for part in ((name_ascii or "").strip(), (name or "").strip()):
        if part and part.casefold() in JUNK_GLOBAL:
            return "discard"
    return "keep"


def quality_verdict(
    canonical: str, iso2: str, *, countries_in_dataset: frozenset[str]
) -> str:
    iso2 = (iso2 or "").strip().upper()
    if not iso2:
        return "n/a"
    if iso2 not in countries_in_dataset:
        return "n/a"
    bag = QUALITY_DISCARD_BY_COUNTRY.get(iso2, frozenset())
    if not canonical:
        return "discard"
    return "discard" if canonical in bag else "keep"


def ethnic_verdict(
    canonical: str, iso2: str, *, countries_in_dataset: frozenset[str]
) -> str:
    iso2 = (iso2 or "").strip().upper()
    if not iso2:
        return "n/a"
    if iso2 not in countries_in_dataset:
        return "n/a"
    bag = ETHNIC_DISCARD_BY_COUNTRY.get(iso2, frozenset())
    if not canonical:
        return "discard"
    return "discard" if canonical in bag else "keep"


def row_sort_key(row: dict[str, str]) -> tuple[str, int, int]:
    code = (row.get("Country code") or "").strip().upper()
    rank = _parse_int(row.get("Country Rank") or "", 10**9)
    freq = _parse_int(row.get("Frequency") or "", 0)
    # Lower frequency sorts later when rank ties (defensive).
    return (code, rank, -freq)


def load_rows() -> list[dict[str, str]]:
    if not INPUT_CSV.is_file():
        raise SystemExit(f"Missing input: {INPUT_CSV}")
    # utf-8-sig: strip BOM so the first header is "Name", not "\ufeffName".
    with INPUT_CSV.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter=";")
        if not r.fieldnames:
            raise SystemExit("CSV has no header")
        rows = list(r)
    return rows


def main() -> None:
    rows = load_rows()
    gender_vals = {((row.get("Gender") or "").strip().lower()) for row in rows}
    gender_vals.discard("")
    if gender_vals and gender_vals != {"m"}:
        print(
            "Warning: expected only Gender=m; also saw:",
            sorted(gender_vals),
            file=sys.stderr,
        )

    rows.sort(key=row_sort_key)

    countries_in_dataset = frozenset(
        (r.get("Country code") or "").strip().upper()
        for r in rows
        if (r.get("Country code") or "").strip()
    )

    seen_key_per_country: dict[str, set[str]] = defaultdict(set)
    out_fieldnames: list[str] | None = None
    out_rows: list[dict[str, str]] = []

    cnt_junk = Counter()
    cnt_qual = Counter()
    cnt_eth = Counter()
    cnt_dup = Counter()
    cnt_row = Counter()
    stats_by_country: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    for row in rows:
        iso2 = (row.get("Country code") or "").strip().upper()
        name = row.get("Name") or ""
        name_ascii = row.get("Name ASCII") or ""
        can = canonical_name(name, iso2)
        key = canonical_key(can)

        q_junk = junk_verdict(name, name_ascii)
        q_qual = quality_verdict(can, iso2, countries_in_dataset=countries_in_dataset)
        q_eth = ethnic_verdict(can, iso2, countries_in_dataset=countries_in_dataset)

        if not can:
            q_dup = "discard"
        elif not key:
            q_dup = "keep"
        elif key in seen_key_per_country[iso2]:
            q_dup = "discard"
        else:
            seen_key_per_country[iso2].add(key)
            q_dup = "keep"

        verdicts = [q_junk, q_qual, q_eth, q_dup]
        if any(v == "discard" for v in verdicts):
            qc_row = "discard"
        else:
            qc_row = "keep"

        enriched = dict(row)
        enriched["name_canonical"] = can
        enriched["qc_global_junk"] = q_junk
        enriched["qc_country_quality"] = q_qual
        enriched["qc_country_ethnic"] = q_eth
        enriched["qc_duplicate_within_country"] = q_dup
        enriched["qc_suggested_row_action"] = qc_row

        out_rows.append(enriched)
        cnt_junk[q_junk] += 1
        cnt_qual[q_qual] += 1
        cnt_eth[q_eth] += 1
        cnt_dup[q_dup] += 1
        cnt_row[qc_row] += 1

        bc = stats_by_country[iso2 or "?"]
        bc[f"junk_{q_junk}"] += 1
        bc[f"qual_{q_qual}"] += 1
        bc[f"eth_{q_eth}"] += 1
        bc[f"dup_{q_dup}"] += 1
        bc[f"row_{qc_row}"] += 1

        if out_fieldnames is None:
            base = list(row.keys())
            extra = [
                "name_canonical",
                "qc_global_junk",
                "qc_country_quality",
                "qc_country_ethnic",
                "qc_duplicate_within_country",
                "qc_suggested_row_action",
            ]
            out_fieldnames = base + extra

    assert out_fieldnames is not None
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fieldnames, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(out_rows)

    def _fmt_ctr(c: Counter) -> str:
        return ", ".join(f"{k}={c[k]}" for k in sorted(c.keys()))

    lines = [
        f"Input:  {INPUT_CSV}",
        f"Output: {OUTPUT_CSV}",
        f"Rows:   {len(out_rows)}",
        "",
        "Counts per QC column:",
        f"  qc_global_junk:              {_fmt_ctr(cnt_junk)}",
        f"  qc_country_quality:        {_fmt_ctr(cnt_qual)}",
        f"  qc_country_ethnic:         {_fmt_ctr(cnt_eth)}",
        f"  qc_duplicate_within_country: {_fmt_ctr(cnt_dup)}",
        f"  qc_suggested_row_action:   {_fmt_ctr(cnt_row)}",
        "",
        "Row-level discard counts (single reason columns):",
        f"  qc_country_quality discard: {sum(1 for r in out_rows if r['qc_country_quality'] == 'discard')}",
        f"  qc_country_ethnic discard:  {sum(1 for r in out_rows if r['qc_country_ethnic'] == 'discard')}",
        "",
        f"Country codes in input ({len(countries_in_dataset)}): {', '.join(sorted(countries_in_dataset))}",
        "",
        "Per-country rule list sizes (empty = checked, no discards from that list):",
    ]
    for code in sorted(countries_in_dataset):
        nq = len(QUALITY_DISCARD_BY_COUNTRY.get(code, frozenset()))
        ne = len(ETHNIC_DISCARD_BY_COUNTRY.get(code, frozenset()))
        lines.append(f"  {code}: quality_list={nq} ethnic_list={ne}")
    lines.extend(
        [
            "",
            "Per-country row discard (qc_suggested_row_action == discard):",
        ]
    )
    per_c_discard = sorted(
        (
            iso,
            stats_by_country[iso].get("row_discard", 0),
        )
        for iso in stats_by_country
        if stats_by_country[iso].get("row_discard", 0)
    )
    for iso, n in per_c_discard[:50]:
        lines.append(f"  {iso}: {n}")
    if len(per_c_discard) > 50:
        lines.append(f"  ... and {len(per_c_discard) - 50} more countries")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_CSV} ({len(out_rows)} rows)")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
