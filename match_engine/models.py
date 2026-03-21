"""
Match engine models: Player and Team classes for match simulation.
These are separate from database models - they represent match-specific team setups.
"""

from .constants import OUTFIELD_ATTRS, GOALKEEPER_ATTRS


class Player:
    """Represents a player in a match simulation."""
    
    def __init__(self, name, matrix_position, attributes, is_goalkeeper=False):
        """
        Args:
            name: Player name
            matrix_position: Position code (e.g., "GK", "DL", "MC", "FC")
            attributes: Dict of attribute_name -> value
            is_goalkeeper: Whether this player is a goalkeeper
        """
        self.name = name
        self.matrix_position = matrix_position
        self.attributes = attributes
        self.is_goalkeeper = is_goalkeeper
        self.minutes_played = 0  # Track minutes played (for stamina calculations and substitutions)

    def get_attr(self, attr_name):
        """Get attribute value, defaulting to 0 if not present."""
        return self.attributes.get(attr_name, 0)
    
    def validate_attributes(self):
        """Validate that player has appropriate attributes for their role."""
        if self.is_goalkeeper:
            required = GOALKEEPER_ATTRS
        else:
            required = OUTFIELD_ATTRS
        
        # Check if all required attributes are present
        missing = [attr for attr in required if attr not in self.attributes]
        if missing:
            raise ValueError(f"Player {self.name} missing attributes: {missing}")
        
        return True


class Team:
    """Represents a team in a match simulation."""
    
    def __init__(self, name, players):
        """
        Args:
            name: Team name
            players: List of Player objects
        """
        self.name = name
        self.players = players
        self._validate_team()
    
    def _validate_team(self):
        """Validate team has exactly 11 players including 1 goalkeeper."""
        if len(self.players) != 11:
            raise ValueError(f"Team {self.name} must have exactly 11 players, got {len(self.players)}")
        
        goalkeepers = [p for p in self.players if p.is_goalkeeper]
        if len(goalkeepers) != 1:
            raise ValueError(f"Team {self.name} must have exactly 1 goalkeeper, got {len(goalkeepers)}")
        
        # Validate all players have correct attributes
        for player in self.players:
            player.validate_attributes()
    
    def get_goalkeeper(self):
        """Get the team's goalkeeper."""
        return [p for p in self.players if p.is_goalkeeper][0]
    
    def get_players_by_position(self, position):
        """Get all players at a specific position."""
        return [p for p in self.players if p.matrix_position == position]
