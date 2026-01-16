"""
Matrix definitions and matrix building functions for match simulation.
"""

import random
from typing import Dict, Tuple
from .models import Team
from .constants import POSITIONS, CHANCE_TYPES


# ============ BASE MATRICES ============

# Base creator matrix: position -> base chance creation weight
BASE_CREATOR_MATRIX = {
    "DL": 6, "DC": 1, "DR": 6,
    "DML": 10, "DMC": 6, "DMR": 10,
    "ML": 10, "MC": 10, "MR": 10,
    "OML": 12, "OMC": 15, "OMR": 12,
    "FC": 12
}

# Creator -> Defender matrix: which defenders contest which creators
BASE_CREATOR_DEFEND_MATRIX = {
    "DL":  {"DL": 0,   "DC": 1,   "DR": 50,  "DML": 0,   "DMC": 30,  "DMR": 50,  "ML": 0,   "MC": 50,  "MR": 100, "OML": 0,   "OMC": 0,   "OMR": 100, "FC": 50},
    "DC":  {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 30,  "MC": 50,  "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 100},
    "DR":  {"DL": 50,  "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 100, "MC": 100, "MR": 0,   "OML": 50,  "OMC": 100, "OMR": 50,  "FC": 100},
    "DML": {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 0,   "MC": 50,  "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "DMC": {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 100, "DMC": 50,  "DMR": 0,   "ML": 0,   "MC": 50,  "MR": 0,   "OML": 100, "OMC": 0,   "OMR": 0,   "FC": 0},
    "DMR": {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 50,  "DMR": 0,   "ML": 0,   "MC": 0,   "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "ML":  {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 100, "MC": 50,  "MR": 100, "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "MC":  {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 10,   "DMC": 50,  "DMR": 10,   "ML": 10,   "MC": 50,  "MR": 10,   "OML": 10,   "OMC": 10,   "OMR": 10,   "FC": 0},
    "MR":  {"DL": 100, "DC": 50,  "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 0,   "MC": 0,   "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "OML": {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 0,   "MC": 0,   "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "OMC": {"DL": 50,  "DC": 50,  "DR": 0,   "DML": 100, "DMC": 50,  "DMR": 0,   "ML": 0,   "MC": 0,   "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 30,  "FC": 0},
    "OMR": {"DL": 100, "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 0,   "MC": 0,   "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "FC":  {"DL": 50,  "DC": 100, "DR": 50,  "DML": 10,  "DMC": 0,   "DMR": 10,  "ML": 0,   "MC": 0,   "MR": 0,   "OML": 10,  "OMC": 0,   "OMR": 0,   "FC": 0},
}

# Creator -> Chance Type matrix
CREATOR_CHANCE_TYPE_MATRIX = {
    "DL":  {"Short": 15, "Long": 15, "Crossing": 55, "Through": 10, "Solo": 5},
    "DC":  {"Short": 20, "Long": 65, "Crossing": 5, "Through": 10, "Solo": 0},
    "DR":  {"Short": 15, "Long": 15, "Crossing": 55, "Through": 10, "Solo": 5},
    "DML": {"Short": 20, "Long": 15, "Crossing": 45, "Through": 15, "Solo": 5},
    "DMC": {"Short": 40, "Long": 35, "Crossing": 5, "Through": 15, "Solo": 5},
    "DMR": {"Short": 20, "Long": 15, "Crossing": 45, "Through": 15, "Solo": 5},
    "ML":  {"Short": 25, "Long": 5, "Crossing": 45, "Through": 10, "Solo": 15},
    "MC":  {"Short": 40, "Long": 20, "Crossing": 5, "Through": 25, "Solo": 10},
    "MR":  {"Short": 25, "Long": 5, "Crossing": 45, "Through": 10, "Solo": 15},
    "OML": {"Short": 15, "Long": 5, "Crossing": 40, "Through": 15, "Solo": 25},
    "OMC": {"Short": 40, "Long": 5, "Crossing": 5, "Through": 30, "Solo": 20},
    "OMR": {"Short": 15, "Long": 5, "Crossing": 40, "Through": 15, "Solo": 25},
    "FC":  {"Short": 35, "Long": 5, "Crossing": 5, "Through": 25, "Solo": 30},
}

# Finisher matrices by chance type
BASE_FINISHER_SHORT_PASS_MATRIX = {
    "DL":  {"DL": 0, "DC": 30, "DR": 0, "DML": 0, "DMC": 50, "DMR": 0, "ML": 100, "MC": 100, "MR": 0, "OML": 100, "OMC": 50, "OMR": 0, "FC": 50},
    "DC":  {"DL": 50, "DC": 0, "DR": 50, "DML": 100, "DMC": 100, "DMR": 100, "ML": 100, "MC": 100, "MR": 100, "OML": 100, "OMC": 100, "OMR": 100, "FC": 50},
    "DR":  {"DL": 0, "DC": 30, "DR": 0, "DML": 0, "DMC": 50, "DMR": 0, "ML": 0, "MC": 100, "MR": 100, "OML": 0, "OMC": 50, "OMR": 100, "FC": 50},
    "DML": {"DL": 0, "DC": 30, "DR": 0, "DML": 0, "DMC": 50, "DMR": 0, "ML": 100, "MC": 100, "MR": 0, "OML": 100, "OMC": 50, "OMR": 0, "FC": 50},
    "DMC": {"DL": 0, "DC": 0, "DR": 0, "DML": 50, "DMC": 50, "DMR": 50, "ML": 100, "MC": 100, "MR": 100, "OML": 100, "OMC": 100, "OMR": 100, "FC": 50},
    "DMR": {"DL": 0, "DC": 30, "DR": 0, "DML": 0, "DMC": 50, "DMR": 0, "ML": 0, "MC": 100, "MR": 100, "OML": 0, "OMC": 50, "OMR": 100, "FC": 50},
    "ML":  {"DL": 30, "DC": 0, "DR": 0, "DML": 30, "DMC": 100, "DMR": 0, "ML": 0, "MC": 100, "MR": 0, "OML": 0, "OMC": 100, "OMR": 0, "FC": 50},
    "MC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 30, "DMC": 50, "DMR": 30, "ML": 100, "MC": 100, "MR": 100, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "MR":  {"DL": 0, "DC": 0, "DR": 30, "DML": 0, "DMC": 100, "DMR": 30, "ML": 0, "MC": 100, "MR": 0, "OML": 0, "OMC": 100, "OMR": 0, "FC": 50},
    "OML": {"DL": 30, "DC": 0, "DR": 0, "DML": 30, "DMC": 30, "DMR": 0, "ML": 0, "MC": 50, "MR": 0, "OML": 0, "OMC": 100, "OMR": 0, "FC": 100},
    "OMC": {"DL": 0, "DC": 0, "DR": 0, "DML": 30, "DMC": 30, "DMR": 30, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "OMR": {"DL": 0, "DC": 0, "DR": 30, "DML": 0, "DMC": 30, "DMR": 30, "ML": 0, "MC": 50, "MR": 0, "OML": 0, "OMC": 100, "OMR": 0, "FC": 100},
    "FC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 30, "DMC": 30, "DMR": 30, "ML": 30, "MC": 50, "MR": 30, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
}

BASE_FINISHER_CROSSING_MATRIX = {
    "DL":  {"DL": 0, "DC": 0, "DR": 30, "DML": 0, "DMC": 30, "DMR": 30, "ML": 0, "MC": 50, "MR": 50, "OML": 0, "OMC": 100, "OMR": 50, "FC": 100},
    "DC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "DR":  {"DL": 30, "DC": 0, "DR": 0, "DML": 30, "DMC": 30, "DMR": 0, "ML": 50, "MC": 50, "MR": 0, "OML": 50, "OMC": 100, "OMR": 0, "FC": 100},
    "DML": {"DL": 0, "DC": 0, "DR": 30, "DML": 0, "DMC": 30, "DMR": 30, "ML": 0, "MC": 50, "MR": 50, "OML": 0, "OMC": 50, "OMR": 50, "FC": 100},
    "DMC": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "DMR": {"DL": 30, "DC": 0, "DR": 0, "DML": 30, "DMC": 30, "DMR": 0, "ML": 50, "MC": 50, "MR": 0, "OML": 50, "OMC": 50, "OMR": 0, "FC": 100},
    "ML":  {"DL": 0, "DC": 0, "DR": 30, "DML": 0, "DMC": 30, "DMR": 30, "ML": 0, "MC": 50, "MR": 50, "OML": 0, "OMC": 50, "OMR": 100, "FC": 100},
    "MC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "MR":  {"DL": 30, "DC": 0, "DR": 0, "DML": 30, "DMC": 30, "DMR": 0, "ML": 50, "MC": 50, "MR": 0, "OML": 100, "OMC": 50, "OMR": 0, "FC": 100},
    "OML": {"DL": 0, "DC": 0, "DR": 30, "DML": 0, "DMC": 30, "DMR": 30, "ML": 0, "MC": 50, "MR": 50, "OML": 0, "OMC": 50, "OMR": 100, "FC": 100},
    "OMC": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "OMR": {"DL": 30, "DC": 0, "DR": 0, "DML": 30, "DMC": 30, "DMR": 0, "ML": 50, "MC": 50, "MR": 0, "OML": 100, "OMC": 50, "OMR": 0, "FC": 100},
    "FC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
}

BASE_FINISHER_THROUGH_MATRIX = {
    "DL":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 0, "OML": 50, "OMC": 100, "OMR": 30, "FC": 100},
    "DC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "DR":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 0, "MC": 50, "MR": 50, "OML": 30, "OMC": 100, "OMR": 50, "FC": 100},
    "DML": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 0, "OML": 100, "OMC": 100, "OMR": 50, "FC": 100},
    "DMC": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 30, "MC": 50, "MR": 30, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "DMR": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 0, "MC": 50, "MR": 50, "OML": 50, "OMC": 100, "OMR": 100, "FC": 100},
    "ML":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 0, "MC": 30, "MR": 0, "OML": 0, "OMC": 100, "OMR": 50, "FC": 100},
    "MC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 30, "MC": 30, "MR": 30, "OML": 100, "OMC": 100, "OMR": 100, "FC": 1000},
    "MR":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 0, "MC": 30, "MR": 0, "OML": 50, "OMC": 100, "OMR": 0, "FC": 100},
    "OML": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 0, "MC": 50, "MR": 30, "OML": 0, "OMC": 100, "OMR": 50, "FC": 100},
    "OMC": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "OMR": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 30, "MC": 50, "MR": 0, "OML": 50, "OMC": 100, "OMR": 0, "FC": 100},
    "FC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 30, "MC": 30, "MR": 30, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
}

BASE_FINISHER_LONG_PASS_MATRIX = {
    "DL":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "DC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "DR":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "DML": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "DMC": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 30, "MC": 30, "MR": 30, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "DMR": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 50, "MR": 50, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "ML":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 0, "MC": 30, "MR": 30, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "MC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 50, "MC": 0, "MR": 50, "OML": 100, "OMC": 50, "OMR": 100, "FC": 100},
    "MR":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 30, "MC": 30, "MR": 0, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "OML": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 30, "MC": 30, "MR": 30, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "OMC": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 30, "MC": 30, "MR": 30, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "OMR": {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 30, "MC": 30, "MR": 30, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
    "FC":  {"DL": 0, "DC": 0, "DR": 0, "DML": 0, "DMC": 0, "DMR": 0, "ML": 30, "MC": 30, "MR": 30, "OML": 100, "OMC": 100, "OMR": 100, "FC": 100},
}

# Finisher -> Defender matrix
BASE_FINISH_DEFEND_MATRIX = {
    "DL":  {"DL": 0,   "DC": 1,   "DR": 50,  "DML": 0,   "DMC": 30,  "DMR": 50,  "ML": 0,   "MC": 50,  "MR": 100, "OML": 0,   "OMC": 0,   "OMR": 100, "FC": 50},
    "DC":  {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 30,  "MC": 50,  "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 100},
    "DR":  {"DL": 50,  "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 100, "MC": 100, "MR": 0,   "OML": 50,  "OMC": 100, "OMR": 50,  "FC": 100},
    "DML": {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 0,   "MC": 50,  "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "DMC": {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 100, "DMC": 50,  "DMR": 0,   "ML": 0,   "MC": 50,  "MR": 0,   "OML": 100, "OMC": 0,   "OMR": 0,   "FC": 0},
    "DMR": {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 50,  "DMR": 0,   "ML": 0,   "MC": 0,   "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "ML":  {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 100, "MC": 50,  "MR": 100, "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "MC":  {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 10,   "DMC": 50,  "DMR": 10,   "ML": 10,   "MC": 50,  "MR": 10,   "OML": 10,   "OMC": 10,   "OMR": 10,   "FC": 0},
    "MR":  {"DL": 100, "DC": 50,  "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 0,   "MC": 0,   "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "OML": {"DL": 0,   "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 0,   "MC": 0,   "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "OMC": {"DL": 50,  "DC": 50,  "DR": 0,   "DML": 100, "DMC": 50,  "DMR": 0,   "ML": 0,   "MC": 0,   "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 30,  "FC": 0},
    "OMR": {"DL": 100, "DC": 1,   "DR": 0,   "DML": 0,   "DMC": 0,   "DMR": 0,   "ML": 0,   "MC": 0,   "MR": 0,   "OML": 0,   "OMC": 0,   "OMR": 0,   "FC": 0},
    "FC":  {"DL": 50,  "DC": 100, "DR": 50,  "DML": 10,  "DMC": 0,   "DMR": 10,  "ML": 0,   "MC": 0,   "MR": 0,   "OML": 10,  "OMC": 0,   "OMR": 0,   "FC": 0},
}

# Chance Type -> Finish Type matrix
CHANCE_TO_FINISH_TYPE_MATRIX = {
    "Crossing": {"FirstTime": 20, "Controlled": 20, "Header": 55, "Chip": 0,  "Finesse": 0,  "Power": 5},
    "Long":     {"FirstTime": 20, "Controlled": 20, "Header": 35, "Chip": 5,  "Finesse": 5,  "Power": 15},
    "Short":    {"FirstTime": 25, "Controlled": 30, "Header": 2,  "Chip": 3,  "Finesse": 10, "Power": 30},
    "Through":  {"FirstTime": 25, "Controlled": 25, "Header": 10, "Chip": 15, "Finesse": 15, "Power": 10},
    "Solo":     {"FirstTime": 10, "Controlled": 25, "Header": 0,  "Chip": 10, "Finesse": 25, "Power": 30}
}


# ============ MATRIX BUILDING FUNCTIONS ============

def get_formation_count(team: Team) -> Dict[str, int]:
    """Return a dict of position code -> number of players at that position for a team."""
    formation = {pos: 0 for pos in POSITIONS}
    for player in team.players:
        pos = player.matrix_position
        if pos in formation:
            formation[pos] += 1
    return formation


def normalize_matrix(matrix: Dict[str, float]) -> Dict[str, float]:
    """Normalize a matrix so values sum to 1."""
    total = sum(matrix.values())
    if total == 0:
        return {pos: 0 for pos in matrix}
    return {pos: value / total for pos, value in matrix.items()}


def get_team_match_creator_matrix(team: Team, base_matrix: Dict[str, int] = None) -> Tuple[Dict[str, float], Dict[str, float]]:
    """Build match-specific creator matrix for a team.
    
    Returns:
        Tuple of (raw_matrix, normalized_matrix)
    """
    if base_matrix is None:
        base_matrix = BASE_CREATOR_MATRIX
    
    formation_count = get_formation_count(team)
    raw_matrix = {}
    for pos in POSITIONS:
        raw_matrix[pos] = base_matrix.get(pos, 0) * formation_count.get(pos, 0)
    
    norm_matrix = normalize_matrix(raw_matrix)
    return raw_matrix, norm_matrix


def build_match_finisher_matrix_weighted(base_matrix: Dict, team: Team) -> Dict[str, Dict[str, float]]:
    """
    For each creator (row) in base_matrix:
    - Only includes finishers in the team formation.
    - Multiplies each finisher's value by the number of players at that position.
    - Normalizes the row.
    """
    position_count = {}
    for player in team.players:
        pos = player.matrix_position
        position_count[pos] = position_count.get(pos, 0) + 1

    match_matrix = {}
    for creator, finishers in base_matrix.items():
        if creator not in position_count:
            continue
        weighted = {}
        for finisher, base_val in finishers.items():
            if finisher in position_count:
                weighted[finisher] = base_val * position_count[finisher]
        total = sum(weighted.values())
        if total > 0:
            match_matrix[creator] = {finisher: value / total for finisher, value in weighted.items()}
        else:
            match_matrix[creator] = {finisher: 0 for finisher in weighted}
    return match_matrix


def build_match_defender_matrix_weighted(
    base_matrix: Dict,
    attacking_team: Team,
    defending_team: Team
) -> Dict[str, Dict[str, float]]:
    """
    For any base defender matrix (row: attacker/creator/finisher, col: defender),
    - Row keys: Only positions present in attacking team.
    - Col keys: Only positions present in defending team.
    - Each cell is base value * (num in attack pos) * (num in defend pos)
    - Each row is normalized to sum to 1 if not all zeros.
    """
    attack_count = {}
    for p in attacking_team.players:
        k = p.matrix_position
        attack_count[k] = attack_count.get(k, 0) + 1
    
    defend_count = {}
    for p in defending_team.players:
        k = p.matrix_position
        defend_count[k] = defend_count.get(k, 0) + 1

    match_matrix = {}
    for row in base_matrix:
        if row not in attack_count:
            continue
        weighted_row = {}
        for col in base_matrix[row]:
            if col in defend_count:
                weighted_row[col] = base_matrix[row][col] * attack_count[row] * defend_count[col]
        total = sum(weighted_row.values())
        if total > 0:
            match_matrix[row] = {col: v / total for col, v in weighted_row.items()}
        else:
            match_matrix[row] = {col: 0 for col in weighted_row}
    return match_matrix


def build_solo_dribble_matrix(team: Team) -> Dict[str, Dict[str, float]]:
    """Build solo dribble matrix where creator = finisher."""
    formation_count = get_formation_count(team)
    return {pos: {pos: 1.0} for pos in POSITIONS if formation_count.get(pos, 0) > 0}


def weighted_choice(items_with_probs: Dict[str, float]) -> str:
    """Select an item based on weighted probabilities."""
    filtered = [(k, v) for k, v in items_with_probs.items() if v > 0]
    if not filtered:
        return None
    items, weights = zip(*filtered)
    return random.choices(items, weights=weights, k=1)[0]
