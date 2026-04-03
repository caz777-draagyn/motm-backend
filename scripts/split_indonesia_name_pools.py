#!/usr/bin/env python3
"""
Cleanse country_IDN male givens + surnames, write neutral tiers to country_IDN.json,
and split givens into three *distinct* custom pools:

  custom_indonesia_javanese.json   — Java / Sundanese–skewed + default Indonesian core
  custom_indonesia_sumatran.json   — Sumatra / Melayu / Aceh–skewed
  custom_indonesia_other.json      — Bali, Sulawesi (Andi), eastern Christian, Maluku/Papua flavour,
                                     plus international / Anglo given names still used in Indonesia

Only a small **pan-national** set (top Islamic / unmarked national givens) is duplicated across
all three pools; every other name appears in **exactly one** custom pool.

~280 additional givens that would otherwise default to Java are sampled (spread across the
alphabet) into the Sumatran pool — nationally plausible, and disjoint from strict Java-only /
Anglo-other / Bali–Sulawesi cues.

Surnames: same cleansed list in all four files.

Run: python scripts/split_indonesia_name_pools.py
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_COUNTRY = _REPO / "data" / "name_pools" / "country_IDN.json"
_JAVA = _REPO / "data" / "name_pools" / "custom_indonesia_javanese.json"
_SUM = _REPO / "data" / "name_pools" / "custom_indonesia_sumatran.json"
_OTH = _REPO / "data" / "name_pools" / "custom_indonesia_other.json"

_TIER_ORDER = ("very_common", "common", "mid", "rare")
_TIER_RANK = {t: i for i, t in enumerate(_TIER_ORDER)}

# Duplicated in javanese + sumatran + other (truly nationwide).
_PAN_NATIONAL_CF: frozenset[str] = frozenset(
    {
        "muhammad",
        "muhamad",
        "mohammad",
        "mohamed",
        "ahmad",
        "achmad",
        "akhmad",
        "ahmed",
        "ali",
        "abdul",
        "abdullah",
        "ibrahim",
        "yusuf",
        "umar",
        "omar",
        "usman",
        "uthman",
        "hasan",
        "hassan",
        "hussein",
        "husein",
        "imam",
        "amin",
        "salman",
        "ismail",
        "syekh",
        "muhammed",
        "mohammed",
    }
)

# Strong Java / Sundanese (single-pool: javanese, unless also in PAN).
_JAVA_STRONG_CF: frozenset[str] = frozenset(
    {
        "agus",
        "budi",
        "eko",
        "joko",
        "jaka",
        "teguh",
        "yoga",
        "yudi",
        "yogi",
        "hendra",
        "hendro",
        "hendi",
        "heru",
        "heri",
        "hari",
        "dedi",
        "dede",
        "deden",
        "ridwan",
        "agung",
        "bambang",
        "slamet",
        "gatot",
        "wawan",
        "toto",
        "seno",
        "danang",
        "anto",
        "yanto",
        "cahya",
        "cecep",
        "ujang",
        "endi",
        "panji",
        "djoko",
        "sutrisno",
        "tri",
        "dwi",
        "sigit",
        "bagus",
        "edi",
        "eddy",
        "edy",
        "hary",
        "hendy",
        "jajang",
        "tatang",
        "dadang",
        "wibowo",
        "prasetyo",
        "firmansyah",
        "setiawan",
        "gunawan",
        "santoso",
        "darmawan",
        "kurniawan",
        "saputra",
        "nugraha",
        "hidayat",
        "pratama",
        "maulana",
        "satria",
        "joko",
        "cahyo",
        "adi",
        "ade",
        "dian",
        "bayu",
        "putra",
        "dimas",
        "taufik",
        "taufiq",
        "asep",
        "iwan",
    }
)

# Sumatra / Melayu / Minang / Aceh skew (single-pool: sumatran, unless PAN).
# Union at runtime with _compute_sumatra_expand_cf(ordered_g).
_SUMATRA_STRONG_CORE_CF: frozenset[str] = frozenset(
    {
        "teuku",
        "tengku",
        "faisal",
        "fairul",
        "fahrul",
        "fadli",
        "fadly",
        "fadhil",
        "fadhillah",
        "arief",
        "arie",
        "rahmat",
        "rahmad",
        "syahrul",
        "syahrial",
        "ramli",
        "fauzi",
        "fauzan",
        "zulkifli",
        "zainal",
        "zainul",
        "chairul",
        "cahyadi",
        "noer",
        "yusril",
        "rizal",
        "riski",
        "reski",
        "reza",
        "rizki",
        "rizky",
        "muzakkir",
        "nurdin",
        "nasution",
        "lubis",
        "siregar",
        "sinaga",
        "simanjuntak",
        "harahap",
        "rangkuti",
        "pohan",
        "tampubolon",
        "damanik",
        "tarigan",
        "sembiring",
        "irfan",
        "naufal",
        "wildan",
        "hafiz",
        "hafid",
        "fajar",
        "ilham",
        "zaki",
        "zaky",
        "farhan",
        "farid",
        "syafiq",
        "faqih",
        "azhar",
        "bachtiar",
        "munawar",
        "zulfikar",
        "hamzah",
        "ubaid",
        "ashari",
        "syafii",
        "maruf",
        "aminuddin",
        "khalid",
        "bilal",
    }
)

# Obvious junk / honorifics — never auto-promote to Sumatra expand.
_SUMATRA_EXPAND_SKIP_CF: frozenset[str] = frozenset(
    {
        "bong",
        "boy",
        "apa",
        "mon",
        "oom",
        "pong",
        "bulan",
        "alter",
        "gens",
    }
)

_SUMATRA_EXPAND_TARGET = 280

# Bali, Sulawesi, eastern / Melanesian Christian Indonesia, etc. (single-pool: other).
_OTHER_STRONG_CF: frozenset[str] = frozenset(
    {
        "wayan",
        "gede",
        "ketut",
        "komang",
        "nyoman",
        "made",
        "putu",
        "andi",
        "yohanes",
        "johanes",
        "stefanus",
        "ignatius",
        "gregorius",
        "petrus",
        "paulus",
        "antonius",
        "yosep",
        "stepanus",
        "stevanus",
        "yonathan",
        "yonatan",
        "oktovian",
        "oktavian",
        "ferdinandus",
        "lukas",
        "matius",
        "markus",
        "barnabas",
        "filemon",
        "timotius",
        "yakobus",
    }
)

# Tier boosts within each pool (subset of that pool’s names).
_JAVA_BOOST_CF: frozenset[str] = _JAVA_STRONG_CF | _PAN_NATIONAL_CF
_OTHER_BOOST_CF: frozenset[str] = _OTHER_STRONG_CF | _PAN_NATIONAL_CF

_REPAIR_CF: dict[str, str] = {
    "jhon": "John",
    "collen": "Colin",
    "mathew": "Matthew",
}

# Junk / honorific / female / initialism / obvious non-Indonesian given names.
_DROP_GIVEN_CF: frozenset[str] = frozenset(
    {
        "bang",
        "mas",
        "mang",
        "om",
        "pak",
        "cak",
        "mbah",
        "budak",
        "bukan",
        "nama",
        "little",
        "king",
        "akun",
        "kopi",
        "shop",
        "calon",
        "indo",
        "my",
        "anti",
        "kang",
        "anak",
        "an",
        "oh",
        "mg",
        "bb",
        "jb",
        "cj",
        "mj",
        "aj",
        "rj",
        "ej",
        "pj",
        "lj",
        "tj",
        "jj",
        "cu",
        "pe",
        "tong",
        "sar",
        "tai",
        "nok",
        "mix",
        "nic",
        "nik",
        "kok",
        "kong",
        "kie",
        "pai",
        "pep",
        "beer",
        "bless",
        "feel",
        "babe",
        "baby",
        "dad",
        "pop",
        "zy",
        "zee",
        "try",
        "ids",
        "ii",
        "wi",
        "ry",
        "y",
        "am",
        "ar",
        "de",
        "ge",
        "dex",
        "wong",
        "tan",
        "teh",
        "ibu",
        "bunda",
        "eng",
        "neng",
        "nurul",
        "dini",
        "suci",
        "mega",
        "gadis",
        "chintya",
        "desty",
        "devy",
        "erni",
        "ratu",
        "sekar",
        "tyas",
        "santy",
        "renny",
        "angel",
        "joan",
        "bim",
        "doi",
        "dek",
        "daddy",
        "ok",
        "ols",
        "sanjay",
        "rohit",
        "rajesh",
        "abhishek",
        "gaurav",
        "amit",
        "graham",
        "helmut",
        "ludwig",
        "bjorn",
        "jurgen",
        "tiger",
        "aquarius",
        "reyes",
        "just",
        "bali",
        "aly",
        "engel",
        "federico",
        "giorgio",
        "vladimir",
        "dmitri",
        "sergei",
        "viktor",
        "claus",
        "sven",
        "lars",
        "olaf",
        "gunnar",
        "thor",
        "bent",
        "jens",
        "niels",
        "pierre",
        "jacques",
        "jean",
        "francois",
        "gilles",
        "henri",
        "antoine",
        "nicolas",
        "sebastien",
        "guillaume",
        "remy",
        "ricci",
        "romano",
        "cesare",
        "enzo",
        "lorenzo",
        "giuseppe",
        "salvatore",
        "vincenzo",
        "carlos",
        "javier",
        "miguel",
        "diego",
        "fernando",
        "ricardo",
        "alejandro",
        "pablo",
        "manuel",
        "jorge",
        "rafael",
        "antonio",
        "jordi",
        "xavier",
        "juan",
        "pedro",
        "luis",
        "jose",
        "mario",
        "stefano",
        "marco",
        "luca",
        "matteo",
        "andrea",
        "giovanni",
        "paolo",
        "francesco",
        "alessandro",
        "massimo",
        "vikram",
        "arjun",
        "rahul",
        "kumar",
        "deepak",
        "suresh",
        "pradeep",
        "wei",
        "jian",
        "hao",
        "ming",
        "takashi",
        "hiroshi",
        "kenji",
        "yuki",
        "satoshi",
        "daisuke",
        "jong",
        "suk",
        "minho",
        "tae",
        "hyun",
        "callum",
        "declan",
        "finley",
        "freddie",
        "archie",
        "alfie",
        "ollie",
        "toby",
        "harry",
        "alfred",
        "arthur",
        "albert",
        "bernard",
        "cecil",
        "clive",
        "cyril",
        "derek",
        "desmond",
        "douglas",
        "edmund",
        "ernest",
        "gerald",
        "gilbert",
        "godfrey",
        "harold",
        "horace",
        "hugh",
        "ian",
        "leslie",
        "leonard",
        "malcolm",
        "maurice",
        "nigel",
        "norman",
        "percy",
        "reginald",
        "roderick",
        "roland",
        "rupert",
        "stanley",
        "terence",
        "wilfred",
        "cecilia",
    }
)

_INITIALISM_CF: frozenset[str] = frozenset(
    {"cj", "mj", "aj", "rj", "ej", "pj", "jb", "jj", "tj", "lj", "jl", "mg", "bb"}
)

_ALLOW_LEN2_CF: frozenset[str] = frozenset({"ed", "yu", "ky", "bo", "le", "lu", "sy", "dy"})

_DROP_SURNAME_CF: frozenset[str] = frozenset(
    {
        "putri",
        "sari",
        "lestari",
        "wulandari",
        "pratiwi",
        "dewi",
        "rahmawati",
        "ayu",
        "anggraini",
        "amalia",
        "amelia",
        "handayani",
        "maharani",
        "susanti",
        "aprilia",
        "oktaviani",
        "damayanti",
        "utami",
        "kartika",
        "natalia",
        "shop",
        "elisabeth",
    }
)

_POOL_META = (
    "tier_probs",
    "middle_name_prob",
    "compound_surname_prob",
    "surname_connector",
)


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", (s or "").strip())


def _strip_marks(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def _norm_key(s: str) -> str:
    return _strip_marks(_nfc(s)).casefold()


def _valid_token(n: str) -> bool:
    if not n:
        return False
    n0 = _nfc(n)
    if len(n0) < 2:
        return False
    for part in re.split(r"[\s–-]", n.replace("–", "-")):
        if not part:
            continue
        if not all((c.isalpha() or c in "'.-" + "´") for c in part):
            return False
    return True


def _title_word(chunk: str) -> str:
    c = chunk.strip()
    if not c:
        return c
    return c[:1].upper() + c[1:].lower()


def _canon_latin_display(raw: str) -> str:
    base = _strip_marks(unicodedata.normalize("NFKC", (raw or "").strip())).replace("–", "-")
    out_words: list[str] = []
    for w in base.split():
        parts = [_title_word(p) for p in w.split("-") if p.strip()]
        if parts:
            out_words.append("-".join(parts))
    return " ".join(out_words)


def _plain_ascii_name(s: str) -> bool:
    for part in re.split(r"[\s–-]", s.replace("–", "-")):
        if not part:
            continue
        for c in part:
            if c in "'.":
                continue
            if not (c.isascii() and (c.isalpha() or c == "-")):
                return False
    return True


def _flatten_tiered(d: dict) -> list[str]:
    out: list[str] = []
    for t in _TIER_ORDER:
        for x in d.get(t) or []:
            if isinstance(x, str):
                out.append(x)
    return out


def _identity_rank_from_raw(gm: dict) -> dict[str, float]:
    id_rank: dict[str, float] = {}
    for tier in _TIER_ORDER:
        band = float(_TIER_RANK[tier])
        for raw in gm.get(tier) or []:
            if not isinstance(raw, str):
                continue
            s = _canon_latin_display(raw)
            cf = _norm_key(s)
            if cf in _REPAIR_CF:
                cf = _norm_key(_REPAIR_CF[cf])
            id_rank[cf] = min(id_rank.get(cf, 1e9), band)
    return id_rank


def _clean_givens_male(raw_flat: list[str], id_rank: dict[str, float]) -> list[str]:
    chosen: dict[str, str] = {}
    for raw in raw_flat:
        s0 = _canon_latin_display(raw)
        if not s0 or not _plain_ascii_name(s0):
            continue
        cf = _norm_key(s0)
        if cf in _DROP_GIVEN_CF:
            continue
        if cf in _REPAIR_CF:
            s0 = _nfc(_REPAIR_CF[cf])
            cf = _norm_key(s0)
        if cf in _INITIALISM_CF:
            continue
        if len(cf) == 2 and cf not in _ALLOW_LEN2_CF:
            continue
        if not _valid_token(s0):
            continue
        if cf == "al":
            continue
        if cf not in chosen or len(s0) >= len(chosen[cf]):
            chosen[cf] = s0

    def nk(display: str) -> tuple[float, str]:
        ik = _norm_key(display)
        return (id_rank.get(ik, 9999.0), display.casefold())

    return sorted(chosen.values(), key=nk)


# Western / global given names common in urban & Christian Indonesian contexts — “other” pool only.
_ANGLO_OTHER_CF: frozenset[str] = frozenset(
    {
        "kevin",
        "brian",
        "ryan",
        "justin",
        "brandon",
        "jordan",
        "tyler",
        "kyle",
        "derek",
        "scott",
        "travis",
        "trevor",
        "cody",
        "connor",
        "dylan",
        "ethan",
        "evan",
        "gavin",
        "hunter",
        "mason",
        "logan",
        "lucas",
        "blake",
        "chase",
        "dustin",
        "tanner",
        "tristan",
        "brad",
        "zachary",
        "zach",
        "zack",
        "caleb",
        "cameron",
        "cole",
        "colin",
        "grant",
        "mitch",
        "mitchell",
        "nate",
        "spencer",
        "taylor",
        "ty",
        "zane",
        "nathaniel",
        "isaac",
        "seth",
        "riley",
        "quinn",
        "reed",
        "parker",
        "preston",
        "quentin",
        "brett",
        "brody",
        "landon",
        "colton",
        "clay",
        "corey",
        "curtis",
        "damon",
        "darren",
        "doug",
        "duane",
        "earl",
        "eddie",
        "elliot",
        "elliott",
        "fred",
        "freddy",
        "garry",
        "glenn",
        "greg",
        "gregory",
        "howard",
        "hugh",
        "hugo",
        "ira",
        "ivan",
        "jeremy",
        "jerome",
        "jerry",
        "jim",
        "jon",
        "julian",
        "julius",
        "karl",
        "keith",
        "kurt",
        "lawrence",
        "lee",
        "leonard",
        "lewis",
        "lloyd",
        "louis",
        "malcolm",
        "marc",
        "marshall",
        "max",
        "maxwell",
        "melvin",
        "micah",
        "miles",
        "morgan",
        "morris",
        "murray",
        "nelson",
        "norman",
        "perry",
        "phil",
        "philip",
        "phillip",
        "ralph",
        "randall",
        "ray",
        "reggie",
        "rex",
        "ricky",
        "robbie",
        "rodney",
        "rory",
        "roscoe",
        "rudy",
        "salvador",
        "sterling",
        "stuart",
        "ted",
        "teddy",
        "theo",
        "theodore",
        "tobias",
        "trent",
        "vernon",
        "virgil",
        "wade",
        "wallace",
        "wendell",
        "wiley",
        "will",
        "wilson",
        "winston",
        "wyatt",
        "barry",
        "bernie",
        "bruce",
        "byron",
        "carl",
        "clark",
        "craig",
        "dale",
        "dave",
        "dean",
        "don",
        "donald",
        "douglas",
        "edmund",
        "elijah",
        "emmanuel",
        "felix",
        "gabriel",
        "gordon",
        "harold",
        "harvey",
        "henry",
        "jack",
        "jake",
        "jimmy",
        "johnny",
        "joel",
        "lance",
        "larry",
        "leo",
        "leon",
        "marcus",
        "martin",
        "matt",
        "neil",
        "nicholas",
        "noah",
        "oscar",
        "oliver",
        "owen",
        "randy",
        "raymond",
        "rich",
        "richard",
        "rick",
        "roger",
        "roland",
        "roman",
        "ron",
        "ronald",
        "ross",
        "roy",
        "ruben",
        "russell",
        "sam",
        "sean",
        "shane",
        "sidney",
        "stanley",
        "stephen",
        "steve",
        "steven",
        "terry",
        "tim",
        "timothy",
        "todd",
        "tom",
        "tommy",
        "troy",
        "vince",
        "vincent",
        "victor",
        "walter",
        "warren",
        "wayne",
        "wesley",
        "bob",
        "bill",
        "joe",
        "nick",
        "mike",
        "chris",
        "alex",
        "andy",
        "jeff",
        "ken",
        "kenny",
        "rob",
        "tony",
        "ian",
        "aaron",
        "alan",
        "allen",
        "albert",
        "alfred",
        "ben",
        "bryan",
        "calvin",
        "christian",
        "christopher",
        "daniel",
        "david",
        "dennis",
        "edward",
        "frank",
        "gary",
        "george",
        "james",
        "jason",
        "john",
        "joseph",
        "joshua",
        "mark",
        "matthew",
        "michael",
        "nathan",
        "patrick",
        "paul",
        "peter",
        "robert",
        "simon",
        "thomas",
        "william",
        "andrew",
        "anthony",
        "charles",
        "jonathan",
        "samuel",
        "benjamin",
        "alexander",
        "jose",
        "juan",
        "luis",
        "xavier",
    }
)


def _compute_sumatra_expand_cf(ordered_g: list[str]) -> frozenset[str]:
    """~N names that would otherwise default to Java; plausible on Sumatra too."""
    skip = (
        _PAN_NATIONAL_CF
        | _JAVA_STRONG_CF
        | _OTHER_STRONG_CF
        | _ANGLO_OTHER_CF
        | _SUMATRA_STRONG_CORE_CF
        | _DROP_GIVEN_CF
        | _SUMATRA_EXPAND_SKIP_CF
    )
    cand = sorted({_norm_key(n) for n in ordered_g if _norm_key(n) not in skip})
    if not cand:
        return frozenset()
    target = min(_SUMATRA_EXPAND_TARGET, len(cand))
    step = max(1, len(cand) // target)
    picked: list[str] = []
    for i in range(0, len(cand), step):
        picked.append(cand[i])
        if len(picked) >= _SUMATRA_EXPAND_TARGET:
            break
    return frozenset(picked)


def _primary_pool_for_name(cf: str, sumatra_strong: frozenset[str]) -> str:
    """Exactly one of java | sumatra | other for non–pan-national names."""
    in_j = cf in _JAVA_STRONG_CF
    in_s = cf in sumatra_strong
    in_o = cf in _OTHER_STRONG_CF
    hits = int(in_j) + int(in_s) + int(in_o)
    if hits >= 2:
        if in_o:
            return "other"
        if in_s:
            return "sumatra"
        return "java"
    if in_o:
        return "other"
    if in_s:
        return "sumatra"
    if in_j:
        return "java"
    if cf in _ANGLO_OTHER_CF:
        return "other"
    return "java"


_IDN_SURNAME_LEGACY_ORDER: tuple[str, ...] = (
    "Setiawan",
    "Saputra",
    "Kurniawan",
    "Pratama",
    "Maulana",
    "Hidayat",
    "Putra",
    "Wijaya",
    "Ramadhan",
    "Gunawan",
    "Nugraha",
    "Prasetyo",
    "Irawan",
    "Firmansyah",
    "Nugroho",
    "Rahman",
    "Ahmad",
    "Permana",
    "Akbar",
    "Hermawan",
    "Chandra",
    "Fauzi",
    "Santoso",
    "Kusuma",
    "Muhammad",
    "Susanto",
    "Firdaus",
    "Wibowo",
    "Darmawan",
    "Siregar",
    "Syahputra",
    "Prasetya",
    "Ramadhani",
    "Sinaga",
    "Kurnia",
    "Arifin",
    "Satria",
    "Purnama",
    "Sanjaya",
    "Yusuf",
    "Iskandar",
    "Dwi",
    "Wahyu",
    "Rahma",
    "Iqbal",
    "Rizki",
    "Setyawan",
    "Lee",
    "Ridwan",
    "Nasution",
    "Hakim",
    "Wicaksono",
    "Simanjuntak",
    "Lesmana",
    "Budiman",
    "Fajar",
    "Rizal",
    "Christian",
    "Agustin",
    "Rachman",
    "Ilham",
    "Lubis",
    "Ramdani",
)


def _clean_surnames(raw_flat: list[str]) -> list[str]:
    legacy_index = {_norm_key(x): i for i, x in enumerate(_IDN_SURNAME_LEGACY_ORDER)}
    seen: dict[str, str] = {}
    for raw in raw_flat:
        s0 = _canon_latin_display(raw)
        if not s0 or not _plain_ascii_name(s0):
            continue
        cf = _norm_key(s0)
        if cf in _DROP_SURNAME_CF:
            continue
        if len(cf) < 2:
            continue
        if not _valid_token(s0):
            continue
        if cf not in seen or len(s0) >= len(seen[cf]):
            seen[cf] = s0

    def sk(d: str) -> tuple[int, str]:
        ik = _norm_key(d)
        return (legacy_index.get(ik, 10_000), d.casefold())

    return sorted(seen.values(), key=sk)


def _tier_list(names: list[str]) -> dict[str, list[str]]:
    return {
        "very_common": names[:20],
        "common": names[20:50],
        "mid": names[50:100],
        "rare": names[100:],
    }


def _rank_for_pool(
    names: list[str], id_rank: dict[str, float], boost: frozenset[str]
) -> list[str]:
    def k(n: str) -> tuple[float, int, str]:
        cf = _norm_key(n)
        br = id_rank.get(cf, 9999.0)
        hit = 1 if cf in boost else 0
        return (br, -hit, cf)

    return sorted(names, key=k)


def _assign_custom_pools(
    ordered_g: list[str], sumatra_strong: frozenset[str]
) -> tuple[list[str], list[str], list[str]]:
    java: list[str] = []
    summ: list[str] = []
    oth: list[str] = []
    for display in ordered_g:
        cf = _norm_key(display)
        if cf in _PAN_NATIONAL_CF:
            java.append(display)
            summ.append(display)
            oth.append(display)
            continue
        p = _primary_pool_for_name(cf, sumatra_strong)
        if p == "java":
            java.append(display)
        elif p == "sumatra":
            summ.append(display)
        else:
            oth.append(display)
    return java, summ, oth


def main() -> None:
    country = json.loads(_COUNTRY.read_text(encoding="utf-8"))
    java = json.loads(_JAVA.read_text(encoding="utf-8"))
    summ = json.loads(_SUM.read_text(encoding="utf-8"))
    oth = json.loads(_OTH.read_text(encoding="utf-8"))

    gm = country["given_names_male"]
    id_rank = _identity_rank_from_raw(gm)
    flat_g = _flatten_tiered(gm)
    ordered_g = _clean_givens_male(flat_g, id_rank)
    tier_country_g = _tier_list(ordered_g)

    sur_flat = _flatten_tiered(country["surnames"])
    ordered_s = _clean_surnames(sur_flat)
    tier_s = _tier_list(ordered_s)

    sumatra_expand_cf = _compute_sumatra_expand_cf(ordered_g)
    sumatra_strong = _SUMATRA_STRONG_CORE_CF | sumatra_expand_cf
    sumatra_boost = sumatra_strong | _PAN_NATIONAL_CF

    java_g, sum_g, oth_g = _assign_custom_pools(ordered_g, sumatra_strong)

    java["given_names_male"] = _tier_list(_rank_for_pool(java_g, id_rank, _JAVA_BOOST_CF))
    summ["given_names_male"] = _tier_list(_rank_for_pool(sum_g, id_rank, sumatra_boost))
    oth["given_names_male"] = _tier_list(_rank_for_pool(oth_g, id_rank, _OTHER_BOOST_CF))

    country["given_names_male"] = tier_country_g
    country["surnames"] = tier_s
    for pool in (java, summ, oth):
        pool["surnames"] = tier_s
        for k in _POOL_META:
            if k in country:
                pool[k] = country[k]

    _COUNTRY.write_text(
        json.dumps(country, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _JAVA.write_text(
        json.dumps(java, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _SUM.write_text(
        json.dumps(summ, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    _OTH.write_text(
        json.dumps(oth, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    pan = len(_PAN_NATIONAL_CF & {_norm_key(x) for x in ordered_g})
    print(
        f"givens total {len(ordered_g)} | java {len(java_g)} | sumatra {len(sum_g)} | "
        f"other {len(oth_g)} | pan-national in data ~{pan} | sumatra_expand ~{len(sumatra_expand_cf)} | "
        f"surnames {len(ordered_s)}"
    )


if __name__ == "__main__":
    main()
