"""
QC rule data for process_first_europe_csv.py.

All structures are keyed by ISO 3166-1 alpha-2 codes as in FirstEurope.csv
(Country code). Do not point multiple countries at the same frozenset object:
each country owns its literals so lists can diverge during review.

HR / BG: no ethnic strip here yet — curate separately from BY (user request).
"""

from __future__ import annotations

# --- Quality (wrong sex, fragments, etc.) ------------------------------------

QUALITY_DISCARD_BY_COUNTRY: dict[str, frozenset[str]] = {
    "AL": frozenset(
        {
            "Jona",
            "Bora",
            "Rigers",
        }
    ),
    "BY": frozenset(
        {
            "Sveta",
            "Ivanov",
            "Al",
        }
    ),
}

# --- Ethnic mainstream (non-local spellings / pools modelled elsewhere) -------

AL_ETHNIC_DISCARD: frozenset[str] = frozenset(
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
)

AT_ETHNIC_DISCARD: frozenset[str] = frozenset(
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
)

# Belarus-only list (same *content* as the old shared Slavic strip once had, but
# a separate object — HR/BG must not reference this).
BY_ETHNIC_DISCARD: frozenset[str] = frozenset(
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

ETHNIC_DISCARD_BY_COUNTRY: dict[str, frozenset[str]] = {
    "AL": AL_ETHNIC_DISCARD,
    "AT": AT_ETHNIC_DISCARD,
    "BY": BY_ETHNIC_DISCARD,
}
