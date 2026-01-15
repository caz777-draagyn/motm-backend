# Cup Competitions Structure

## Overview

In Classic game mode, there are two types of cup competitions:

1. **Domestic Cup**: Main cup competition for all teams in a country
2. **Lower League Cup**: Separate cup competitions for lower tiers

## Participation Rules

### Domestic Cup
- **All teams** in the country participate (all tiers)
- Single-leg matches (one match per round, no home/away legs)
- Tier 1 teams participate and typically progress deep

### Lower League Cup
- **Tiers 2-3**: Combined into one lower league cup
- **Tier 4+**: Each tier has its own separate lower league cup
- Tier 1 teams **do NOT** participate in lower league cups

### Summary
- **Tier 1 teams**: Participate in 1 cup (Domestic Cup only)
- **Tier 2+ teams**: Participate in 2 cups (Domestic Cup + Lower League Cup)

## Cup Structure

### Match Format
- Single-leg matches (one match per round)
- Winner advances to next round
- Loser is eliminated

### Round Structure
- Typically starts with many teams and reduces by half each round
- Example: 64 teams → 32 → 16 → 8 → 4 → 2 (final)
- Exact structure depends on number of participating teams

## Calendar Integration

Cup matches are scheduled on specific days in the calendar:
- Cup match days are marked as `DayType.CUP_MATCH` in the calendar
- Can be scheduled alongside or separate from league matches
- Exact scheduling details to be determined

## Database Models

### CupCompetition
- Defines the cup structure (domestic vs lower league)
- Links to country or federation
- Specifies which tiers participate (for lower league cups)

### CupSeason
- Links a cup competition to a specific season
- Tracks current round and status
- Stores cup configuration

### CupMatch
- Individual cup match
- Single-leg format
- Links to match day and cup season

## Implementation Notes

- Cup competitions are created per country/federation
- Each season, cup seasons are created for each cup competition
- Teams are automatically entered based on their tier and country
- Match scheduling will be determined when calendar details are finalized
