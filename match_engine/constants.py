"""
Constants for the match engine: positions, attributes, and base values.
"""

# Available positions in the match engine
POSITIONS = [
    "DL", "DC", "DR",           # Defenders
    "DML", "DMC", "DMR",        # Defensive Midfielders
    "ML", "MC", "MR",           # Midfielders
    "OML", "OMC", "OMR",        # Offensive Midfielders
    "FC"                        # Forwards
]

# Outfield player attributes
OUTFIELD_ATTRS = [
    'Finishing', 'Tackling', 'Marking', 'Heading', 'Passing', 'Crossing', 'Ball Control',
    'Positioning', 'Vision', 'Composure', 'Work Rate',
    'Strength', 'Stamina', 'Acceleration', 'Agility', 'Jump Reach'
]

# Goalkeeper attributes
GOALKEEPER_ATTRS = [
    'Positioning', 'Command of Area', 'Composure', 'Work Rate',
    'Strength', 'Stamina', 'Acceleration', 'Agility', 'Jump Reach',
    'Reflexes', 'Handling', 'One-on-One', 'Aerial Reach'
]

# Chance types
CHANCE_TYPES = ["Short", "Long", "Crossing", "Through", "Solo"]

# Finish types
FINISH_TYPES = ["FirstTime", "Controlled", "Header", "Chip", "Finesse", "Power"]
