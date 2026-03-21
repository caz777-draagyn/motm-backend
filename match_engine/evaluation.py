"""
Evaluation functions for match events using sigmoid functions and attribute comparisons.
"""

import random
import math
from typing import Tuple, List, Dict
from .models import Player


# ============ EVALUATION FORMULAS ============
# Based on football logic with weighted attribute combinations

EVENT_X_FORMULAS = {
    # Chance Creation Types
    #------------------------------------------------------------------------------------
    "Short": lambda initiator, defender: (
        0.4 * initiator.get_attr("Passing") +
        0.3 * initiator.get_attr("Vision") +
        0.1 * initiator.get_attr("Ball Control") +
        0.1 * initiator.get_attr("Composure") +
        0.1 * initiator.get_attr("Positioning")
    ) - (
        0.4 * defender.get_attr("Marking") +
        0.3 * defender.get_attr("Tackling") +
        0.1 * defender.get_attr("Work Rate") +
        0.1 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Strength")
    ),
    
    "Long": lambda initiator, defender: (
        0.4 * initiator.get_attr("Crossing") +
        0.3 * initiator.get_attr("Passing") +
        0.1 * initiator.get_attr("Ball Control") +
        0.1 * initiator.get_attr("Composure") +
        0.1 * initiator.get_attr("Vision")
    ) - (
        0.4 * defender.get_attr("Work Rate") +
        0.3 * defender.get_attr("Tackling") +
        0.1 * defender.get_attr("Marking") +
        0.1 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Strength")
    ),
    
    "Crossing": lambda initiator, defender: (
        0.4 * initiator.get_attr("Crossing") +
        0.3 * initiator.get_attr("Acceleration") +
        0.1 * initiator.get_attr("Agility") +
        0.1 * initiator.get_attr("Vision") +
        0.1 * initiator.get_attr("Ball Control")
    ) - (
        0.4 * defender.get_attr("Marking") +
        0.3 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Tackling") +
        0.1 * defender.get_attr("Acceleration") +
        0.1 * defender.get_attr("Agility")
    ),
    
    "Through": lambda initiator, defender: (
        0.4 * initiator.get_attr("Vision") +
        0.3 * initiator.get_attr("Passing") +
        0.1 * initiator.get_attr("Ball Control") +
        0.1 * initiator.get_attr("Crossing") +
        0.1 * initiator.get_attr("Composure")
    ) - (
        0.4 * defender.get_attr("Tackling") +
        0.3 * defender.get_attr("Acceleration") +
        0.1 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Marking") +
        0.1 * defender.get_attr("Strength")
    ),
    
    "Solo": lambda initiator, defender: (
        0.4 * initiator.get_attr("Ball Control") +
        0.3 * initiator.get_attr("Agility") +
        0.1 * initiator.get_attr("Vision") +
        0.1 * initiator.get_attr("Composure") +
        0.1 * initiator.get_attr("Acceleration")
    ) - (
        0.4 * defender.get_attr("Tackling") +
        0.3 * defender.get_attr("Agility") +
        0.1 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Marking") +
        0.1 * defender.get_attr("Strength")
    ),
    
    # Finisher Types (for chance creation success)
    #------------------------------------------------------------------------------------
     "Short_finisher": lambda initiator, defender: (
        0.4 * initiator.get_attr("Ball Control") +
        0.3 * initiator.get_attr("Positioning") +
        0.1 * initiator.get_attr("Work Rate") +
        0.1 * initiator.get_attr("Agility") +
        0.1 * initiator.get_attr("Strength")
    ) - (
        0.4 * defender.get_attr("Tackling") +
        0.3 * defender.get_attr("Marking") +
        0.1 * defender.get_attr("Work Rate") +
        0.1 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Agility")
    ),
    
    "Long_finisher": lambda initiator, defender: (
        0.4 * initiator.get_attr("Jump Reach") +
        0.3 * initiator.get_attr("Strength") +
        0.1 * initiator.get_attr("Agility") +
        0.1 * initiator.get_attr("Positioning") +
        0.1 * initiator.get_attr("Acceleration")
    ) - (
        0.4 * defender.get_attr("Heading") +
        0.3 * defender.get_attr("Jump Reach") +
        0.1 * defender.get_attr("Strength") +
        0.1 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Agility")
    ),
    
    "Crossing_finisher": lambda initiator, defender: (
        0.4 * initiator.get_attr("Jump Reach") +
        0.3 * initiator.get_attr("Strength") +
        0.1 * initiator.get_attr("Agility") +
        0.1 * initiator.get_attr("Positioning") +
        0.1 * initiator.get_attr("Work Rate")
    ) - (
        0.4 * defender.get_attr("Heading") +
        0.3 * defender.get_attr("Jump Reach") +
        0.1 * defender.get_attr("Strength") +
        0.1 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Agility")
    ),
    
    "Through_finisher": lambda initiator, defender: (
        0.4 * initiator.get_attr("Vision") +
        0.3 * initiator.get_attr("Acceleration") +
        0.1 * initiator.get_attr("Agility") +
        0.1 * initiator.get_attr("Positioning") +
        0.1 * initiator.get_attr("Composure")
    ) - (
        0.4 * defender.get_attr("Positioning") +
        0.3 * defender.get_attr("Acceleration") +
        0.1 * defender.get_attr("Strength") +
        0.1 * defender.get_attr("Tackling") +
        0.1 * defender.get_attr("Marking")
    ),
    
    "Solo_finisher": lambda initiator, defender: (
        0.4 * initiator.get_attr("Ball Control") +
        0.3 * initiator.get_attr("Agility") +
        0.1 * initiator.get_attr("Vision") +
        0.1 * initiator.get_attr("Composure") +
        0.1 * initiator.get_attr("Acceleration")
    ) - (
        0.4 * defender.get_attr("Tackling") +
        0.3 * defender.get_attr("Agility") +
        0.1 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Marking") +
        0.1 * defender.get_attr("Strength")
    ),
    
    # Shot/Finish Types
    #------------------------------------------------------------------------------------
     "FirstTime": lambda initiator, defender: (
        0.4 * initiator.get_attr("Ball Control") +
        0.4 * initiator.get_attr("Finishing") +
        0.2 * initiator.get_attr("Composure") 
    ) - (
        10
    ),
    
    "Controlled": lambda initiator, defender: (
        0.5 * initiator.get_attr("Finishing") +
        0.3 * initiator.get_attr("Composure") +
        0.2 * initiator.get_attr("Ball Control")
    ) - (
        10
    ),
    
    "Header": lambda initiator, defender: (
        0.5 * initiator.get_attr("Heading") +
        0.3 * initiator.get_attr("Jump Reach") +
        0.2 * initiator.get_attr("Strength")
    ) - (
       10
    ),
            
    "Chip": lambda initiator, defender: (
        0.4 * initiator.get_attr("Composure") +
        0.3 * initiator.get_attr("Ball Control") +
        0.3 * initiator.get_attr("Finishing") 
    ) - (
        10
    ),
    
    "Finesse": lambda initiator, defender: (
        0.3 * initiator.get_attr("Vision") +
        0.3 * initiator.get_attr("Finishing") +
        0.1 * initiator.get_attr("Composure") +
        0.3 * initiator.get_attr("Agility")
    ) - (
        10
    ),
    
    "Power": lambda initiator, defender: (
        0.4 * initiator.get_attr("Finishing") +
        0.4 * initiator.get_attr("Strength") +
        0.2 * initiator.get_attr("Ball Control")
    ) - (
        10
    ),
    
    # Goalkeeper Saves (from goalkeeper's perspective: goalkeeper as initiator, finisher as defender)
    "FirstTime_save": lambda initiator, defender: (
        0.6 * initiator.get_attr("Reflexes") +
        0.3 * initiator.get_attr("Positioning") +
        0.1 * initiator.get_attr("Handling")
    ) - (
        10
    ),
    
    "Controlled_save": lambda initiator, defender: (
        0.5 * initiator.get_attr("Handling") +
        0.3 * initiator.get_attr("Positioning") +
        0.2 * initiator.get_attr("Reflexes")
    ) - (
        10
    ),
    
    "Header_save": lambda initiator, defender: (
        0.6 * initiator.get_attr("Aerial Reach") +
        0.3 * initiator.get_attr("Positioning") +
        0.3 * initiator.get_attr("Agility") +
        0.1 * initiator.get_attr("Handling")
    ) - (
        10
    ),
    
    "Chip_save": lambda initiator, defender: (
        0.5 * initiator.get_attr("One-on-One") +
        0.3 * initiator.get_attr("Positioning") +
        0.2 * initiator.get_attr("Reflexes")
    ) - (
        10
    ),
    
    "Finesse_save": lambda initiator, defender: (
        0.5 * initiator.get_attr("Handling") +
        0.3 * initiator.get_attr("Agility") +
        0.3 * initiator.get_attr("Positioning") +
        0.2 * initiator.get_attr("Handling")
    ) - (
        10
    ),
    
    "Power_save": lambda initiator, defender: (
        0.3 * initiator.get_attr("Handling") +
        0.3 * initiator.get_attr("Reflexes") +
        0.3 * initiator.get_attr("Strength") +
        0.1 * initiator.get_attr("Positioning")
    ) - (
        10
    ),

    # Set Pieces shots    
    #----------------------------------------------------------------------------   
    
    "Penalty": lambda initiator, defender: (
        0.5 * initiator.get_attr("Composure") +
        0.3 * initiator.get_attr("Finishing") +
        0.2 * initiator.get_attr("Ball Control")
    ) - (
        10
    ),
    "Freekick": lambda initiator, defender: (
        0.3 * initiator.get_attr("Finishing") +
        0.2 * initiator.get_attr("Vision") +
        0.2 * initiator.get_attr("Composure") +
        0.3 * initiator.get_attr("Ball Control")
    ) - (
        10
    ),
    
    # Set Piece Saves
    #----------------------------------------------------------------------------
    "Penalty_save": lambda initiator, defender: (
        0.4 * initiator.get_attr("One-on-One") +
        0.3 * initiator.get_attr("Composure") +
        0.3 * initiator.get_attr("Agility")
    ) - (
        10
    ),
    
    "Freekick_save": lambda initiator, defender: (
        0.4 * initiator.get_attr("Agility") +
        0.3 * initiator.get_attr("Handling") +
        0.2 * initiator.get_attr("Positioning")
    ) - (
        10
    ),
    
    # Goalkeeper Intercepts (GK is initiator)
    "Long_intercept": lambda initiator, defender: (
        0.3 * initiator.get_attr("Aerial Reach") +
        0.3 * initiator.get_attr("Command of Area") +
        0.2 * initiator.get_attr("Strength") +
        0.2 * initiator.get_attr("Positioning")
    ) - (
       10
    ),
    
    "Crossing_intercept": lambda initiator, defender: (
        0.4 * initiator.get_attr("Aerial Reach") +
        0.4 * initiator.get_attr("Command of Area") +
        0.2 * initiator.get_attr("Strength") +
        0.2 * initiator.get_attr("Positioning")
    ) - (
        10
    ),
    
    "Through_intercept": lambda initiator, defender: (
        0.6 * initiator.get_attr("One-on-One") +
        0.3 * initiator.get_attr("Positioning") +
        0.1 * initiator.get_attr("Agility")
    ) - (
        10
    ),
    
    # Set Pieces
    "Corner": lambda initiator, defender: (
        0.5 * initiator.get_attr("Crossing") +
        0.3 * initiator.get_attr("Vision") +
        0.2 * initiator.get_attr("Ball Control")
    ) - (
        0.5 * defender.get_attr("Aerial Reach") +
        0.3 * defender.get_attr("Command of Area") +
        0.2 * defender.get_attr("Positioning")
    ),

    # Counter (using similar logic to Through ball)
    "Counter": lambda initiator, defender: (
        0.4 * initiator.get_attr("Vision") +
        0.3 * initiator.get_attr("Passing") +
        0.2 * initiator.get_attr("Composure") +
        0.1 * initiator.get_attr("Acceleration")
    ) - (
        0.5 * defender.get_attr("Positioning") +
        0.3 * defender.get_attr("Marking") +
        0.2 * defender.get_attr("Tackling")
    ),

    # Header Duel (outfield player vs outfield player, e.g., during corners)
    "Header_duel": lambda initiator, defender: (
        0.4 * initiator.get_attr("Heading") +
        0.3 * initiator.get_attr("Jump Reach") +
        0.2 * initiator.get_attr("Positioning") +
        0.1 * initiator.get_attr("Strength")
    ) - (
        0.4 * defender.get_attr("Heading") +
        0.3 * defender.get_attr("Jump Reach") +
        0.2 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Strength")
    ),
    
    # Corner Finisher (outfield player vs outfield player during corner kicks)
    "Corner_finisher": lambda initiator, defender: (
        0.4 * initiator.get_attr("Heading") +
        0.3 * initiator.get_attr("Jump Reach") +
        0.2 * initiator.get_attr("Positioning") +
        0.1 * initiator.get_attr("Strength")
    ) - (
        0.4 * defender.get_attr("Heading") +
        0.3 * defender.get_attr("Jump Reach") +
        0.2 * defender.get_attr("Positioning") +
        0.1 * defender.get_attr("Strength")
    ),
    
    "Gk_Corner": lambda initiator, defender: (
        0.5 * initiator.get_attr("Crossing") +
        0.3 * initiator.get_attr("Vision") +
        0.2 * initiator.get_attr("Composure")
    ) - (
        0.5 * defender.get_attr("Aerial Reach") +
        0.3 * defender.get_attr("Command of Area") +
        0.2 * defender.get_attr("Positioning")
    ),
    
    # Corner triggers - defender/GK as initiator trying to deflect for corner
    "Corner_from_save": lambda initiator, defender: (
        # GK's ability to avoid deflecting ball out for corner
        0.5 * initiator.get_attr("Handling") +
        0.2 * initiator.get_attr("Positioning") +
        0.3 * initiator.get_attr("Composure")
    ) - (
        10
    ),
    
    "Corner_from_finisher_fail": lambda initiator, defender: (
        # Defender's ability to avoid deflecting ball out for corner
        0.4 * initiator.get_attr("Ball Control") +
        0.3 * initiator.get_attr("Positioning") +
        0.3 * initiator.get_attr("Agility")
    ) - (
       10
    ),
    
    "Corner_from_creation_fail": lambda initiator, defender: (
        # Defender's ability to avoid deflecting ball out for corner
        0.4 * initiator.get_attr("Ball Control") +
        0.3 * initiator.get_attr("Positioning") +
        0.3 * initiator.get_attr("Agility")
    ) - (
       10
    ),
}

# Skill weight mapping for each event type: {event_type: {skill: weight}}
# This maps exactly to the formulas above
EVENT_SKILL_WEIGHTS: Dict[str, Dict[str, float]] = {
    "Short": {
        "Passing": 0.4, "Vision": 0.3, "Ball Control": 0.1, "Composure": 0.1, "Positioning": 0.1,  # initiator
        "Marking": 0.4, "Tackling": 0.3, "Work Rate": 0.1, "Positioning": 0.1, "Strength": 0.1  # defender
    },
    "Long": {
        "Crossing": 0.4, "Passing": 0.3, "Ball Control": 0.1, "Composure": 0.1, "Vision": 0.1,  # initiator
        "Work Rate": 0.4, "Tackling": 0.3, "Marking": 0.1, "Positioning": 0.1, "Strength": 0.1  # defender
    },
    "Crossing": {
        "Crossing": 0.4, "Acceleration": 0.3, "Agility": 0.1, "Vision": 0.1, "Ball Control": 0.1,  # initiator
        "Marking": 0.4, "Positioning": 0.3, "Tackling": 0.1, "Acceleration": 0.1, "Agility": 0.1  # defender
    },
    "Through": {
        "Vision": 0.4, "Passing": 0.3, "Ball Control": 0.1, "Crossing": 0.1, "Composure": 0.1,  # initiator
        "Tackling": 0.4, "Acceleration": 0.3, "Positioning": 0.1, "Marking": 0.1, "Strength": 0.1  # defender
    },
    "Solo": {
        "Ball Control": 0.4, "Agility": 0.3, "Vision": 0.1, "Composure": 0.1, "Acceleration": 0.1,  # initiator
        "Tackling": 0.4, "Agility": 0.3, "Positioning": 0.1, "Marking": 0.1, "Strength": 0.1  # defender
    },
    "Short_finisher": {
        "Ball Control": 0.4, "Positioning": 0.3, "Work Rate": 0.1, "Agility": 0.1, "Strength": 0.1,  # initiator
        "Tackling": 0.4, "Marking": 0.3, "Work Rate": 0.1, "Positioning": 0.1, "Agility": 0.1  # defender
    },
    "Long_finisher": {
        "Jump Reach": 0.4, "Strength": 0.3, "Agility": 0.1, "Positioning": 0.1, "Acceleration": 0.1,  # initiator
        "Heading": 0.4, "Jump Reach": 0.3, "Strength": 0.1, "Positioning": 0.1, "Agility": 0.1  # defender
    },
    "Crossing_finisher": {
        "Jump Reach": 0.4, "Strength": 0.3, "Agility": 0.1, "Positioning": 0.1, "Work Rate": 0.1,  # initiator
        "Heading": 0.4, "Jump Reach": 0.3, "Strength": 0.1, "Positioning": 0.1, "Agility": 0.1  # defender
    },
    "Through_finisher": {
        "Vision": 0.4, "Acceleration": 0.3, "Agility": 0.1, "Positioning": 0.1, "Composure": 0.1,  # initiator
        "Positioning": 0.4, "Acceleration": 0.3, "Strength": 0.1, "Tackling": 0.1, "Marking": 0.1  # defender
    },
    "Solo_finisher": {
        "Ball Control": 0.4, "Agility": 0.3, "Vision": 0.1, "Composure": 0.1, "Acceleration": 0.1,  # initiator
        "Tackling": 0.4, "Agility": 0.3, "Positioning": 0.1, "Marking": 0.1, "Strength": 0.1  # defender
    },
    "FirstTime": {
        "Ball Control": 0.4, "Finishing": 0.4, "Composure": 0.2  # initiator only (defender is -10 constant)
    },
    "Controlled": {
        "Finishing": 0.5, "Composure": 0.3, "Ball Control": 0.2  # initiator only
    },
    "Header": {
        "Heading": 0.5, "Jump Reach": 0.3, "Strength": 0.2  # initiator only
    },
    "Chip": {
        "Composure": 0.4, "Ball Control": 0.3, "Finishing": 0.3  # initiator only
    },
    "Finesse": {
        "Vision": 0.3, "Finishing": 0.3, "Composure": 0.1, "Agility": 0.3  # initiator only
    },
    "Power": {
        "Finishing": 0.4, "Strength": 0.4, "Ball Control": 0.2  # initiator only
    },
    "Header_duel": {
        "Heading": 0.4, "Jump Reach": 0.3, "Positioning": 0.2, "Strength": 0.1,  # initiator
        "Heading": 0.4, "Jump Reach": 0.3, "Positioning": 0.2, "Strength": 0.1  # defender (same)
    },
    "Corner_finisher": {
        "Heading": 0.4, "Jump Reach": 0.3, "Positioning": 0.2, "Strength": 0.1,  # initiator
        "Heading": 0.4, "Jump Reach": 0.3, "Positioning": 0.2, "Strength": 0.1  # defender (same)
    },
    "Corner_from_save": {
        "Handling": 0.5, "Reflexes": 0.3, "Positioning": 0.2,  # initiator (GK)
        "Finishing": 0.5, "Ball Control": 0.3, "Composure": 0.2  # defender (finisher)
    },
    "Corner_from_finisher_fail": {
        "Tackling": 0.4, "Positioning": 0.3, "Strength": 0.2, "Agility": 0.1,  # initiator (defender)
        "Ball Control": 0.4, "Agility": 0.3, "Composure": 0.2, "Positioning": 0.1  # defender (finisher)
    },
    "Corner_from_creation_fail": {
        "Tackling": 0.4, "Marking": 0.3, "Positioning": 0.2, "Strength": 0.1,  # initiator (defender)
        "Ball Control": 0.4, "Passing": 0.3, "Composure": 0.2, "Vision": 0.1  # defender (creator)
    },
    "FirstTime_save": {
        "Reflexes": 0.6, "Positioning": 0.3, "Handling": 0.1  # initiator (GK) only
    },
    "Controlled_save": {
        "Handling": 0.5, "Positioning": 0.3, "Reflexes": 0.2  # initiator (GK) only
    },
    "Header_save": {
        "Aerial Reach": 0.6, "Positioning": 0.3, "Agility": 0.3, "Handling": 0.1  # initiator (GK) only (note: weights sum to 1.3, error in formula)
    },
    "Chip_save": {
        "One-on-One": 0.5, "Positioning": 0.3, "Reflexes": 0.2  # initiator (GK) only
    },
    "Finesse_save": {
        "Handling": 0.5, "Agility": 0.3, "Positioning": 0.3  # initiator (GK) only (note: weights sum to 1.1, error in formula)
    },
    "Power_save": {
        "Handling": 0.3, "Reflexes": 0.3, "Strength": 0.3, "Positioning": 0.1  # initiator (GK) only
    },
    "Penalty_save": {
        "One-on-One": 0.5, "Reflexes": 0.3, "Positioning": 0.2  # initiator (GK) only
    },
    "Freekick_save": {
        "Positioning": 0.4, "Reflexes": 0.3, "Command of Area": 0.2, "Handling": 0.1  # initiator (GK) only
    },
    "Long_intercept": {
        "Aerial Reach": 0.3, "Command of Area": 0.3, "Strength": 0.2, "Positioning": 0.2  # initiator (GK) only
    },
    "Crossing_intercept": {
        "Aerial Reach": 0.4, "Command of Area": 0.4, "Strength": 0.2, "Positioning": 0.2  # initiator (GK) only (note: weights sum to 1.2, error in formula)
    },
    "Through_intercept": {
        "One-on-One": 0.6, "Positioning": 0.3, "Agility": 0.1  # initiator (GK) only
    },
    "Corner": {
        "Crossing": 0.5, "Vision": 0.3, "Ball Control": 0.2,  # initiator
        "Aerial Reach": 0.5, "Command of Area": 0.3, "Positioning": 0.2  # defender
    },
    "Freekick": {
        "Finishing": 0.3, "Vision": 0.2, "Composure": 0.2, "Ball Control": 0.3,  # initiator
        "Positioning": 0.3, "Reflexes": 0.3, "Agility": 0.3, "Handling": 0.1  # defender
    },
    "Penalty": {
        "Composure": 0.5, "Finishing": 0.3, "Ball Control": 0.2,  # initiator
        "Reflexes": 0.3, "Agility": 0.4, "One-on-One": 0.3  # defender
    },
    "Counter": {
        "Vision": 0.4, "Passing": 0.3, "Composure": 0.2, "Acceleration": 0.1,  # initiator
        "Positioning": 0.5, "Marking": 0.3, "Tackling": 0.2  # defender
    },
    "Gk_Pen": {
        "Finishing": 0.5, "Composure": 0.4, "Vision": 0.1,  # initiator
        "Reflexes": 0.5, "Positioning": 0.3, "One-on-One": 0.2  # defender
    },
    "Gk_Free": {
        "Finishing": 0.4, "Vision": 0.3, "Composure": 0.2, "Ball Control": 0.1,  # initiator
        "Positioning": 0.4, "Reflexes": 0.3, "Command of Area": 0.2, "Handling": 0.1  # defender
    },
    "Gk_Corner": {
        "Crossing": 0.5, "Vision": 0.3, "Composure": 0.2,  # initiator
        "Aerial Reach": 0.5, "Command of Area": 0.3, "Positioning": 0.2  # defender
    },
}

# Sigmoid parameters
DEFAULT_PARAMS = {"a": 0.7, "c": 0.20, "L": 0.60}
EVENT_SIGMOID_PARAMS = {
    "Short": DEFAULT_PARAMS,
    "Crossing": DEFAULT_PARAMS,
    "Solo": DEFAULT_PARAMS,
    "Through": DEFAULT_PARAMS,
    "Long": DEFAULT_PARAMS,
    "Short_finisher": DEFAULT_PARAMS,
    "Crossing_finisher": DEFAULT_PARAMS,
    "Solo_finisher": DEFAULT_PARAMS,
    "Through_finisher": DEFAULT_PARAMS,
    "Long_finisher": DEFAULT_PARAMS,
    "FirstTime": {"a": 0.3, "c": 0.15, "L": 0.25}, #shoot on target 15-40%
    "Controlled": {"a": 0.3, "c": 0.25, "L": 0.25}, #shoot on target 25-50%
    "Header": {"a": 0.3, "c": 0.2, "L": 0.25}, #shoot on target 20-45%
    "Chip": {"a": 0.3, "c": 0.1, "L": 0.25}, #shoot on target 10-35%
    "Finesse": {"a": 0.3, "c": 0.1, "L": 0.25}, #shoot on target 10-35%
    "Power": {"a": 0.3, "c": 0.2, "L": 0.25}, #shoot on target 10-35%
    "Header_duel": DEFAULT_PARAMS,
    "Corner_finisher": DEFAULT_PARAMS,
    "Corner_from_save": {"a": 0.15, "c": 0.6, "L": 0.3},
    "Corner_from_finisher_fail": {"a": 0.15, "c": 0.75, "L": 0.2},
    "Corner_from_creation_fail": {"a": 0.15, "c": 0.75, "L": 0.2},
    "FirstTime_save": {"a": 0.3, "c": 0.28, "L": 0.5}, #Save 50-75%
    "Controlled_save": {"a": 0.3, "c": 0.30, "L": 0.5}, #Save 55-78%
    "Header_save": {"a": 0.3, "c": 0.23, "L": 0.5}, #Save 45-70%
    "Chip_save": {"a": 0.3, "c": 0.18, "L": 0.5}, #Save 40-65%
    "Finesse_save": {"a": 0.3, "c": 0.18, "L": 0.5}, #Save 40-65%
    "Power_save": {"a": 0.3, "c": 0.40, "L": 0.45}, #Save 65-85%
    "Penalty_save": {"a": 0.3, "c": 0.0, "L": 0.30}, #Save 15-30% (penalties are hard to save)
    "Freekick_save": {"a": 0.3, "c": 0.25, "L": 0.45}, #Save 45-70%
    "Long_intercept": DEFAULT_PARAMS,
    "Crossing_intercept": DEFAULT_PARAMS,
    "Through_intercept": DEFAULT_PARAMS,
    "Corner": DEFAULT_PARAMS,
    "Penalty": {"a": 0.4, "c": 0.70, "L": 0.25}, #On target 70-90% (penalties rarely miss)
    "Freekick": {"a": 0.3, "c": 0.28, "L": 0.50}, #On target 25-40% (similar to Controlled shots)
}


# ============ EVALUATION FUNCTIONS ============

def sigmoid_eval(X: float, a: float, c: float, L: float) -> float:
    """Sigmoid function: c + L / (1 + exp(-a * X))"""
    return c + L / (1 + math.exp(-a * X))


def calculate_stamina_modifier(initiator: Player, defender: Player) -> float:
    """
    Calculate stamina modifier based on stamina difference between initiator and defender.
    
    Formula: 0.001 * (Stamina_initiator * minutes_played_initiator - Stamina_defender * minutes_played_defender)
    
    Args:
        initiator: Player initiating the event
        defender: Player defending against the event
    
    Returns:
        Stamina modifier value to add to X calculation
    """
    stamina_init = initiator.get_attr("Stamina")
    stamina_def = defender.get_attr("Stamina")
    minutes_init = initiator.minutes_played
    minutes_def = defender.minutes_played
    
    modifier = 0.001 * (stamina_init * minutes_init - stamina_def * minutes_def)
    return modifier


def eval_event(
    event_type: str,
    initiator: Player,
    defender: Player,
    x_bonus: float = 0.0,
    crit_multiplier_1: float = 0.3,
    crit_multiplier_2: float = 0.7,
    stamina_modifier: float = None
) -> Tuple[bool, float, float, str, List[str]]:
    """
    Evaluate an event between initiator and defender with two-level critical success system.
    
    Args:
        event_type: Type of event (e.g., "Short", "FirstTime", "Header_save", "Short_finisher")
        initiator: Player initiating the event (e.g., creator, finisher, goalkeeper)
        defender: Player defending against the event
        x_bonus: Bonus value to add to X calculation (default: 0.0)
        crit_multiplier_1: Multiplier for first critical chance threshold (default: 0.3)
        crit_multiplier_2: Multiplier for second critical chance threshold (default: 0.7)
        stamina_modifier: Stamina modifier to add to X calculation. If None, calculated automatically.
    
    Returns:
        Tuple of:
        - success: Whether the event succeeded (roll > prob)
        - prob: Probability of success
        - X: Raw X value from formula (after bonus and stamina modifier)
        - crit_level: Critical level achieved - "crit_2" (roll > crit_chance_2), 
                      "crit_1" (crit_chance_1 < roll <= crit_chance_2), or "none"
        - skills_used: List of attribute names used in evaluation
    """
    x_formula = EVENT_X_FORMULAS.get(event_type)
    if x_formula is None:
        raise ValueError(f"Unknown event type: {event_type}")
    
    params = EVENT_SIGMOID_PARAMS.get(event_type, DEFAULT_PARAMS)
    
    # Calculate stamina modifier if not provided
    if stamina_modifier is None:
        stamina_modifier = calculate_stamina_modifier(initiator, defender)
    
    # Calculate X value and apply bonus and stamina modifier
    X = x_formula(initiator, defender) + x_bonus + stamina_modifier
    
    # Convert to probability using sigmoid
    prob = 1 - sigmoid_eval(X, params["a"], params["c"], params["L"])
    
    # Random roll
    roll = random.random()
    
    # Calculate critical chance thresholds
    crit_chance_1 = prob + crit_multiplier_1 * (1 - prob)
    crit_chance_2 = prob + crit_multiplier_2 * (1 - prob)
    
    # Determine success and critical level
    success = roll > prob
    
    if roll > crit_chance_2:
        crit_level = "crit_2"
    elif roll > crit_chance_1:
        crit_level = "crit_1"
    else:
        crit_level = "none"
    
    # Track which skills were used (for statistics)
    skills_used = _get_skills_used_for_event(event_type, initiator, defender)
    
    return success, prob, X, crit_level, skills_used


def _get_skills_used_for_event(event_type: str, initiator: Player, defender: Player) -> List[str]:
    """
    Determine which attributes were used in an evaluation based on event type.
    Returns a list of all attributes used by both initiator and defender.
    This is the unweighted version (each skill counts as +1).
    """
    weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
    if not weights:
        # Fallback for unknown event types
        return ["Composure", "Positioning"]
    
    # Return list of all skills used (keys from weights dict)
    return list(weights.keys())


def _get_skills_with_weights_for_event(event_type: str, initiator: Player, defender: Player) -> Dict[str, float]:
    """
    Determine which attributes were used in an evaluation based on event type, with their weights.
    Returns a dictionary mapping skill names to their weights.
    This is the weighted version (skills are weighted by their contribution to the formula).
    """
    weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
    if not weights:
        # Fallback for unknown event types
        return {"Composure": 1.0, "Positioning": 1.0}
    
    # Return the weights dictionary directly
    return weights.copy()
