# Match Engine Implementation

## Overview
The match engine has been successfully refactored and integrated into the codebase with a complete test bench UI.

## Structure

### Match Engine Core (`match_engine/`)
- **`constants.py`**: Positions, attributes, and constants
- **`models.py`**: Player and Team classes for match simulation
- **`matrices.py`**: Matrix definitions and building functions
- **`evaluation.py`**: Evaluation formulas and sigmoid functions
- **`simulator.py`**: MatchSimulator class - runs minute-by-minute simulation
- **`statistics.py`**: Statistics collection with skill usage tracking

### API Endpoints (`api/`)
- **`match_engine.py`**: 
  - `POST /api/match-engine/simulate` - Simulate a single match
  - `GET /api/match-engine/constants` - Get available positions/attributes
- **`test_bench.py`**:
  - `GET /api/test-bench/` - Serve test bench UI
  - `POST /api/test-bench/simulate` - Batch simulation endpoint

### Test Bench UI (`templates/test_bench.html`)
- Full-featured web interface for:
  - Team selection (11 players each)
  - Position and attribute editing
  - Match count selection (1, 10, 100, 1000)
  - Full statistics display including skill usage

## Usage

### Running a Single Match via API
```python
POST /api/match-engine/simulate
{
    "home_team": {
        "name": "Home Team",
        "players": [
            {
                "name": "Player 1",
                "position": "GK",
                "attributes": {"Reflexes": 10, "Handling": 10, ...},
                "is_goalkeeper": true
            },
            ...
        ]
    },
    "away_team": {...},
    "minutes": 90
}
```

### Using the Test Bench UI
1. Start the FastAPI server
2. Navigate to `http://localhost:8000/api/test-bench/`
3. Configure both teams (players, positions, attributes)
4. Select number of matches to simulate
5. Click "Run Simulation"
6. View detailed results including:
   - Match summary (wins/draws)
   - Team statistics
   - Player statistics
   - Skill usage per player and team

## Features

### Skill Usage Tracking
Every evaluation tracks which attributes were used, allowing you to see:
- Which skills are used most frequently
- Skill usage by event type
- Per-player skill usage statistics

### Statistics Collected
- **Team Stats**: Goals, shots, shots on target, creator/finisher attempts and successes
- **Player Stats**: Goals, assists, shots, creator/finisher stats
- **Skill Usage**: Total usage and usage by event type for each skill

## Testing

Run the test script to verify the engine works:
```bash
python test_match_engine.py
```

## Next Steps

1. **Tune Evaluation Formulas**: The formulas in `evaluation.py` are currently placeholders and need to be tuned based on game balance requirements.

2. **Tactical Modifications**: The system is designed to support tactical choices that modify matrices (e.g., "attack on wings", "focus on X"). This can be implemented by:
   - Adding tactical modifiers to Team model
   - Modifying matrix building functions to apply tactical adjustments

3. **Integration with Database**: When ready, connect the match engine to database models:
   - Convert database Player/Club models to match engine Player/Team models
   - Store match results in database
   - Link to season/league system

## Notes

- The match engine is completely separate from database models - it uses its own Player/Team classes
- All matrices are built automatically from team formations
- Statistics include detailed skill usage tracking as requested
- The test bench UI provides a complete interface for tuning and testing
