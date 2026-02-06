"""
Name data structures for realistic player name generation.

Contains country-specific name pools (tiered), heritage group definitions,
origin country mappings, and configuration for name structure probabilities.
"""

from typing import Dict, List, Optional

# Tier probabilities (default, configurable per country)
DEFAULT_GIVEN_NAME_TIER_PROBS = {
    "very_common": 0.55,
    "common": 0.30,
    "mid": 0.13,
    "rare": 0.02
}

DEFAULT_SURNAME_TIER_PROBS = {
    "very_common": 0.45,
    "common": 0.35,
    "mid": 0.17,
    "rare": 0.03
}

# Country-specific tier probabilities
COUNTRY_TIER_PROBS: Dict[str, Dict[str, Dict[str, float]]] = {
    "ENG": {
        "given": {"very_common": 0.55, "common": 0.30, "mid": 0.13, "rare": 0.02},
        "surname": {"very_common": 0.45, "common": 0.35, "mid": 0.17, "rare": 0.03}
    },
    "FRA": {
        "given": {"very_common": 0.52, "common": 0.32, "mid": 0.14, "rare": 0.02},
        "surname": {"very_common": 0.42, "common": 0.38, "mid": 0.17, "rare": 0.03}
    },
    "NGA": {
        "given": {"very_common": 0.50, "common": 0.33, "mid": 0.15, "rare": 0.02},
        "surname": {"very_common": 0.40, "common": 0.40, "mid": 0.18, "rare": 0.02}
    }
}

# England (ENG) name pools
ENG_GIVEN_NAMES_MALE = {
    "very_common": [
        "Aaron", "Adam", "Adrian", "Alan", "Alex", "Alexander", "Andrew", "Anthony", "Arthur", "Ben", "Benjamin", "Bradley",
        "Callum", "Carl", "Charles", "Chris", "Christian", "Christopher", "Colin", "Connor", "Craig", "Daniel", "David", "Dean",
        "Dylan", "Edward", "Elliot", "Ethan", "Finley", "Francis", "George", "Graham", "Harry", "Henry", "Hugh", "Ian",
        "Jack", "Jacob", "James", "Jamie", "Jason", "John", "Jonathan", "Jordan", "Joseph", "Josh", "Joshua", "Karl",
        "Kieran", "Kyle", "Lee", "Liam", "Logan", "Luke", "Mark", "Martin", "Matthew", "Max", "Michael", "Nathan",
        "Nicholas", "Oliver", "Oscar", "Owen", "Paul", "Peter", "Philip", "Robert", "Ryan", "Sam", "Samuel", "Scott",
        "Sean", "Stephen", "Steven", "Thomas", "Tim", "Toby", "Tom", "William"
    ],
    "common": [
        "Alfie", "Angus", "Archie", "Barry", "Blake", "Brandon", "Cameron", "Carter", "Charlie", "Cliff", "Curtis", "Damian",
        "Darren", "Dominic", "Douglas", "Eddie", "Edmund", "Ewan", "Felix", "Freddie", "Frederick", "Gareth", "Gary", "Gavin",
        "Geoff", "Glen", "Grant", "Greg", "Harvey", "Harrison", "Heath", "Isaac", "Jake", "Jasper", "Jay", "Jenson",
        "Jerome", "Joe", "Joel", "Jon", "Julian", "Justin", "Keith", "Kevin", "Lewis", "Leo", "Leon", "Lloyd",
        "Marcus", "Mason", "Miles", "Mitchell", "Mohammed", "Morgan", "Neil", "Niall", "Noah", "Patrick", "Reece", "Ricky",
        "Ross", "Ruben", "Shaun", "Shane", "Simon", "Stanley", "Theo", "Tristan", "Tyler", "Victor", "Wayne", "Zachary"
    ],
    "mid": [
        "Aiden", "Alistair", "Amos", "Ashton", "Bailey", "Benedict", "Brett", "Caleb", "Cedric", "Chester", "Cody", "Cooper",
        "Dale", "Damon", "Darius", "Declan", "Derek", "Elliott", "Emmett", "Ernest", "Evan", "Fergus", "Frank", "Freeman",
        "Hamish", "Hayden", "Hector", "Jude", "Keaton", "Kendall", "Kirk", "Lachlan", "Laurence", "Lawrence", "Malcolm", "Marvin",
        "Micah", "Miles", "Milo", "Nate", "Nigel", "Noel", "Norman", "Perry", "Quentin", "Ralph", "Reginald", "Robin",
        "Rory", "Rupert", "Sidney", "Spencer", "Terry", "Trevor", "Vince", "Wesley", "Xavier", "Zane"
    ],
    "rare": [
        "Alban", "Alfred", "Ambrose", "Ansel", "Arlo", "Barnaby", "Basil", "Bowie", "Casper", "Cecil", "Crispin", "Cyril",
        "Dexter", "Digby", "Edgar", "Ellis", "Errol", "Fabian", "Godfrey", "Hadrian", "Humphrey", "Isidore", "Jethro", "Kingsley",
        "Lorcan", "Lucian", "Merrick", "Montgomery", "Morris", "Oswald", "Piers", "Quincy", "Roderick", "Roland", "Seth", "Thaddeus",
        "Ulysses", "Wilfred", "Winston", "Zebedee"
    ]
}

ENG_SURNAMES = {
    "very_common": [
        "Adams", "Allen", "Anderson", "Bailey", "Baker", "Barnes", "Bell", "Bennett", "Brown", "Butler", "Campbell", "Carter",
        "Clark", "Collins", "Cook", "Cooper", "Cox", "Davies", "Davis", "Edwards", "Evans", "Foster", "Garcia", "Graham",
        "Gray", "Green", "Hall", "Harris", "Harrison", "Hill", "Hughes", "Jackson", "James", "Jenkins", "Johnson", "Jones",
        "Kelly", "King", "Knight", "Lee", "Lewis", "Marshall", "Martin", "Mason", "Miller", "Mitchell", "Moore", "Morgan",
        "Morris", "Murphy", "Nelson", "Parker", "Phillips", "Price", "Reid", "Richards", "Richardson", "Roberts", "Robinson", "Rogers",
        "Russell", "Scott", "Shaw", "Simpson", "Smith", "Stewart", "Taylor", "Thomas", "Thompson", "Turner", "Walker", "Ward",
        "Watson", "White", "Williams", "Wilson", "Wood", "Wright", "Young"
    ],
    "common": [
        "Armstrong", "Atkinson", "Austin", "Baldwin", "Barrett", "Barton", "Bates", "Beck", "Bishop", "Booth", "Bowen", "Bradley",
        "Brooks", "Burton", "Byrne", "Cameron", "Chapman", "Clarke", "Cole", "Crawford", "Cunningham", "Curtis", "Dawson", "Day",
        "Dixon", "Douglas", "Doyle", "Duncan", "Ellis", "Ferguson", "Fisher", "Fleming", "Ford", "Fox", "Francis", "Gardner",
        "Gibson", "Gordon", "Griffin", "Hamilton", "Harper", "Hawkins", "Hayes", "Henderson", "Holland", "Hopkins", "Howard", "Hudson",
        "Hunter", "Jennings", "Kennedy", "Lambert", "Lawrence", "Lloyd", "Lowe", "Matthews", "May", "Miles", "Murray", "Newman",
        "Nicholson", "Owen", "Palmer", "Pearson", "Perkins", "Perry", "Porter", "Powell", "Quinn", "Ray", "Reynolds", "Rose",
        "Saunders", "Sharp", "Spencer", "Stone", "Sutton", "Wallace", "Walsh", "Webb", "Wells", "Wheeler", "Woods", "Warren"
    ],
    "mid": [
        "Abbott", "Ainsworth", "Baxter", "Benson", "Black", "Bolton", "Bond", "Bright", "Buckley", "Burns", "Carlisle", "Carr",
        "Chandler", "Christie", "Coleman", "Conway", "Dale", "Dalton", "Drake", "Eaton", "Emerson", "Fenton", "Finch", "Fry",
        "Giles", "Gill", "Goodman", "Graves", "Hale", "Hardy", "Hodges", "Howe", "Ingram", "Jarvis", "Kerr", "Lang",
        "Lennon", "Little", "Mann", "Metcalfe", "Monroe", "Nash", "Norris", "Osborne", "Peacock", "Poole", "Pope", "Reeves",
        "Rowe", "Sawyer", "Shepherd", "Skinner", "Slater", "Swan", "Thornton", "Tucker", "Vaughan", "Watts", "Weaver", "West"
    ],
    "rare": [
        "Aldridge", "Ashworth", "Beaumont", "Bicknell", "Bridger", "Chadwick", "Chamberlain", "Crompton", "Danvers", "Devereux", "Farquhar", "Featherstone",
        "Fitzpatrick", "Fleetwood", "Godwin", "Goodfellow", "Harmsworth", "Hatherley", "Hollingworth", "Ketteridge", "Kingsnorth", "Lansbury", "Molesworth", "Netherby",
        "Oxlade", "Pritchard", "Quarles", "Ravenhill", "Satterthwaite", "Templeton", "Thornhill", "Windermere", "Wooldridge", "Yarborough"
    ]
}

# France (FRA) name pools
FRA_GIVEN_NAMES_MALE = {
    "very_common": [
        "Adam", "Adrien", "Alexandre", "Antoine", "Arthur", "Axel", "Baptiste", "Benjamin", "Charles", "Clément", "Damien", "Daniel",
        "David", "Enzo", "Étienne", "Félix", "Florian", "François", "Gabriel", "Hugo", "Julien", "Kévin", "Léo", "Louis",
        "Lucas", "Mathieu", "Maxime", "Michel", "Nicolas", "Noah", "Olivier", "Paul", "Pierre", "Quentin", "Rayan", "Rémi",
        "Robin", "Samuel", "Simon", "Théo", "Thomas", "Timothée", "Tristan", "Valentin", "Victor", "William", "Yanis"
    ],
    "common": [
        "Alban", "Amaury", "Bastien", "Bruno", "Cédric", "Christophe", "Dimitri", "Émile", "Fabien", "Gaël", "Gauthier", "Gérard",
        "Guillaume", "Henri", "Jérôme", "Jonathan", "Jordan", "Kylian", "Laurent", "Loïc", "Lorenzo", "Marcel", "Marco", "Mathis",
        "Mehdi", "Mickaël", "Nathan", "Nohan", "Pascal", "Romain", "Sacha", "Stéphane", "Sylvain", "Tanguy", "Thibault", "Yohan"
    ],
    "mid": [
        "Anatole", "Armand", "Arnaud", "Augustin", "Benoît", "Cyril", "Denis", "Eliott", "Evan", "Fabrice", "Frédéric", "Georges",
        "Grégory", "Ismaël", "Jean", "Joël", "Jules", "Lamine", "Luc", "Malo", "Manuel", "Matteo", "Moussa", "Nassim",
        "Norbert", "Raphaël", "Sébastien", "Serge", "Sylvio", "Vianney", "Youssef", "Zinedine"
    ],
    "rare": [
        "Alphonse", "Ambroise", "Anselme", "Apolline", "Arsène", "Barnabé", "Célestin", "Côme", "Cyprien", "Eloi", "Gaston", "Godefroy",
        "Hippolyte", "Isidore", "Lazare", "Loup", "Marin", "Marius", "Octave", "Omer", "Prosper", "Renaud", "Simeon", "Ulysse"
    ]
}

FRA_SURNAMES = {
    "very_common": [
        "Andre", "Bernard", "Bertrand", "Blanc", "Bonnet", "Boucher", "Boyer", "Brun", "Carpentier", "Colin", "David", "Dubois",
        "Dufour", "Dupont", "Durand", "Fabre", "Faure", "Fournier", "Francois", "Garcia", "Garnier", "Girard", "Guerin", "Henry",
        "Lambert", "Laurent", "Lefebvre", "Legrand", "Lemaire", "Lemoine", "Leroy", "Martinez", "Masson", "Mathieu", "Mercier", "Michel",
        "Moreau", "Muller", "Nguyen", "Noel", "Perrin", "Petit", "Philippe", "Renard", "Richard", "Riviere", "Robert", "Roux",
        "Simon", "Thomas", "Vidal"
    ],
    "common": [
        "Adam", "Aubert", "Barbier", "Benard", "Besson", "Boulanger", "Bourgeois", "Bouvier", "Briand", "Chauvin", "Chevalier", "Clement",
        "Cousin", "Da Silva", "Delattre", "Deschamps", "Duval", "Etienne", "Fernandez", "Fontaine", "Gauthier", "Gillet", "Gomez", "Goncalves",
        "Hubert", "Jacob", "Joly", "Klein", "Lacroix", "Lamy", "Lemoine", "Leclerc", "Lopez", "Marchand", "Marin", "Maurice",
        "Meyer", "Morin", "Pereira", "Poirier", "Prevost", "Rey", "Renaud", "Rolland", "Rousseau", "Schmitt", "Schneider", "Vasseur"
    ],
    "mid": [
        "Arnaud", "Bailly", "Baron", "Bazin", "Beaumont", "Benoit", "Bertin", "Bourdon", "Boutin", "Camus", "Charlier", "Charpentier",
        "Couturier", "Delaunay", "Delorme", "Dumont", "Foucher", "Giraud", "Grondin", "Hamel", "Hardy", "Hebert", "Lachance", "Langlois",
        "Lejeune", "Lombard", "Mallet", "Maréchal", "Michaud", "Monnier", "Pichon", "Roch", "Serra", "Teixeira", "Valette", "Verdier"
    ],
    "rare": [
        "Aumont", "Beaufort", "Bellec", "Chateauneuf", "Courtois", "d'Artois", "de Montfort", "Desmarais", "d'Orléans", "Fontenay", "Guillemet", "LaFleur",
        "Montmorency", "Pélissier", "Queneau", "Saint-Clair", "Saint-Pierre", "Talleyrand", "Villedieu", "Watteau"
    ]
}

# Nigeria (NGA) name pools
NGA_GIVEN_NAMES_MALE = {
    "very_common": [
        "Abdul", "Abdullahi", "Abubakar", "Ahmed", "Akin", "Akinola", "Ali", "Bello", "Chidi", "Chidiebere", "Chigozie", "Chijioke",
        "Chukwuemeka", "Chukwudi", "David", "Emeka", "Emmanuel", "Ezekiel", "Farouk", "Femi", "Francis", "Godwin", "Hassan", "Ibrahim",
        "Idris", "Ifeanyi", "Ikechukwu", "Ikenna", "Isa", "Ismail", "Jacob", "James", "Joseph", "Joshua", "Kelechi", "Kingsley",
        "Lawal", "Moses", "Muhammad", "Musa", "Mustapha", "Nnamdi", "Obinna", "Okechukwu", "Oladele", "Olamide", "Oluwaseun", "Peter",
        "Samuel", "Sani", "Segun", "Suleiman", "Tunde", "Uche", "Umar", "Victor", "Yusuf"
    ],
    "common": [
        "Abel", "Ade", "Adebayo", "Adegoke", "Adewale", "Adeyemi", "Afolabi", "Akinyemi", "Chibueze", "Chibuzo", "Chinedu", "Chinonso",
        "Chinweike", "Daniel", "Ebuka", "Enoch", "Ephraim", "Gideon", "Haruna", "Ifeoluwa", "Ike", "Iken", "Ishaq", "Jibril",
        "Johnson", "Kayode", "Kola", "Lukman", "Malam", "Michael", "Najeeb", "Nathaniel", "Nwafor", "Obi", "Oke", "Olatunde",
        "Oluwatobi", "Onyeka", "Raphael", "Sadiq", "Saviour", "Shehu", "Taiwo", "Temitope", "Tope", "Usman", "Yakubu"
    ],
    "mid": [
        "Abiola", "Adamu", "Adedayo", "Adetayo", "Adisa", "Akeem", "Akinwumi", "Amadi", "Bashir", "Chima", "Chimdi", "Chukwuka",
        "Danjuma", "Dare", "Dayo", "Ebere", "Efe", "Ekenedilichukwu", "Eromosele", "Ikenna", "Izu", "Khamzat", "Kolawole", "Kunle",
        "Nnaemeka", "Nneka", "Obasi", "Oche", "Oghenekaro", "Oghenetega", "Ojo", "Okafor", "Okonkwo", "Olumide", "Onyekachi", "Orji",
        "Salisu", "Sunday", "Uchenna", "Ugochukwu"
    ],
    "rare": [
        "Akintunde", "Ayomide", "Chukwunonso", "Chukwuma", "Efeosa", "Ejiro", "Ekenna", "Ifechukwu", "Ifeoma", "Ikenye", "Kamsiyochukwu", "Kenechukwu",
        "Nkemakonam", "Nwachukwu", "Obumneme", "Oghene", "Okezie", "Olaitan", "Oluwafemi", "Oluwakayode", "Onwubiko", "Udochukwu", "Ugo", "Uzoma"
    ]
}

NGA_SURNAMES = {
    "very_common": [
        "Abubakar", "Adamu", "Adebayo", "Adeyemi", "Afolabi", "Ahmad", "Ahmed", "Akande", "Akinyemi", "Aliyu", "Bello", "Danladi",
        "Eze", "Ibrahim", "Idris", "Isah", "Jibril", "Lawal", "Musa", "Mustapha", "Nwachukwu", "Nwosu", "Obi", "Okafor",
        "Okeke", "Okonkwo", "Olawale", "Olayinka", "Oluwole", "Onyeka", "Sani", "Shehu", "Suleiman", "Usman", "Yakubu", "Yusuf"
    ],
    "common": [
        "Abiola", "Adedayo", "Adegoke", "Adelaja", "Adeniyi", "Adesina", "Adekunle", "Adeola", "Ajayi", "Akintola", "Alabi", "Amadi",
        "Anyanwu", "Balogun", "Bashir", "Chukwu", "Ekwueme", "Ezeh", "Ezenwa", "Iheanacho", "Ike", "Ikenna", "Iroegbu", "James",
        "Mohammed", "Nnamdi", "Nwankwo", "Obasi", "Obinna", "Odunayo", "Ogunleye", "Ojo", "Okoro", "Okwu", "Olaniyan", "Olatunji",
        "Olorunfemi", "Oluwaseun", "Onyema", "Onyekuru", "Orji", "Sadiq", "Salisu", "Tijani", "Uche", "Umar", "Yahaya"
    ],
    "mid": [
        "Abdullahi", "Adetokunbo", "Akinwale", "Akinwumi", "Chibueze", "Chibuzo", "Chinedu", "Chinonso", "Danbaba", "Danjuma", "Ebere",
        "Ekwere", "Emefiele", "Eromosele", "Ifeanyi", "Ifeoma", "Igwe", "Iroha", "Kelechi", "Kolawole", "Nwafor", "Nworie", "Obafemi",
        "Oche", "Odili", "Odogwu", "Oghene", "Okechukwu", "Okezie", "Okoli", "Oluwadare", "Oluwatobi", "Onwubiko", "Onyekachi", "Uchenna",
        "Ugochukwu", "Uzoma"
    ],
    "rare": [
        "Akinjide", "Chukwunonso", "Ekenedilichukwu", "Ezeanwu", "Ifechukwu", "Iroegbu-Okoye", "Nkemakonam", "Nnaemeka", "Obumneme", "Oghenetega",
        "Oluwakayode", "Onyejekwe", "Udochukwu", "Umeadi", "Uzodimma"
    ]
}

# Heritage groups for England (ENG)
ENG_HERITAGE_GROUPS = {
    "ENG_Mainstream": {
        "weight": 0.70,  # 70% of ENG players
        "origin_country_weights": {"ENG": 1.0},
        "name_structure_probs": {
            "LL": 1.00,  # LOCAL given, LOCAL surname
            "LH": 0.00,  # LOCAL given, HERITAGE surname
            "HL": 0.00,  # HERITAGE given, LOCAL surname
            "HH": 0.00   # HERITAGE given, HERITAGE surname
        }
    },
    "ENG_WestAfrica": {
        "weight": 0.30,
        "origin_country_weights": {
            "NGA": 0.40,  # Nigeria
            "GHA": 0.30,  # Ghana
            "SEN": 0.15,  # Senegal
            "CIV": 0.10,  # Ivory Coast
            "CMR": 0.05   # Cameroon
        },
        "name_structure_probs": {
            "LL": 0.20,
            "LH": 0.30,
            "HL": 0.20,
            "HH": 0.30
        }
    },
    "ENG_Caribbean": {
        "weight": 0.00,
        "origin_country_weights": {
            "JAM": 0.50,  # Jamaica
            "TTO": 0.25,  # Trinidad & Tobago
            "BRB": 0.15,  # Barbados
            "GUY": 0.10   # Guyana
        },
        "name_structure_probs": {
            "LL": 0.15,
            "LH": 0.35,
            "HL": 0.25,
            "HH": 0.25
        }
    },
    "ENG_SouthAsia": {
        "weight": 0.00,
        "origin_country_weights": {
            "IND": 0.50,  # India
            "PAK": 0.30,  # Pakistan
            "BGD": 0.15,  # Bangladesh
            "LKA": 0.05   # Sri Lanka
        },
        "name_structure_probs": {
            "LL": 0.10,
            "LH": 0.40,
            "HL": 0.30,
            "HH": 0.20
        }
    },
    "ENG_EastEurope": {
        "weight": 0.00,
        "origin_country_weights": {
            "POL": 0.40,  # Poland
            "ROU": 0.25,  # Romania
            "CZE": 0.20,  # Czech Republic
            "HUN": 0.15   # Hungary
        },
        "name_structure_probs": {
            "LL": 0.25,
            "LH": 0.30,
            "HL": 0.25,
            "HH": 0.20
        }
    }
}

# Placeholder name pools for heritage origin countries (to be expanded)
# Note: NGA is now in COUNTRY_NAME_POOLS above
HERITAGE_NAME_POOLS = {
    "GHA": {  # Ghana
        "given_names_male": {
            "very_common": ["Kwame", "Kofi", "Kwaku", "Yaw", "Kojo", "Fiifi"],
            "common": ["Akwasi", "Akwesi", "Afi", "Ama", "Efua", "Akosua"],
            "mid": ["Kobina", "Kweku", "Kwabena", "Yaw", "Akwasi", "Ama"],
            "rare": ["Nana", "Osei", "Asante", "Agyeman", "Bonsu", "Mensah"]
        },
        "surnames": {
            "very_common": ["Mensah", "Asante", "Agyeman", "Bonsu", "Osei", "Appiah"],
            "common": ["Owusu", "Boateng", "Darko", "Amoah", "Adjei", "Sarpong"],
            "mid": ["Acheampong", "Gyasi", "Frimpong", "Antwi", "Amoako", "Baffour"],
            "rare": ["Nkrumah", "Danquah", "Busia", "Rawlings", "Kufuor", "Mills"]
        }
    },
    "JAM": {  # Jamaica
        "given_names_male": {
            "very_common": ["Marcus", "Andre", "Dwayne", "Tyrone", "Jamal", "Kareem"],
            "common": ["Jermaine", "Deshawn", "Trevon", "Malik", "Darius", "Cedric"],
            "mid": ["Khalil", "Rashad", "DeAndre", "Marquis", "Tariq", "Jalen"],
            "rare": ["Zaire", "Kendrick", "Javon", "Tavon", "Darnell", "Lamar"]
        },
        "surnames": {
            "very_common": ["Brown", "Williams", "Johnson", "Jones", "Davis", "Miller"],
            "common": ["Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson"],
            "mid": ["Thompson", "White", "Harris", "Martin", "Thompson", "Garcia"],
            "rare": ["Robinson", "Clark", "Rodriguez", "Lewis", "Lee", "Walker"]
        }
    },
    "IND": {  # India
        "given_names_male": {
            "very_common": ["Raj", "Amit", "Rahul", "Vikram", "Arjun", "Rohan"],
            "common": ["Siddharth", "Karan", "Aditya", "Nikhil", "Ravi", "Anil"],
            "mid": ["Varun", "Rishabh", "Kunal", "Harsh", "Yash", "Dev"],
            "rare": ["Arnav", "Ishaan", "Vihaan", "Ayaan", "Advik", "Atharv"]
        },
        "surnames": {
            "very_common": ["Patel", "Shah", "Kumar", "Singh", "Sharma", "Gupta"],
            "common": ["Mehta", "Desai", "Joshi", "Agarwal", "Malhotra", "Reddy"],
            "mid": ["Kapoor", "Verma", "Nair", "Iyer", "Menon", "Pillai"],
            "rare": ["Chopra", "Bhatt", "Saxena", "Tiwari", "Dwivedi", "Mishra"]
        }
    }
}

# Country name pool structure
COUNTRY_NAME_POOLS: Dict[str, Dict] = {
    "ENG": {
        "given_names_male": ENG_GIVEN_NAMES_MALE,
        "surnames": ENG_SURNAMES
    },
    "FRA": {
        "given_names_male": FRA_GIVEN_NAMES_MALE,
        "surnames": FRA_SURNAMES
    },
    "NGA": {
        "given_names_male": NGA_GIVEN_NAMES_MALE,
        "surnames": NGA_SURNAMES
    }
}

# Add heritage origin country pools to main structure (only if not already present)
for country_code, pools in HERITAGE_NAME_POOLS.items():
    if country_code not in COUNTRY_NAME_POOLS:
        COUNTRY_NAME_POOLS[country_code] = pools

# Heritage group configurations by nationality
HERITAGE_CONFIG: Dict[str, Dict] = {
    "ENG": ENG_HERITAGE_GROUPS
}

# Mapping from heritage groups to picture folders
HERITAGE_PICTURE_FOLDER_MAP: Dict[str, str] = {
    "ENG_Mainstream": "BritishIsles",
    "ENG_WestAfrica": "AfricaWest",
    "ENG_Caribbean": "Anglosphere",  # Fallback until specific folder exists
    "ENG_SouthAsia": "Anglosphere",  # Fallback until specific folder exists
    "ENG_EastEurope": "Anglosphere",  # Fallback until specific folder exists
}

# Middle name probabilities (per country)
MIDDLE_NAME_PROBS: Dict[str, float] = {
    "ENG": 0.22,  # 22% of UK players have middle names
    "FRA": 0.18,  # 18% of French players have middle names
    "NGA": 0.10,  # 10% of Nigerian players have middle names
    "default": 0.15
}

# Compound surname probabilities and connectors (per country)
COMPOUND_SURNAME_PROBS: Dict[str, float] = {
    "ENG": 0.03,  # 3% of UK players have compound surnames
    "FRA": 0.02,  # 2% of French players have compound surnames
    "NGA": 0.005,  # 0.5% of Nigerian players have compound surnames
    "default": 0.05
}

SURNAME_CONNECTORS: Dict[str, str] = {
    "ENG": "-",  # UK uses hyphen
    "FRA": "-",  # France uses hyphen
    "NGA": "-",  # Nigeria uses hyphen
    "ESP": " ",  # Spanish uses space
    "default": "-"
}

# Compound surname tier bias (for surname2)
# 70% common/common, 25% common/mid, 5% mid/mid, ~0-2% rare involvement
COMPOUND_SURNAME_TIER_BIAS = {
    ("common", "common"): 0.70,
    ("common", "mid"): 0.25,
    ("mid", "mid"): 0.05,
    ("very_common", "common"): 0.00,  # Allow but rare
    ("common", "rare"): 0.00,  # Allow but rare
    ("mid", "rare"): 0.00,  # Allow but rare
    ("rare", "rare"): 0.00   # Very rare
}
