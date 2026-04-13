#!/usr/bin/env python3
"""
Fix mojibake in name pool JSON (UTF-8 bytes mis-decoded as Latin-1), e.g. GÃ¼ler -> Güler, AteÅŸ -> Ateş.

Only rewrites strings that round-trip via latin-1 -> utf-8; correct Unicode (ş, ü in native form)
often cannot encode as latin-1 and is left unchanged.

Run from repo root: python scripts/fix_name_pool_mojibake.py
Optional: python scripts/fix_name_pool_mojibake.py --dry-run
Backups/old: python scripts/fix_name_pool_mojibake.py --include-backups
Audit only: python scripts/fix_name_pool_mojibake.py --audit-only [--include-backups] [--strict-audit]
After fix + audit: python scripts/fix_name_pool_mojibake.py --audit [--strict-audit]
Optional ftfy (pip install ftfy): add --ftfy (only runs on strings that still look suspicious before heuristics).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME_POOLS = ROOT / "data" / "name_pools"

TIER_BLOCKS = ("given_names_male", "surnames")

# UTF-8 sequences truncated mid-character (latin-1 round-trip cannot fix). Re-check after CSV import.
KNOWN_TRUNCATED: dict[str, str] = {
    "Âzim": "Azim",
    "Âme": "Ame",
    "MarbÃ": "Marban",
}

# Pool stem (Path.stem, e.g. country_VIE) -> truncated-token fixes that differ by locale.
POOL_SPECIFIC_TRUNCATED: dict[str, dict[str, str]] = {
    "country_VIE": {
        "TrÃ": "Trang",
        "QuÃ": "Quang",
        "ZacÃ": "Zach",
    },
    "country_KOR": {
        "TrÃ": "Tran",
    },
}

# Literals that never improve via latin-1 round-trip (multi-layer or wrong encoding).
KNOWN_BROKEN_LITERALS: dict[str, str] = {
    "Ãlšhãwî": "Alshawi",
}

# Substrings: if present with Â, treat as legitimate (Portuguese / Lusophone).
_AUDIT_ALLOW_SUBSTRINGS_Â = (
    "Ângelo",
    "Ângela",
    "Âncora",
)


def _suspicious_mojibake(s: str) -> bool:
    if not isinstance(s, str) or not s:
        return False
    if "Ã" in s:
        return True
    if "Â" not in s:
        return False
    for sub in _AUDIT_ALLOW_SUBSTRINGS_Â:
        if sub in s:
            return False
    return True


def _needs_ftfy(s: str) -> bool:
    """Avoid running ftfy on every string (large pools); only likely mojibake survivors."""
    return _suspicious_mojibake(s)


def fix_mojibake(s: str, max_rounds: int = 4) -> str:
    if not isinstance(s, str) or not s:
        return s
    out = s
    for _ in range(max_rounds):
        try:
            b = out.encode("latin-1")
            n = b.decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if n == out:
            break
        out = n
    return out


def _apply_trunc_maps(s: str, pool_stem: str) -> str:
    fixed = s
    if fixed in KNOWN_TRUNCATED:
        fixed = KNOWN_TRUNCATED[fixed]
    pool_map = POOL_SPECIFIC_TRUNCATED.get(pool_stem)
    if pool_map and fixed in pool_map:
        fixed = pool_map[fixed]
    if fixed in KNOWN_BROKEN_LITERALS:
        fixed = KNOWN_BROKEN_LITERALS[fixed]
    return fixed


def _maybe_ftfy(s: str, use_ftfy: bool) -> str:
    if not use_ftfy or not s or not _needs_ftfy(s):
        return s
    try:
        import ftfy  # type: ignore[import-untyped]
    except ImportError:
        return s
    return ftfy.fix_text(s)


def _fix_spurious_leading_circumflex(s: str) -> str:
    """
    Leading U+00C2 (Â) before a letter is often a mis-decoded 'A' (e.g. Âdem -> Adem, Âmbar -> Ambar).
    Do not touch Ângelo / Ângela (Portuguese).
    """
    if not s.startswith("Â") or len(s) < 2:
        return s
    if s.startswith("Ângel"):
        return s
    rest = s[1:]
    if not rest[:1].isalpha():
        return s
    return "A" + rest


def _fix_spurious_leading_c3_a(s: str) -> str:
    """
    Leading U+00C3 (Ã) before a letter: latin-1 round-trip often fails on the first byte; treat as 'A'.
    (e.g. Ãbràhém -> Abràhém, Ãttåçk -> Attåçk.)
    """
    if not s.startswith("Ã") or len(s) < 2:
        return s
    if not s[1].isalpha():
        return s
    return "A" + s[1:]


def fix_string_list(names: list, pool_stem: str, use_ftfy: bool) -> tuple[list, int]:
    changed = 0
    out = []
    for x in names:
        if not isinstance(x, str):
            out.append(x)
            continue
        fixed = fix_mojibake(x)
        fixed = _apply_trunc_maps(fixed, pool_stem)
        fixed = _maybe_ftfy(fixed, use_ftfy)
        fixed = _fix_spurious_leading_circumflex(fixed)
        fixed = _fix_spurious_leading_c3_a(fixed)
        if fixed != x:
            changed += 1
        out.append(fixed)
    return out, changed


def fix_tier_block(block: dict, pool_stem: str, use_ftfy: bool) -> int:
    if not isinstance(block, dict):
        return 0
    total = 0
    for _tier, arr in list(block.items()):
        if not isinstance(arr, list):
            continue
        new_list, n = fix_string_list(arr, pool_stem, use_ftfy)
        block[_tier] = new_list
        total += n
    return total


def should_skip(path: Path, include_backups: bool) -> bool:
    if include_backups:
        return False
    parts_cf = {p.casefold() for p in path.parts}
    if "old" in parts_cf:
        return True
    for p in path.parts:
        if "_backup" in p.casefold():
            return True
    if "_backup" in path.name.casefold():
        return True
    return False


def iter_pool_paths(include_backups: bool) -> list[Path]:
    paths: list[Path] = []
    patterns = ("country_*.json", "custom_*.json")
    for pattern in patterns:
        for path in sorted(NAME_POOLS.glob(pattern)):
            if not should_skip(path, include_backups=False):
                paths.append(path)
    if include_backups:
        for sub in ("_backup_heuristic_male_clean", "_backup_surnames", "old"):
            d = NAME_POOLS / sub
            if not d.is_dir():
                continue
            for pattern in patterns:
                paths.extend(sorted(d.glob(pattern)))
    return sorted(set(paths), key=lambda p: str(p))


def collect_tier_strings(data: dict) -> list[tuple[str, str, str]]:
    """(block_key, tier_key, name) for each string in tier lists."""
    found: list[tuple[str, str, str]] = []
    for block_key in TIER_BLOCKS:
        block = data.get(block_key)
        if not isinstance(block, dict):
            continue
        for tier_key, arr in block.items():
            if not isinstance(arr, list):
                continue
            for x in arr:
                if isinstance(x, str):
                    found.append((block_key, str(tier_key), x))
    return found


def audit_file(path: Path) -> list[tuple[str, str, str]]:
    """Return list of (block, tier, name) that still look like mojibake."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    bad: list[tuple[str, str, str]] = []
    for block_key, tier_key, name in collect_tier_strings(data):
        if _suspicious_mojibake(name):
            bad.append((block_key, tier_key, name))
    return bad


def process_file(path: Path, dry_run: bool, use_ftfy: bool) -> int:
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Skip {path.name}: {e}", file=sys.stderr)
        return 0

    pool_stem = path.stem
    changed = 0
    for key in TIER_BLOCKS:
        if key not in data:
            continue
        changed += fix_tier_block(data[key], pool_stem, use_ftfy)

    if changed == 0:
        return 0

    if dry_run:
        print(f"{path.name}: would fix {changed} string(s)")
        return changed

    out = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(out, encoding="utf-8")
    print(f"{path.name}: fixed {changed} string(s)")
    return changed


def run_audit(paths: list[Path], strict: bool) -> int:
    total = 0
    for path in paths:
        issues = audit_file(path)
        if not issues:
            continue
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            rel = path
        for block_key, tier_key, name in issues:
            total += 1
            print(f"{rel}\t{block_key}\t{tier_key}\t{name!r}", file=sys.stderr)
    if total:
        print(f"Audit: {total} suspicious string(s)", file=sys.stderr)
    else:
        print("Audit: 0 suspicious strings", file=sys.stderr)
    if strict and total:
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Fix or audit mojibake in name pool JSON files.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--include-backups",
        action="store_true",
        help="Also process _backup_heuristic_male_clean, _backup_surnames, and old/ under name_pools.",
    )
    ap.add_argument(
        "--audit-only",
        action="store_true",
        help="Do not modify files; only report strings that still look like mojibake.",
    )
    ap.add_argument(
        "--audit",
        action="store_true",
        help="After fixing (unless --audit-only), scan all processed paths and report survivors.",
    )
    ap.add_argument(
        "--strict-audit",
        action="store_true",
        help="Exit with code 1 if audit finds any suspicious strings.",
    )
    ap.add_argument(
        "--ftfy",
        action="store_true",
        help="If ftfy is installed, run it after round-trip + known maps (helps some multi-layer cases).",
    )
    args = ap.parse_args()

    paths = iter_pool_paths(args.include_backups)

    if args.audit_only:
        return run_audit(paths, strict=args.strict_audit)

    total_files = 0
    total_strings = 0
    for path in paths:
        n = process_file(path, args.dry_run, args.ftfy)
        if n:
            total_files += 1
            total_strings += n

    print(
        f"Done. Files touched: {total_files}, strings changed: {total_strings} (dry_run={args.dry_run})",
        file=sys.stderr,
    )

    if args.audit:
        audit_rc = run_audit(paths, strict=args.strict_audit)
        if audit_rc != 0:
            return audit_rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
