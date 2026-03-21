# Set Piece (Penalty & Free Kick) Probability Analysis

## Current Implementation

### Event Flow
1. **Per Minute**: `decide_event()` returns `True` with **50% probability** (line 106)
2. **If event occurs**: Creation phase happens
3. **If creation succeeds**: Check for set pieces (lines 276-284)
4. **If finisher selected**: Check for set pieces again (lines 312-320)

### Set Piece Probabilities

#### During Creation Phase (after successful creation)
**Location**: `match_engine/simulator.py` lines 276-284

```python
# Check for special events during creation
if random.random() < 0.01:  # 1% chance penalty
    self.log.append((minute, "special", "penalty_awarded", team.name, "during_creation"))
    self.handle_penalty(team, opponent_team, minute)
    continue
elif random.random() < 0.02:  # 2% chance free kick
    self.log.append((minute, "special", "free_kick_awarded", team.name, "during_creation"))
    self.handle_freekick(team, opponent_team, minute)
    continue
```

**Values**:
- **Penalty**: 1% chance (0.01)
- **Free Kick**: 2% chance (0.02) - checked only if penalty didn't occur

**Note**: These are checked sequentially, so:
- Penalty probability: 1%
- Free kick probability: 2% (but only if penalty didn't happen)
- Total set piece probability: ~2.98% (1% + 2% * 99%)

#### During Finishing Phase (after finisher selection)
**Location**: `match_engine/simulator.py` lines 312-320

```python
# Check for special events during finishing
if random.random() < 0.005:  # 0.5% penalty chance
    self.log.append((minute, "special", "penalty_awarded", team.name, "during_finish"))
    self.handle_penalty(team, opponent_team, minute)
    continue
elif random.random() < 0.015:  # 1.5% free kick chance
    self.log.append((minute, "special", "free_kick_awarded", team.name, "during_finish"))
    self.handle_freekick(team, opponent_team, minute)
    continue
```

**Values**:
- **Penalty**: 0.5% chance (0.005)
- **Free Kick**: 1.5% chance (0.015) - checked only if penalty didn't occur

**Note**: These are checked sequentially, so:
- Penalty probability: 0.5%
- Free kick probability: 1.5% (but only if penalty didn't happen)
- Total set piece probability: ~1.99% (0.5% + 1.5% * 99.5%)

## Expected Frequency Calculation

### Assumptions
- 90-minute match
- 50% chance of event per minute = **45 events per match**
- Assume ~50% of creations succeed = **22.5 successful creations**
- All successful creations proceed to finisher selection = **22.5 finisher selections**

### Expected Set Pieces Per Match

**From Creation Phase**:
- Penalties: 22.5 × 0.01 = **0.225 penalties**
- Free kicks: 22.5 × 0.02 = **0.45 free kicks**
- Total: **~0.675 set pieces**

**From Finishing Phase**:
- Penalties: 22.5 × 0.005 = **0.1125 penalties**
- Free kicks: 22.5 × 0.015 = **0.3375 free kicks**
- Total: **~0.45 set pieces**

**Combined Total**: **~1.12 set pieces per match**

## Real-World Comparison

In real football:
- **Penalties**: ~0.2-0.3 per match (1 every 3-5 matches)
- **Free kicks (scoring opportunities)**: ~2-4 per match
- **Total set pieces**: ~2-4 per match

## Current Implementation (Updated)

The probabilities have been **reduced** to more realistic values:
1. Set pieces are checked in **two separate phases** (creation + finishing)
2. Creation phase: Penalty 1%, Free kick 2%
3. Finishing phase: Penalty 0.5%, Free kick 1.5%
4. Expected total: **~1.12 set pieces per match**

This gives:
- **~0.79 free kicks per match** (realistic: 2-4 per match, but many are not scoring opportunities)
- **~0.34 penalties per match** (realistic: 0.2-0.3 per match)

**Note**: Free kicks are counted as shots in statistics, and the taker is selected randomly from all players, which can lead to uneven distribution across players.
