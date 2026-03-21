# Match Engine Implementation Plan

## Overview
Integrate the match engine from ME.ipynb into the codebase, refactor for clarity, and create a test bench UI for tuning.

## File Structure

```
match_engine/
├── __init__.py
├── models.py              # Player, Team classes (match-specific, not DB models)
├── matrices.py            # All matrix definitions and matrix building functions
├── evaluation.py          # Evaluation formulas, sigmoid functions, event evaluation
├── simulator.py           # MatchSimulator class and match execution
├── statistics.py          # Stats collection classes and aggregation
└── constants.py          # Constants (attributes, positions, etc.)

api/
├── match_engine.py        # API endpoints for match simulation
└── test_bench.py          # API endpoints for test bench UI

templates/                 # HTML templates for test bench UI
└── test_bench.html

static/                    # CSS/JS for test bench UI
└── test_bench.js
```

## Implementation Steps

### Phase 1: Code Organization & Refactoring
1. Extract constants (attributes, positions) → `constants.py`
2. Extract matrix definitions → `matrices.py`
3. Extract evaluation logic → `evaluation.py`
4. Extract simulator class → `simulator.py`
5. Extract statistics classes → `statistics.py`
6. Create match-specific models (Player, Team) → `models.py`

### Phase 2: Match Engine Core
1. Refactor to accept team input (list of players with positions/attributes)
2. Ensure clean separation from database models
3. Make simulator work as single function call: `simulate_match(home_team, away_team) -> MatchResult`

### Phase 3: Statistics Enhancement
1. Track individual skill usage in evaluations
2. Log which attributes were used in each evaluation
3. Aggregate skill usage statistics per player

### Phase 4: API Integration
1. Create POST endpoint: `/api/match-engine/simulate`
   - Input: Two teams (JSON with players, positions, attributes)
   - Output: Match result with statistics
2. Create GET endpoint: `/api/match-engine/test-bench` (serves UI)
3. Create POST endpoint: `/api/match-engine/test-bench/simulate`
   - Input: Team configs, number of matches
   - Output: Aggregated statistics

### Phase 5: Test Bench UI
1. Create HTML interface with:
   - Team 1 selection (11 players with positions/attributes)
   - Team 2 selection (11 players with positions/attributes)
   - Number of matches selector (1, 10, 100, 1000)
   - Run simulation button
   - Results display (team stats, player stats, skill usage)
2. Use vanilla JS or simple framework for interactivity
3. Display statistics in clear, readable format

## Key Design Decisions

### Team Input Format
```python
{
    "name": "Team Name",
    "players": [
        {
            "name": "Player Name",
            "position": "GK",  # or "DL", "DC", etc.
            "attributes": {
                "Finishing": 10,
                "Tackling": 8,
                # ... all attributes
            },
            "is_goalkeeper": False
        },
        # ... 10 more players
    ]
}
```

### Match Result Format
```python
{
    "home_score": 2,
    "away_score": 1,
    "match_length": 93,
    "team_stats": {...},
    "player_stats": {...},
    "skill_usage": {...}  # NEW: Track which skills were used
}
```

### Statistics Enhancement
- Track every attribute used in each evaluation
- Log: `{"player": "John", "skill": "Finishing", "event": "FirstTime", "used_in": "shot_quality", "count": 5}`
- Aggregate per player: total times each skill was evaluated

## File Dependencies

```
match_engine/
  models.py          → constants.py
  matrices.py        → models.py, constants.py
  evaluation.py     → models.py, constants.py
  simulator.py      → matrices.py, evaluation.py, models.py
  statistics.py     → models.py
  
api/
  match_engine.py   → match_engine/*, models/*
  test_bench.py     → match_engine/*, models/*
```

## Next Steps
1. Start with Phase 1 (refactoring)
2. Then Phase 2 (core engine)
3. Then Phase 3 (statistics)
4. Then Phase 4 (API)
5. Finally Phase 5 (UI)
