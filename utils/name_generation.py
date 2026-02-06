"""
Name generation engine for realistic player names.

Implements tier-based sampling, heritage naming, middle names, compound surnames,
and anti-duplication logic.
"""

import random
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from .name_data import (
    COUNTRY_NAME_POOLS,
    HERITAGE_CONFIG,
    MIDDLE_NAME_PROBS,
    COMPOUND_SURNAME_PROBS,
    SURNAME_CONNECTORS,
    COMPOUND_SURNAME_TIER_BIAS,
    DEFAULT_GIVEN_NAME_TIER_PROBS,
    DEFAULT_SURNAME_TIER_PROBS,
    COUNTRY_TIER_PROBS,
    HERITAGE_NAME_POOLS
)


@dataclass
class PlayerName:
    """Structured player name with separate components."""
    
    given_first: str
    given_middle: Optional[str] = None
    surname_parts: List[str] = None
    surname_connector: Optional[str] = None
    
    def __post_init__(self):
        if self.surname_parts is None:
            self.surname_parts = []
    
    @property
    def display_full(self) -> str:
        """Full display name: 'John Michael Smith-Jones'"""
        parts = [self.given_first]
        if self.given_middle:
            parts.append(self.given_middle)
        
        if self.surname_parts:
            if len(self.surname_parts) == 2 and self.surname_connector:
                surname = f"{self.surname_parts[0]}{self.surname_connector}{self.surname_parts[1]}"
            else:
                surname = self.surname_parts[0] if self.surname_parts else ""
            parts.append(surname)
        
        return " ".join(parts)
    
    @property
    def display_short(self) -> str:
        """Short display name: 'J. M. Smith-Jones' or 'J. Smith-Jones'"""
        first_initial = self.given_first[0] + "." if self.given_first else ""
        parts = [first_initial]
        
        if self.given_middle:
            parts.append(self.given_middle[0] + ".")
        
        if self.surname_parts:
            if len(self.surname_parts) == 2 and self.surname_connector:
                surname = f"{self.surname_parts[0]}{self.surname_connector}{self.surname_parts[1]}"
            else:
                surname = self.surname_parts[0]
            parts.append(surname)
        
        return " ".join(parts)
    
    def __str__(self) -> str:
        """String representation returns full display name."""
        return self.display_full


def sample_from_tier(
    tier_list: List[str],
    tier_probs: Dict[str, float]
) -> str:
    """
    Sample a name from a tiered list.
    
    Args:
        tier_list: List of names in the selected tier
        tier_probs: Dictionary mapping tier names to probabilities
    
    Returns:
        Random name from the tier
    """
    if not tier_list:
        return ""
    return random.choice(tier_list)


def roll_tier(tier_probs: Dict[str, float]) -> str:
    """
    Roll a tier based on probabilities.
    
    Args:
        tier_probs: Dictionary mapping tier names to probabilities
    
    Returns:
        Selected tier name
    """
    tiers = list(tier_probs.keys())
    weights = [tier_probs[t] for t in tiers]
    return random.choices(tiers, weights=weights, k=1)[0]


def sample_name_from_pool(
    name_pool: Dict[str, List[str]],
    tier_probs: Dict[str, float]
) -> str:
    """
    Sample a name from a tiered name pool.
    
    Args:
        name_pool: Dictionary with tier keys and name lists
        tier_probs: Tier probability distribution
    
    Returns:
        Random name sampled from the pool
    """
    tier = roll_tier(tier_probs)
    tier_list = name_pool.get(tier, [])
    return sample_from_tier(tier_list, tier_probs)


def get_country_name_pool(country_code: str, name_type: str) -> Optional[Dict[str, List[str]]]:
    """
    Get name pool for a country and name type.
    
    Args:
        country_code: Country code (e.g., "ENG", "NGA")
        name_type: "given_names_male" or "surnames"
    
    Returns:
        Name pool dictionary or None if not found
    """
    country_pools = COUNTRY_NAME_POOLS.get(country_code)
    if not country_pools:
        return None
    return country_pools.get(name_type)


def select_heritage_group(nationality: str) -> Optional[str]:
    """
    Select a heritage group for a player based on nationality.
    
    Args:
        nationality: Player's nationality code
    
    Returns:
        Heritage group name or None if no heritage groups defined
    """
    heritage_groups = HERITAGE_CONFIG.get(nationality)
    if not heritage_groups:
        return None
    
    # Filter out groups with zero or negative weights
    groups = []
    weights = []
    for group_name, group_config in heritage_groups.items():
        weight = group_config.get("weight", 0.0)
        if weight > 0:
            groups.append(group_name)
            weights.append(weight)
    
    if not groups:
        return None
    
    return random.choices(groups, weights=weights, k=1)[0]


def select_origin_country(nationality: str, heritage_group: str) -> Optional[str]:
    """
    Select origin country for heritage name generation.
    
    If the selected country doesn't exist in name pools, falls back to the
    highest weight country in the heritage group.
    
    Args:
        nationality: Player's nationality
        heritage_group: Selected heritage group
    
    Returns:
        Origin country code or None
    """
    heritage_config = HERITAGE_CONFIG.get(nationality, {}).get(heritage_group)
    if not heritage_config:
        return None
    
    origin_weights = heritage_config.get("origin_country_weights", {})
    if not origin_weights:
        return None
    
    countries = list(origin_weights.keys())
    weights = [origin_weights[c] for c in countries]
    selected_country = random.choices(countries, weights=weights, k=1)[0]
    
    # Check if selected country has name pools, if not, use highest weight country
    if get_country_name_pool(selected_country, "given_names_male") is None:
        # Find country with highest weight that has name pools
        sorted_countries = sorted(origin_weights.items(), key=lambda x: x[1], reverse=True)
        for country_code, _ in sorted_countries:
            if get_country_name_pool(country_code, "given_names_male") is not None:
                return country_code
        # If no country has pools, return the highest weight one anyway
        return sorted_countries[0][0] if sorted_countries else selected_country
    
    return selected_country


def select_name_structure(nationality: str, heritage_group: str) -> Tuple[str, str]:
    """
    Select name structure pair (given origin, surname origin).
    
    Returns:
        Tuple of (given_origin, surname_origin) where each is "LOCAL" or "HERITAGE"
    """
    heritage_config = HERITAGE_CONFIG.get(nationality, {}).get(heritage_group)
    if not heritage_config:
        return ("LOCAL", "LOCAL")
    
    structure_probs = heritage_config.get("name_structure_probs", {})
    if not structure_probs:
        return ("LOCAL", "LOCAL")
    
    # Map structure codes to (given, surname) origins
    structure_map = {
        "LL": ("LOCAL", "LOCAL"),
        "LH": ("LOCAL", "HERITAGE"),
        "HL": ("HERITAGE", "LOCAL"),
        "HH": ("HERITAGE", "HERITAGE")
    }
    
    structures = list(structure_probs.keys())
    weights = [structure_probs[s] for s in structures]
    selected = random.choices(structures, weights=weights, k=1)[0]
    
    return structure_map.get(selected, ("LOCAL", "LOCAL"))


def generate_name(
    nationality: str,
    heritage_group: Optional[str] = None,
    origin_country: Optional[str] = None,
    used_names: Optional[Set[str]] = None,
    max_retries: int = 50
) -> PlayerName:
    """
    Generate a player name based on nationality and heritage.
    
    Args:
        nationality: Player's nationality code
        heritage_group: Optional heritage group (if None, will be selected)
        origin_country: Optional origin country (if None and heritage, will be selected)
        used_names: Set of already-used full names to avoid duplicates
        max_retries: Maximum retries if duplicate detected
    
    Returns:
        PlayerName object with structured name components
    """
    if used_names is None:
        used_names = set()
    
    for attempt in range(max_retries):
        # Select heritage group if not provided
        if heritage_group is None:
            heritage_group = select_heritage_group(nationality)
        
        # Determine name structure
        if heritage_group and heritage_group != "ENG_Mainstream":
            if origin_country is None:
                origin_country = select_origin_country(nationality, heritage_group)
            
            # If origin_country doesn't have name pools, fall back to highest weight country
            if origin_country and get_country_name_pool(origin_country, "given_names_male") is None:
                heritage_config = HERITAGE_CONFIG.get(nationality, {}).get(heritage_group)
                if heritage_config:
                    origin_weights = heritage_config.get("origin_country_weights", {})
                    if origin_weights:
                        # Find country with highest weight that has name pools
                        sorted_countries = sorted(origin_weights.items(), key=lambda x: x[1], reverse=True)
                        for country_code, _ in sorted_countries:
                            if get_country_name_pool(country_code, "given_names_male") is not None:
                                origin_country = country_code
                                break
                        # If still no valid country found, use highest weight anyway
                        if get_country_name_pool(origin_country, "given_names_male") is None and sorted_countries:
                            origin_country = sorted_countries[0][0]
            
            given_origin, surname_origin = select_name_structure(nationality, heritage_group)
        else:
            given_origin = "LOCAL"
            surname_origin = "LOCAL"
            origin_country = None
        
        # Select country pools for given name and surname
        given_country = origin_country if given_origin == "HERITAGE" else nationality
        surname_country = origin_country if surname_origin == "HERITAGE" else nationality
        
        # Get name pools
        given_pool = get_country_name_pool(given_country, "given_names_male")
        surname_pool = get_country_name_pool(surname_country, "surnames")
        
        if not given_pool or not surname_pool:
            # Fallback to nationality pool
            given_pool = get_country_name_pool(nationality, "given_names_male")
            surname_pool = get_country_name_pool(nationality, "surnames")
            if not given_pool or not surname_pool:
                # Fallback to ENG (England) if nationality not found in pools
                # This handles cases where player has nationality like SCO, WAL, ESP, etc.
                # but we only have name pools for ENG
                given_pool = get_country_name_pool("ENG", "given_names_male")
                surname_pool = get_country_name_pool("ENG", "surnames")
                if not given_pool or not surname_pool:
                    # Ultimate fallback
                    return PlayerName(
                        given_first="John",
                        surname_parts=["Smith"]
                    )
        
        # Get country-specific tier probabilities if available
        country_tier_probs = COUNTRY_TIER_PROBS.get(given_country, {})
        given_tier_probs = country_tier_probs.get("given", DEFAULT_GIVEN_NAME_TIER_PROBS)
        surname_tier_probs = country_tier_probs.get("surname", DEFAULT_SURNAME_TIER_PROBS)
        
        # Sample given name
        given_first = sample_name_from_pool(given_pool, given_tier_probs)
        
        # Sample surname
        surname_first = sample_name_from_pool(surname_pool, surname_tier_probs)
        surname_parts = [surname_first]
        surname_connector = None
        
        # Check for compound surname
        compound_prob = COMPOUND_SURNAME_PROBS.get(nationality, COMPOUND_SURNAME_PROBS.get("default", 0.05))
        if random.random() < compound_prob:
            # Sample second surname with tier bias
            # For compound, bias toward common/mid tiers
            compound_tier_probs = {
                "very_common": 0.10,
                "common": 0.50,
                "mid": 0.35,
                "rare": 0.05
            }
            surname_second = sample_name_from_pool(surname_pool, compound_tier_probs)
            surname_parts.append(surname_second)
            surname_connector = SURNAME_CONNECTORS.get(nationality, SURNAME_CONNECTORS.get("default", "-"))
        
        # Check for middle name
        middle_name = None
        middle_prob = MIDDLE_NAME_PROBS.get(nationality, MIDDLE_NAME_PROBS.get("default", 0.15))
        if random.random() < middle_prob:
            # Middle names usually from LOCAL pool
            middle_pool = get_country_name_pool(nationality, "given_names_male")
            if middle_pool:
                # Use country-specific tier probabilities for middle name
                country_tier_probs = COUNTRY_TIER_PROBS.get(nationality, {})
                middle_tier_probs = country_tier_probs.get("given", DEFAULT_GIVEN_NAME_TIER_PROBS)
                middle_name = sample_name_from_pool(middle_pool, middle_tier_probs)
        
        # Create name object
        name = PlayerName(
            given_first=given_first,
            given_middle=middle_name,
            surname_parts=surname_parts,
            surname_connector=surname_connector
        )
        
        # Check for duplicates
        full_name = name.display_full
        if full_name not in used_names:
            used_names.add(full_name)
            return name
    
    # If max retries exceeded, return the last generated name anyway
    return name


def generate_name_string(nationality: str, **kwargs) -> str:
    """
    Convenience function to generate a name and return as string.
    
    Args:
        nationality: Player's nationality code
        **kwargs: Additional arguments passed to generate_name()
    
    Returns:
        Full display name as string
    """
    name = generate_name(nationality, **kwargs)
    return name.display_full
