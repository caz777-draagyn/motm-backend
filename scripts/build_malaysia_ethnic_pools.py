#!/usr/bin/env python3
"""
Split country_MAS.json into custom_malaysia_malay / chinese / indian pools.

Classifies male givens + surnames by Malaysia-appropriate heuristics, drops junk,
re-tiers (20/30/50/rest). Leaves country_MAS as a thin mixed-national fallback.

Run: python scripts/build_malaysia_ethnic_pools.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
from name_pool_text import canon_name, is_plausible_token

REPO = Path(__file__).resolve().parent.parent
NP = REPO / "data" / "name_pools"
TIERS = ("very_common", "common", "mid", "rare")

META = {
    "tier_probs": {
        "given": {"very_common": 0.55, "common": 0.3, "mid": 0.13, "rare": 0.02},
        "surname": {"very_common": 0.45, "common": 0.35, "mid": 0.17, "rare": 0.03},
    },
    "middle_name_prob": 0.08,
    "compound_surname_prob": 0.04,
    "surname_connector": "-",
}

# Social / OCR / title junk, female tokens in male pool, non-names
DROP_CF: frozenset[str] = frozenset(
    {
        "junior", "cj", "mj", "jr", "sr", "mr", "ms", "dr", "ii", "iii", "iv",
        "dad", "baby", "king", "queen", "shop", "girl", "bro", "daddy", "little",
        "smart", "rock", "pop", "mj", "bb", "jb", "ej", "tj", "jj", "rj", "mg",
        "sk", "aj", "ed", "nic", "mac", "kit", "oh", "pa", "pie", "feel", "babe",
        "tok", "pok", "bang", "dak", "pu", "mas", "nad", "nay", "nix", "mon",
        "mj", "mek", "kaki", "insan", "bukan", "kedai", "kopi", "boy", "are",
        "dad", "shop", "baby", "king", "queen", "girl", "joan", "mae", "rose",
        "joy", "anne", "nicole", "claire", "marie", "kim",
    }
)

FEMALE_CF: frozenset[str] = frozenset(
    {"nurul", "natasha", "nabila", "amira", "ain", "gadis"}
)

# Chinese-style surnames (MY romanization)
CHINESE_SURNAMES: frozenset[str] = frozenset(
    """
    Tan Lee Lim Wong Chan Ng Chong Chin Ong Teh Yap Goh Ho Lau Lai Chew Ooi Khoo
    Chua Teoh Ling Ang Tang Loh Chang Gan Koh Kok Yong Low Leong Foo Yeoh Yew
    Cho Chai Hew Heng Hiew Hui Khor Kwan Kwee Liew Moy Poon Quah Seow Sim Soon
    Soo Su Sze Tham Toh Tye Wee Woo Yeo Yip Yuen Chia Chiew Choy Fong Fung Hon
    Keong Koo Kuah Lum Mah Ngai Pang Peh Phua Poh Quek Seah Shee Shen Shum Song
    Sun Tay Teng Ti Tiong Toh Tsai Tsen Tsoi Ung Woon Yen Yoon Zam
    """.split()
)

INDIAN_SURNAMES: frozenset[str] = frozenset(
    """
    Kumar Singh Raj Nair Ram Menon Pillai Rao Reddy Shetty Iyer Kapoor Gill
    Khan Kaur Sidhu Bala Devi Subramaniam Krishnan Murugan Tharmalingam
    """.split()
)

# Malay / Muslim patronymic-style surnames common in MY
MALAY_SURNAMES: frozenset[str] = frozenset(
    """
    Ahmad Abdullah Rahman Hassan Othman Osman Ismail Ibrahim Shah Aziz Ali
    Salleh Ramli Omar Zakaria Sulaiman Idris Hashim Ishak Ariffin Firdaus
    Hakim Azhar Nizam Nasir Razak Razali Anuar Yusof Zainal Zulkifli
    """.split()
)

CHINESE_SURNAMES_CF: frozenset[str] = frozenset(x.casefold() for x in CHINESE_SURNAMES)
INDIAN_SURNAMES_CF: frozenset[str] = frozenset(x.casefold() for x in INDIAN_SURNAMES)
MALAY_SURNAMES_CF: frozenset[str] = frozenset(x.casefold() for x in MALAY_SURNAMES)

# Romanization + common English givens in Malaysian Chinese use
CHINESE_GIVEN_EXTRA: frozenset[str] = frozenset(
    """
    Wei Wai Jun Jin Chin Chee Yong Hong Ming Hock Boon Eng Kang Kok Keong
    Kelvin Jason Kevin Andy Vincent Raymond Calvin Stanley Wilson Marcus
    Jonathan Andrew Aaron Alvin Kelvin Kenny Kenneth Kent Keith Colin
    Clarence Craig Calvin Carson Carter Cedric Clifford
    Derek Derrick Desmond Dexter Dominic Duncan
    Edison Edmund Edward Edwin Elliott Elvis Eric Ernest Eugene Evan
    Felix Ferdinand Francis Frankie
    Gabriel Gavin Gerald Gilbert Glen Glenn Gordon Greg
    Harrison Harry Hayden Henry Herman Howard
    Ian Isaac Ivan
    Jack Jamie Jared Jason Jay Jeff Jeffrey Jeremy Jerome Jerry Jesse
    Jimmy Johnny Jon Jordan Joseph Josh Julian Justin
    Kelvin Ken Kenny Kent Keith Kevin
    Lawrence Leonard Lewis Lincoln Lloyd Logan Lucas Luke Luther
    Marcus Mark Martin Marvin Matthew Max Melvin Michael
    Nathan Nathaniel Neil Nelson Nicholas Nigel
    Oscar Owen
    Patrick Paul Peter Philip Phillip
    Raymond Reginald Remy Rex Richard Ricky Rob Robert Rocky Ron Ronald
    Rory Ross Rowan Roy Russell Ryan
    Sam Samuel Scott Sean Sebastian Shane Shaun Shawn Sheldon Sherman
    Simon Sonny Stanley Stefan Stephen Steve Steven Stewart
    Ted Teddy Terence Terry Thomas Timothy Tony Troy
    Victor Vincent
    Wayne Wesley William
    Zach Zack
    Adrian Alan Alex Alexander Alfred Allen Andre Andreas Andrew Andy Angel
    Anthony Arnold Arthur Ashley
    Benjamin Ben Benny Bernie Bill Billy Bob Bobby Brandon Brian Bruce Bryan
    Alex Daniel David James John Michael Chris Mark Nick Steve Matt Luke Jake
    George Henry Harry Donald Douglas Dean Dale Don Derek Dave Dan Curtis Cory
    Cody Clinton Chester Chase Carl Cameron Bruce Brett Brad Blake
    """.replace("\n", " ").split()
)

CHINESE_GIVEN_CF: frozenset[str] = frozenset(x.casefold() for x in CHINESE_GIVEN_EXTRA)

# Tamil / Hindi / Punjabi / common Indian Malaysian givens
INDIAN_GIVEN_EXTRA: frozenset[str] = frozenset(
    """
    Sanjay Rajesh Raj Rahul Ravi Prem Sandeep Abhishek Naveed Nadeem Arun Anil
    Aditya Deepak Karthik Suresh Mahesh Ramesh Praveen Vijay Vishal Vikram
    Kiran Kishore Naresh Narendra Ganesh Gopal Krishna Kumar Lakshman Manoj
    Mukesh Prakash Rajiv Ranjit Rohit Sachin Saravan Selvam Shankar Siva
    Sridhar Subramaniam Sundaram Suresh Thiru Venkat Vinod Yogesh
    Amiruddin
    """.replace("\n", " ").split()
)

INDIAN_GIVEN_CF: frozenset[str] = frozenset(x.casefold() for x in INDIAN_GIVEN_EXTRA)

# Islamic / Malay given — prefix patterns (lowercase)
MALAY_PREFIX_RE = re.compile(
    r"^(muham|moham|mohd|muhamad|ahmad|abdul|abd|syed|tengku|nik|wan|che|mat\b|"
    r"khair|nur|amirul|zulk|firdaus|saiful|shah|shahid|badrul|taufik|taufiq|"
    r"nor|muh\b|ust|yusuf|yusri|yusof|zain|zaid|zaki|zikri|zul|nazr|nazmi|"
    r"nasir|naim|nabil|nazir|firdaus|faiz|fikri|fauzi|fauzan|fariz|farid|"
    r"farhan|fadhil|fadli|fad|hafiz|hafizi|hafis|haziq|hazim|haris|harith|"
    r"harris|hanif|hanis|hanafi|haniff|hilmi|hisham|husni|husin|hussein|"
    r"hussain|habib|halim|hamzah|hasan|hassan|haikal|hakim|hakimi|ikmal|"
    r"imran|irfan|ismail|izzat|izz|izz|johan|johan|kamal|karim|khalil|"
    r"khalid|khairul|luqman|luqman|mohd|moham|muham|mustafa|mustaqim|"
    r"naufal|omar|osman|othman|rizal|rizki|rizky|ridwan|ridhwan|raihan|"
    r"rafi|rafiq|rahmat|rahman|rashid|rasul|saiful|salman|shamsul|samsul|"
    r"syukri|syafiq|tarmizi|taufiq|taufik|umar|usman|yusri|zulkarnain|"
    r"zulkifli|zainal|zainuddin|zainul|zakaria|zakwan|zaidi|zamri|zul|"
    r"asri|aswad|aswad|azlan|azman|azmi|azril|azizi|azizul|azam|azim|"
    r"afiq|afif|afi|akmal|akbar|amir|ammar|amri|anas|anuar|anwar|ariff|"
    r"ariffin|ashraf|aswad|azhar|bad|badrul|faiq|fair|fuad|fauzi|"
    r"iskandar|ismail|izzuddin|izzat)",
    re.I,
)

# Looks like Tamil / Hindi romanization
INDIAN_SUFFIX_RE = re.compile(
    r"(esh|esan|esan|kumar|raj(?!ah)|pathy|rao|shek|veer|murug|mani|selv|"
    r"subram|tharan|karan|kish|deep|prem\b|sanja|naveed|nadeem|shek|deen|"
    r"deen\b|latha|pathy|kumar|reddy|swamy|gopal|kris|nanda|shank|mahesh|"
    r"ramesh|suresh|kumar|bir\b|ind\b|deep\b|kumar|sandeep|abhishek|"
    r"praveen|vijay|vishal|vikram|kiran|ganesh|mukesh|prakash|rajiv|"
    r"rohit|sachin|saravan|shankar|siva|sridhar|venkat|vinod|yogesh|"
    r"thiru|laksh|murthy|pillai|menon|nair\b|singh|kaur)",
    re.I,
)

# Short tokens that are Chinese romanization or family particles
CHINESE_SHORT_CF: frozenset[str] = frozenset(
    """
    wei wai jun jin chin chee yong kok kang hong ming eng boon hock lee lim
    tan wong chan ng chee teo teh yap goh ho lau lai chew ooi khoo chua teoh
    ling ang tang loh chang gan koh yong low leong foo yeoh yew cho chai
    """.split()
)


def flatten_names(pool: dict, key: str) -> list[str]:
    out: list[str] = []
    d = pool.get(key) or {}
    for t in TIERS:
        for x in d.get(t) or []:
            if isinstance(x, str):
                out.append(x)
    return out


def dedupe_first(names: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in names:
        c = canon_name(raw)
        if not c or not is_plausible_token(c):
            continue
        cf = c.casefold()
        if cf in DROP_CF or cf in FEMALE_CF:
            continue
        if cf in seen:
            continue
        seen.add(cf)
        out.append(c)
    return out


def tier(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def classify_surname(raw: str) -> str | None:
    c = canon_name(raw)
    if not c or not is_plausible_token(c):
        return None
    cf = c.casefold()
    if cf in DROP_CF or cf in FEMALE_CF:
        return None
    if cf in CHINESE_SURNAMES_CF:
        return "chinese"
    if cf in INDIAN_SURNAMES_CF:
        return "indian"
    if cf in MALAY_SURNAMES_CF:
        return "malay"
    # Mis-filed givens in surname buckets — route like givens
    g = classify_given(c)
    if g:
        return g
    return "malay"


def classify_given(raw: str) -> str | None:
    c = canon_name(raw)
    if not c or not is_plausible_token(c):
        return None
    cf = c.casefold()
    if cf in DROP_CF or cf in FEMALE_CF:
        return None
    if len(cf) <= 2 and cf not in {"al", "bo", "yu", "oh", "ko", "pu", "te", "we"}:
        return None

    if cf in INDIAN_GIVEN_CF:
        return "indian"
    if cf in CHINESE_GIVEN_CF:
        return "chinese"

    if INDIAN_SUFFIX_RE.search(cf) and not MALAY_PREFIX_RE.match(cf):
        # Karim, Omar etc. are Malay-Arabic; prefix check catches many
        if cf in {"karim", "umar", "salman", "ismail", "yusuf", "adam", "imran"}:
            return "malay"
        return "indian"

    if MALAY_PREFIX_RE.match(cf):
        return "malay"
    if cf in CHINESE_SHORT_CF:
        return "chinese"

    # Islamic / Malay flavour (no prefix match)
    if re.search(
        r"(uddin|udin|ilah|izan|izal|izin|wani|budi|putra|mamat|"
        r"mas\b|suka\b|bukan\b)",
        cf,
    ):
        return "malay"

    return "malay"


def main() -> None:
    # Full pre-split list (not the thin country_MAS output). Replace with a larger export if needed.
    src_path = REPO / "scripts" / "data" / "country_MAS_source.json"
    src = json.loads(src_path.read_text(encoding="utf-8-sig"))

    raw_g = flatten_names(src, "given_names_male")
    raw_s = flatten_names(src, "surnames")

    malay_g: list[str] = []
    chinese_g: list[str] = []
    indian_g: list[str] = []
    seen_g: set[str] = set()

    for x in raw_g:
        cat = classify_given(x)
        if not cat:
            continue
        c = canon_name(x)
        cf = c.casefold()
        if cf in seen_g:
            continue
        seen_g.add(cf)
        if cat == "malay":
            malay_g.append(c)
        elif cat == "chinese":
            chinese_g.append(c)
        else:
            indian_g.append(c)

    malay_s: list[str] = []
    chinese_s: list[str] = []
    indian_s: list[str] = []
    seen_s: set[str] = set()

    for x in raw_s:
        cat = classify_surname(x)
        if not cat:
            continue
        c = canon_name(x)
        cf = c.casefold()
        if cf in seen_s:
            continue
        seen_s.add(cf)
        if cat == "malay":
            malay_s.append(c)
        elif cat == "chinese":
            chinese_s.append(c)
        else:
            indian_s.append(c)

    # Thin national fallback (mixed, deduped, Malaysia-appropriate)
    mixed_g = dedupe_first(
        [
            "Muhammad",
            "Ahmad",
            "Amir",
            "Hafiz",
            "Tan",
            "Lee",
            "Lim",
            "Wong",
            "Kumar",
            "Raj",
            "Daniel",
            "Jason",
            "Kevin",
            "Adam",
            "David",
            "Michael",
            "Faiz",
            "Aiman",
            "Kelvin",
            "Vincent",
        ]
    )
    mixed_s = dedupe_first(
        [
            "Ahmad",
            "Abdullah",
            "Tan",
            "Lee",
            "Lim",
            "Wong",
            "Chan",
            "Ismail",
            "Rahman",
            "Kumar",
            "Singh",
            "Ng",
            "Ong",
            "Hassan",
            "Ibrahim",
            "Raj",
            "Nair",
            "Chong",
            "Yap",
            "Goh",
        ]
    )

    def doc(pool_id: str, label: str, g: list[str], s: list[str]) -> dict:
        return {
            "pool_id": pool_id,
            "country_code": "MAS",
            "country_name": label,
            "given_names_male": tier(g),
            "surnames": tier(s),
            **META,
        }

    out = {
        "custom_malaysia_malay.json": doc(
            "custom_malaysia_malay", "Malaysia Malay", malay_g, malay_s
        ),
        "custom_malaysia_chinese.json": doc(
            "custom_malaysia_chinese", "Malaysia Chinese", chinese_g, chinese_s
        ),
        "custom_malaysia_indian.json": doc(
            "custom_malaysia_indian", "Malaysia Indian", indian_g, indian_s
        ),
    }

    for fn, payload in out.items():
        (NP / fn).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    country_doc = {
        "country_code": "MAS",
        "country_name": "Malaysia",
        "given_names_male": tier(mixed_g),
        "surnames": tier(mixed_s),
        "tier_probs": src.get("tier_probs", META["tier_probs"]),
        "middle_name_prob": src.get("middle_name_prob", META["middle_name_prob"]),
        "compound_surname_prob": src.get("compound_surname_prob", META["compound_surname_prob"]),
        "surname_connector": src.get("surname_connector", META["surname_connector"]),
        "pool_id": "country_MAS",
    }

    (NP / "country_MAS.json").write_text(
        json.dumps(country_doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    def ng(d: dict) -> int:
        return sum(len(d["given_names_male"][t]) for t in TIERS)

    def ns(d: dict) -> int:
        return sum(len(d["surnames"][t]) for t in TIERS)

    print(f"malay:    givens={ng(out['custom_malaysia_malay.json'])} surnames={ns(out['custom_malaysia_malay.json'])}")
    print(f"chinese:  givens={ng(out['custom_malaysia_chinese.json'])} surnames={ns(out['custom_malaysia_chinese.json'])}")
    print(f"indian:   givens={ng(out['custom_malaysia_indian.json'])} surnames={ns(out['custom_malaysia_indian.json'])}")
    print(f"country:  givens={ng(country_doc)} surnames={ns(country_doc)} (mixed fallback)")


if __name__ == "__main__":
    main()
