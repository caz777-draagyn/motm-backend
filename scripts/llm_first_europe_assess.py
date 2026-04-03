#!/usr/bin/env python3
"""
LLM-assisted mainstream plausibility for FirstEurope name rows (batched).

Reads a semicolon CSV (default: FirstEurope_qc.csv), adds columns:
  llm_mainstream_suggestion — keep | discard | review
  llm_mainstream_note      — short reason (may be empty)
  llm_model                — model id used
  llm_assessed_at          — ISO timestamp

OpenAI default model: gpt-4o-mini (override with OPENAI_MODEL or --model).

Ollama (local, no OpenAI key):
  python scripts/llm_first_europe_assess.py --ollama --model llama3.2
  # or set OLLAMA_BASE_URL=http://127.0.0.1:11434/v1 and OLLAMA_MODEL / OPENAI_MODEL

Requires one of:
  * --ollama — uses http://127.0.0.1:11434/v1 by default (override with --ollama-url)
  * OPENAI_API_KEY — OpenAI or compatible API (optional OPENAI_BASE_URL for Azure)
  * OLLAMA_BASE_URL in .env — same as --ollama

Install Ollama: https://ollama.com — then: ollama pull llama3.2

Resume: re-run the same command; rows that already have llm_mainstream_suggestion
set are skipped. Output is rewritten from input + merged LLM fields each time
(checkpoint batches flush the full file).

Usage:
  python scripts/llm_first_europe_assess.py --ollama --model llama3.2
  python scripts/llm_first_europe_assess.py --ollama --limit 64   # smoke test
  python scripts/llm_first_europe_assess.py   # OpenAI if OPENAI_API_KEY set
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO = _SCRIPT_DIR.parent

DEFAULT_INPUT = _REPO / "FirstEurope_qc.csv"
DEFAULT_OUTPUT = _REPO / "FirstEurope_llm.csv"

SYSTEM_PROMPT = """You assess male GIVEN NAMES for a football management game.
For each row you receive: country (ISO code + English country name) and the name as shown in data.

"keep" — The name is plausible as a common/local mainstream male given name for that country (including well-integrated international names that are everyday in that country).

"discard" — Clear issues: not a plausible given name (junk word, obvious non-name), clearly a female name used as male by mistake, OR the name is overwhelmingly and specifically associated with another culture/region such that it would NOT read as mainstream local for a generic domestic player in that country.

"review" — Uncertain, rare, diaspora-ambiguous, or you lack confidence.

Use "discard" sparingly for cultural judgment; when genuinely unsure prefer "review".
Return ONLY valid JSON matching the schema; no markdown."""

USER_TEMPLATE = """Assess each item. Respond with JSON:
{{"results":[{{"i":<int>,"verdict":"keep"|"discard"|"review","note":"<brief optional>"}}]}}

Items:
{items_json}
"""


def _row_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        (row.get("Country code") or "").strip(),
        (row.get("Name") or "").strip(),
        (row.get("Country Rank") or "").strip(),
    )


def _normalize_ollama_base(url: str) -> str:
    u = (url or "").strip().rstrip("/")
    if not u:
        return "http://127.0.0.1:11434/v1"
    if not u.endswith("/v1"):
        u = f"{u}/v1"
    return u


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="LLM batch assess FirstEurope names")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument(
        "--ollama",
        action="store_true",
        help="Use local Ollama OpenAI-compatible API (no OPENAI_API_KEY)",
    )
    p.add_argument(
        "--ollama-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
        help="Ollama base URL (/v1 appended if missing)",
    )
    p.add_argument(
        "--model",
        default="",
        help="Model name (e.g. llama3.2 for Ollama, gpt-4o-mini for OpenAI)",
    )
    p.add_argument("--batch-size", type=int, default=32, help="Rows per API call")
    p.add_argument(
        "--flush-every",
        type=int,
        default=20,
        help="Write full output every N completed batches",
    )
    p.add_argument("--limit", type=int, default=0, help="Max new assessments (0=all)")
    p.add_argument(
        "--sleep",
        type=float,
        default=0.15,
        help="Seconds between API calls (rate limits)",
    )
    p.add_argument(
        "--progress-every",
        type=int,
        default=5,
        help="Print progress every N batches (0=only checkpoints)",
    )
    return p.parse_args()


def _load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f, delimiter=";")
        if not r.fieldnames:
            raise SystemExit("CSV has no header")
        fieldnames = list(r.fieldnames)
        rows = list(r)
    return fieldnames, rows


def _parse_llm_json(raw: str) -> dict:
    """Parse JSON from model output; tolerate markdown fences."""
    text = (raw or "").strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=fieldnames, delimiter=";", extrasaction="ignore", lineterminator="\n"
        )
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def _call_openai_batch(
    client: OpenAI,
    model: str,
    batch: list[tuple[int, dict[str, str]]],
    *,
    prefer_json_object: bool,
) -> dict[int, tuple[str, str]]:
    """Returns row_index -> (verdict, note)."""
    items = []
    for i, row in batch:
        items.append(
            {
                "i": i,
                "name": (row.get("Name") or "").strip(),
                "name_ascii": (row.get("Name ASCII") or "").strip(),
                "country_code": (row.get("Country code") or "").strip(),
                "country_name": (row.get("Country name") or "").strip(),
            }
        )
    user_msg = USER_TEMPLATE.format(items_json=json.dumps(items, ensure_ascii=False))

    kwargs: dict = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0.1,
    }
    if prefer_json_object:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        resp = client.chat.completions.create(**kwargs)
    except Exception:
        if prefer_json_object:
            kwargs.pop("response_format", None)
            resp = client.chat.completions.create(**kwargs)
        else:
            raise

    raw = (resp.choices[0].message.content or "").strip()
    data = _parse_llm_json(raw)
    results = data.get("results")
    if not isinstance(results, list):
        raise ValueError(f"Missing results list: {raw[:500]}")

    out: dict[int, tuple[str, str]] = {}
    for item in results:
        if not isinstance(item, dict):
            continue
        idx = item.get("i")
        verdict = (item.get("verdict") or "").strip().lower()
        note = (item.get("note") or "").strip()
        if verdict not in ("keep", "discard", "review"):
            verdict = "review"
            if not note:
                note = "invalid verdict from model"
        if isinstance(idx, int):
            out[idx] = (verdict, note[:500])
    return out


def main() -> None:
    if load_dotenv:
        load_dotenv(_REPO / ".env")

    args = _parse_args()
    if OpenAI is None:
        raise SystemExit("Install openai: pip install openai")

    use_ollama = False
    api_key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    base_url = (os.environ.get("OPENAI_BASE_URL") or "").strip() or None
    ollama_url = (os.environ.get("OLLAMA_BASE_URL") or "").strip()

    if args.ollama:
        use_ollama = True
        api_key = "ollama"
        base_url = _normalize_ollama_base(args.ollama_url)
    elif not api_key and ollama_url:
        api_key = "ollama"
        base_url = _normalize_ollama_base(ollama_url)
        use_ollama = True

    if not api_key:
        raise SystemExit(
            "No API configured. Use one of:\n"
            "  Ollama:  python scripts/llm_first_europe_assess.py --ollama --model llama3.2\n"
            "           (start Ollama, then: ollama pull <model>)\n"
            "  OpenAI:  set OPENAI_API_KEY in .env\n"
            "  Or set OLLAMA_BASE_URL in .env without OPENAI_API_KEY."
        )

    if args.model.strip():
        model = args.model.strip()
    elif use_ollama:
        model = (
            (os.environ.get("OLLAMA_MODEL") or "").strip()
            or (os.environ.get("OPENAI_MODEL") or "").strip()
            or "llama3.2"
        )
    else:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    client = OpenAI(api_key=api_key, base_url=base_url if base_url else None)
    prefer_json_object = not use_ollama

    inp = args.input
    if not inp.is_file():
        raise SystemExit(f"Input not found: {inp}")

    fieldnames, rows = _load_csv(inp)
    llm_cols = [
        "llm_mainstream_suggestion",
        "llm_mainstream_note",
        "llm_model",
        "llm_assessed_at",
    ]
    for c in llm_cols:
        if c not in fieldnames:
            fieldnames.append(c)

    # Merge existing LLM output if present (resume)
    existing: dict[tuple[str, str, str], dict[str, str]] = {}
    if args.output.is_file() and args.output.resolve() != inp.resolve():
        _ofn, orows = _load_csv(args.output)
        for r in orows:
            k = _row_key(r)
            if (r.get("llm_mainstream_suggestion") or "").strip():
                existing[k] = {c: r.get(c, "") for c in llm_cols}

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pending: list[tuple[int, dict[str, str]]] = []
    for idx, row in enumerate(rows):
        k = _row_key(row)
        if k in existing:
            for c in llm_cols:
                row[c] = existing[k].get(c, "")
            continue
        if (row.get("llm_mainstream_suggestion") or "").strip():
            continue
        pending.append((idx, row))

    if args.limit > 0:
        pending = pending[: args.limit]

    total_pending = len(pending)
    if total_pending == 0:
        print("Nothing to assess (all rows already have llm_mainstream_suggestion).")
        _write_csv(args.output, fieldnames, rows)
        return

    num_batches = (total_pending + args.batch_size - 1) // max(1, args.batch_size)
    print(
        f"Model: {model}  Base URL: {base_url or '(default OpenAI)'}  "
        f"Pending rows: {total_pending}  Batches: ~{num_batches}  Batch size: {args.batch_size}"
    )

    batch_size = max(1, args.batch_size)
    flush_every = max(1, args.flush_every)
    batches_done = 0
    new_done = 0
    t_loop = time.time()

    for off in range(0, len(pending), batch_size):
        chunk = pending[off : off + batch_size]
        indices = [i for i, _ in chunk]
        last_err: Exception | None = None
        for attempt in range(5):
            try:
                verdicts = _call_openai_batch(
                    client, model, chunk, prefer_json_object=prefer_json_object
                )
                break
            except Exception as e:
                last_err = e
                wait = 2**attempt
                print(f"API error (attempt {attempt + 1}/5): {e!s}; sleeping {wait}s", file=sys.stderr)
                time.sleep(wait)
        else:
            raise RuntimeError(f"Batch failed after retries: {last_err}") from last_err

        for i, row in chunk:
            v, note = verdicts.get(i, ("review", "missing from model response"))
            row["llm_mainstream_suggestion"] = v
            row["llm_mainstream_note"] = note
            row["llm_model"] = model
            row["llm_assessed_at"] = now
            new_done += 1

        missing = [i for i in indices if i not in verdicts]
        if missing:
            print(f"Warning: missing indices in response: {missing[:10]}...", file=sys.stderr)

        batches_done += 1
        pe = args.progress_every
        if pe > 0 and (batches_done % pe == 0 or new_done >= total_pending):
            elapsed = max(time.time() - t_loop, 0.001)
            rps = new_done / elapsed
            left = total_pending - new_done
            eta_s = left / rps if rps > 0 else 0
            pct = 100.0 * new_done / total_pending
            print(
                f"Progress: {new_done}/{total_pending} rows ({pct:.1f}%)  "
                f"batch {batches_done}/{num_batches}  ~{eta_s / 60:.0f} min remaining"
            )

        if batches_done % flush_every == 0:
            _write_csv(args.output, fieldnames, rows)
            print(f"Checkpoint: wrote {args.output} ({new_done}/{total_pending} new)")

        time.sleep(args.sleep)

    _write_csv(args.output, fieldnames, rows)
    print(f"Done. Wrote {args.output}  New assessments: {new_done}")


if __name__ == "__main__":
    main()
