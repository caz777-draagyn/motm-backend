"""
Regenerate data/chinese_pinyin_syllables.txt (needs: pip install pypinyin).

Used by scripts/cleanse_chn_nonchinese_givens.py for Mandarin syllable validation.
"""
from __future__ import annotations

from pypinyin import pinyin, Style

syllables: set[str] = set()
for code in range(0x4E00, 0x9FFF + 1):
    ch = chr(code)
    try:
        py = pinyin(ch, style=Style.NORMAL, heteronym=False)
    except Exception:
        continue
    if not py or not py[0]:
        continue
    s = py[0][0].lower().replace("ü", "v")
    if s and all(c in "abcdefghijklmnopqrstuvwxyz" for c in s):
        syllables.add(s)

# zero-initial syllables written with y/w in pinyin
for extra in (
    "a", "o", "e", "ai", "ei", "ao", "ou", "an", "en", "ang", "eng", "er",
    "yi", "yin", "ying", "wu", "yu", "yue", "yuan", "yun",
):
    syllables.add(extra.replace("ü", "v"))

from pathlib import Path

out = Path(__file__).resolve().parent.parent / "data" / "chinese_pinyin_syllables.txt"
out.write_text("\n".join(sorted(syllables)) + "\n", encoding="utf-8")
print("wrote", len(syllables), "syllables to", out)
