"""
Name data structures for realistic player name generation.

Loads country-specific name pools (tiered), heritage group definitions,
origin country mappings, and configuration for name structure probabilities
from JSON data files in the data/ directory.

To add a new country:
  1. Create data/name_pools/<COUNTRY_CODE>.json with given_names_male, surnames, etc.
  2. Optionally add tier_probs, middle_name_prob, compound_surname_prob, surname_connector.

To add heritage groups for a nationality:
  1. Create data/heritage_groups/<NATIONALITY_CODE>.json with heritage_groups config.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

# ── Paths ─────────────────────────────────────────────────────────────────────
_BASE_DIR = Path(__file__).resolve().parent.parent
_NAME_POOLS_DIR = _BASE_DIR / "data" / "name_pools"
_HERITAGE_GROUPS_DIR = _BASE_DIR / "data" / "heritage_groups"

# ── Defaults ──────────────────────────────────────────────────────────────────
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

# Compound surname tier bias (for surname2)
# 70% common/common, 25% common/mid, 5% mid/mid, ~0-2% rare involvement
COMPOUND_SURNAME_TIER_BIAS = {
    ("common", "common"): 0.70,
    ("common", "mid"): 0.25,
    ("mid", "mid"): 0.05,
    ("very_common", "common"): 0.00,
    ("common", "rare"): 0.00,
    ("mid", "rare"): 0.00,
    ("rare", "rare"): 0.00
}

# ── Load name pools from JSON ─────────────────────────────────────────────────
COUNTRY_NAME_POOLS: Dict[str, Dict] = {}
COUNTRY_TIER_PROBS: Dict[str, Dict[str, Dict[str, float]]] = {}
MIDDLE_NAME_PROBS: Dict[str, float] = {"default": 0.15}
COMPOUND_SURNAME_PROBS: Dict[str, float] = {"default": 0.05}
SURNAME_CONNECTORS: Dict[str, str] = {"default": "-"}

def _load_name_pools():
    """Load all country name pool JSON files from the data/name_pools directory."""
    if not _NAME_POOLS_DIR.exists():
        return
    
    for json_file in sorted(_NAME_POOLS_DIR.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load name pool {json_file}: {e}")
            continue
        
        code = data.get("country_code")
        if not code:
            print(f"Warning: No country_code in {json_file}, skipping")
            continue
        
        # Name pools (required)
        if "given_names_male" in data and "surnames" in data:
            COUNTRY_NAME_POOLS[code] = {
                "given_names_male": data["given_names_male"],
                "surnames": data["surnames"]
            }
        
        # Optional: tier probabilities
        if "tier_probs" in data:
            COUNTRY_TIER_PROBS[code] = data["tier_probs"]
        
        # Optional: middle name probability
        if "middle_name_prob" in data:
            MIDDLE_NAME_PROBS[code] = data["middle_name_prob"]
        
        # Optional: compound surname probability
        if "compound_surname_prob" in data:
            COMPOUND_SURNAME_PROBS[code] = data["compound_surname_prob"]
        
        # Optional: surname connector
        if "surname_connector" in data:
            SURNAME_CONNECTORS[code] = data["surname_connector"]


# ── Load heritage groups from JSON ────────────────────────────────────────────
HERITAGE_CONFIG: Dict[str, Dict] = {}
HERITAGE_PICTURE_FOLDER_MAP: Dict[str, str] = {}

# Legacy alias — some code references this; it's now a subset of COUNTRY_NAME_POOLS
HERITAGE_NAME_POOLS: Dict[str, Dict] = {}

def _load_heritage_groups():
    """Load all heritage group JSON files from the data/heritage_groups directory."""
    if not _HERITAGE_GROUPS_DIR.exists():
        return
    
    for json_file in sorted(_HERITAGE_GROUPS_DIR.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load heritage groups {json_file}: {e}")
            continue
        
        nationality = data.get("nationality")
        if not nationality:
            print(f"Warning: No nationality in {json_file}, skipping")
            continue
        
        groups = data.get("heritage_groups", {})
        if groups:
            HERITAGE_CONFIG[nationality] = groups
            
            # Build picture folder map from heritage group configs
            for group_name, group_config in groups.items():
                if "picture_folder" in group_config:
                    HERITAGE_PICTURE_FOLDER_MAP[group_name] = group_config["picture_folder"]


# ── Initialize on import ──────────────────────────────────────────────────────
_load_name_pools()
_load_heritage_groups()

# Build HERITAGE_NAME_POOLS for backward compatibility
# Any country referenced in heritage groups but not a "main" nationality gets added here
for _nat_code, _groups in HERITAGE_CONFIG.items():
    for _group_name, _group_config in _groups.items():
        for _origin_code in _group_config.get("origin_country_weights", {}).keys():
            if _origin_code in COUNTRY_NAME_POOLS and _origin_code != _nat_code:
                HERITAGE_NAME_POOLS[_origin_code] = COUNTRY_NAME_POOLS[_origin_code]
