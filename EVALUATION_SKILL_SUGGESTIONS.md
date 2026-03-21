# Evaluation Skill and Weight Suggestions

Based on football logic, here are suggested formulas for each evaluation situation using available attributes with appropriate weights.

## Formula Format
Each formula returns an X value: `attacker_skills - defender_skills`
- Positive X = attacker advantage
- Negative X = defender advantage
- The sigmoid converts X to probability

## Chance Creation Types

### Short Pass Creation
**Attacker Skills:**
- Passing (0.4) - Primary skill for short passes
- Vision (0.3) - Ability to see the pass
- Ball Control (0.2) - First touch and control
- Composure (0.1) - Under pressure

**Defender Skills:**
- Tackling (0.5) - Ability to intercept
- Marking (0.3) - Positioning to block passing lanes
- Positioning (0.2) - Anticipation

**Formula:**
```python
"Short": lambda attacker, defender: (
    0.4 * attacker.get_attr("Passing") +
    0.3 * attacker.get_attr("Vision") +
    0.2 * attacker.get_attr("Ball Control") +
    0.1 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("Tackling") +
    0.3 * defender.get_attr("Marking") +
    0.2 * defender.get_attr("Positioning")
)
```

### Long Pass Creation
**Attacker Skills:**
- Passing (0.5) - Primary skill for long passes
- Vision (0.3) - Ability to see long-range options
- Composure (0.2) - Execution under pressure

**Defender Skills:**
- Positioning (0.5) - Anticipation and positioning
- Marking (0.3) - Tracking and intercepting
- Tackling (0.2) - Ability to break up play

**Formula:**
```python
"Long": lambda attacker, defender: (
    0.5 * attacker.get_attr("Passing") +
    0.3 * attacker.get_attr("Vision") +
    0.2 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("Positioning") +
    0.3 * defender.get_attr("Marking") +
    0.2 * defender.get_attr("Tackling")
)
```

### Crossing Creation
**Attacker Skills:**
- Crossing (0.5) - Primary crossing ability
- Vision (0.2) - Seeing crossing opportunities
- Ball Control (0.15) - First touch before crossing
- Composure (0.15) - Under pressure from defender

**Defender Skills:**
- Marking (0.5) - Tracking wide players
- Positioning (0.3) - Cutting off crossing angles
- Tackling (0.2) - Closing down the crosser

**Formula:**
```python
"Crossing": lambda attacker, defender: (
    0.5 * attacker.get_attr("Crossing") +
    0.2 * attacker.get_attr("Vision") +
    0.15 * attacker.get_attr("Ball Control") +
    0.15 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("Marking") +
    0.3 * defender.get_attr("Positioning") +
    0.2 * defender.get_attr("Tackling")
)
```

### Through Ball Creation
**Attacker Skills:**
- Vision (0.4) - Key for through balls
- Passing (0.3) - Execution of the pass
- Composure (0.2) - Timing and execution
- Ball Control (0.1) - First touch

**Defender Skills:**
- Positioning (0.5) - Reading the through ball
- Marking (0.3) - Tracking runners
- Tackling (0.2) - Intercepting

**Formula:**
```python
"Through": lambda attacker, defender: (
    0.4 * attacker.get_attr("Vision") +
    0.3 * attacker.get_attr("Passing") +
    0.2 * attacker.get_attr("Composure") +
    0.1 * attacker.get_attr("Ball Control")
) - (
    0.5 * defender.get_attr("Positioning") +
    0.3 * defender.get_attr("Marking") +
    0.2 * defender.get_attr("Tackling")
)
```

### Solo Dribble Creation
**Attacker Skills:**
- Ball Control (0.4) - Close control
- Agility (0.25) - Quick changes of direction
- Acceleration (0.2) - Burst of speed
- Composure (0.15) - Under pressure

**Defender Skills:**
- Tackling (0.5) - Ability to win the ball
- Positioning (0.3) - Cutting off angles
- Marking (0.2) - Staying close

**Formula:**
```python
"Solo": lambda attacker, defender: (
    0.4 * attacker.get_attr("Ball Control") +
    0.25 * attacker.get_attr("Agility") +
    0.2 * attacker.get_attr("Acceleration") +
    0.15 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("Tackling") +
    0.3 * defender.get_attr("Positioning") +
    0.2 * defender.get_attr("Marking")
)
```

## Finishing Types

### FirstTime Finish
**Attacker Skills:**
- Finishing (0.4) - Primary finishing ability
- Composure (0.3) - Quick decision making
- Ball Control (0.2) - First touch
- Positioning (0.1) - Being in right place

**Defender Skills (GK):**
- Reflexes (0.5) - Quick reactions
- Positioning (0.3) - Being in right place
- Handling (0.2) - Catching the shot

**Formula:**
```python
"FirstTime": lambda attacker, defender: (
    0.4 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Composure") +
    0.2 * attacker.get_attr("Ball Control") +
    0.1 * attacker.get_attr("Positioning")
) - (
    0.5 * defender.get_attr("Reflexes") +
    0.3 * defender.get_attr("Positioning") +
    0.2 * defender.get_attr("Handling")
)
```

### Controlled Finish
**Attacker Skills:**
- Finishing (0.4) - Primary finishing ability
- Ball Control (0.3) - Controlling the ball
- Composure (0.2) - Taking time
- Positioning (0.1) - Being in right place

**Defender Skills (GK):**
- Reflexes (0.4) - Reaction time
- Positioning (0.3) - Anticipation
- Handling (0.3) - Catching ability

**Formula:**
```python
"Controlled": lambda attacker, defender: (
    0.4 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Ball Control") +
    0.2 * attacker.get_attr("Composure") +
    0.1 * attacker.get_attr("Positioning")
) - (
    0.4 * defender.get_attr("Reflexes") +
    0.3 * defender.get_attr("Positioning") +
    0.3 * defender.get_attr("Handling")
)
```

### Header Finish
**Attacker Skills:**
- Heading (0.5) - Primary heading ability
- Jump Reach (0.3) - Getting to the ball
- Positioning (0.2) - Being in right place

**Defender Skills (GK):**
- Aerial Reach (0.5) - Ability to claim crosses
- Positioning (0.3) - Being in right place
- Command of Area (0.2) - Dominating the box

**Formula:**
```python
"Header": lambda attacker, defender: (
    0.5 * attacker.get_attr("Heading") +
    0.3 * attacker.get_attr("Jump Reach") +
    0.2 * attacker.get_attr("Positioning")
) - (
    0.5 * defender.get_attr("Aerial Reach") +
    0.3 * defender.get_attr("Positioning") +
    0.2 * defender.get_attr("Command of Area")
)
```

### Chip Finish
**Attacker Skills:**
- Finishing (0.4) - Primary finishing ability
- Vision (0.3) - Seeing the opportunity
- Composure (0.2) - Execution
- Ball Control (0.1) - Touch

**Defender Skills (GK):**
- Positioning (0.5) - Being in right place
- Reflexes (0.3) - Quick reactions
- One-on-One (0.2) - Coming off line

**Formula:**
```python
"Chip": lambda attacker, defender: (
    0.4 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Vision") +
    0.2 * attacker.get_attr("Composure") +
    0.1 * attacker.get_attr("Ball Control")
) - (
    0.5 * defender.get_attr("Positioning") +
    0.3 * defender.get_attr("Reflexes") +
    0.2 * defender.get_attr("One-on-One")
)
```

### Finesse Finish
**Attacker Skills:**
- Finishing (0.4) - Primary finishing ability
- Ball Control (0.3) - Technique
- Composure (0.2) - Execution
- Vision (0.1) - Placement

**Defender Skills (GK):**
- Reflexes (0.5) - Quick reactions
- Positioning (0.3) - Anticipation
- Handling (0.2) - Catching ability

**Formula:**
```python
"Finesse": lambda attacker, defender: (
    0.4 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Ball Control") +
    0.2 * attacker.get_attr("Composure") +
    0.1 * attacker.get_attr("Vision")
) - (
    0.5 * defender.get_attr("Reflexes") +
    0.3 * defender.get_attr("Positioning") +
    0.2 * defender.get_attr("Handling")
)
```

### Power Finish
**Attacker Skills:**
- Finishing (0.4) - Primary finishing ability
- Strength (0.3) - Power in shot
- Composure (0.2) - Execution
- Ball Control (0.1) - Technique

**Defender Skills (GK):**
- Reflexes (0.4) - Quick reactions
- Handling (0.4) - Holding powerful shots
- Positioning (0.2) - Being in right place

**Formula:**
```python
"Power": lambda attacker, defender: (
    0.4 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Strength") +
    0.2 * attacker.get_attr("Composure") +
    0.1 * attacker.get_attr("Ball Control")
) - (
    0.4 * defender.get_attr("Reflexes") +
    0.4 * defender.get_attr("Handling") +
    0.2 * defender.get_attr("Positioning")
)
```

## Goalkeeper Saves

### FirstTime Save
**Attacker Skills:**
- Finishing (0.5) - Shot quality
- Composure (0.3) - Execution
- Ball Control (0.2) - First touch

**Defender Skills (GK):**
- Reflexes (0.6) - Quick reactions (most important)
- Positioning (0.3) - Being in right place
- Handling (0.1) - Catching

**Formula:**
```python
"FirstTime_save": lambda attacker, defender: (
    0.5 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Composure") +
    0.2 * attacker.get_attr("Ball Control")
) - (
    0.6 * defender.get_attr("Reflexes") +
    0.3 * defender.get_attr("Positioning") +
    0.1 * defender.get_attr("Handling")
)
```

### Controlled Save
**Attacker Skills:**
- Finishing (0.5) - Shot quality
- Ball Control (0.3) - Control
- Composure (0.2) - Execution

**Defender Skills (GK):**
- Reflexes (0.5) - Reaction time
- Positioning (0.3) - Anticipation
- Handling (0.2) - Catching ability

**Formula:**
```python
"Controlled_save": lambda attacker, defender: (
    0.5 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Ball Control") +
    0.2 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("Reflexes") +
    0.3 * defender.get_attr("Positioning") +
    0.2 * defender.get_attr("Handling")
)
```

### Header Save
**Attacker Skills:**
- Heading (0.5) - Header quality
- Jump Reach (0.3) - Getting to ball
- Positioning (0.2) - Being in right place

**Defender Skills (GK):**
- Aerial Reach (0.6) - Claiming crosses (most important)
- Positioning (0.3) - Being in right place
- Command of Area (0.1) - Dominating box

**Formula:**
```python
"Header_save": lambda attacker, defender: (
    0.5 * attacker.get_attr("Heading") +
    0.3 * attacker.get_attr("Jump Reach") +
    0.2 * attacker.get_attr("Positioning")
) - (
    0.6 * defender.get_attr("Aerial Reach") +
    0.3 * defender.get_attr("Positioning") +
    0.1 * defender.get_attr("Command of Area")
)
```

### Chip Save
**Attacker Skills:**
- Finishing (0.5) - Shot quality
- Vision (0.3) - Placement
- Composure (0.2) - Execution

**Defender Skills (GK):**
- Positioning (0.5) - Being in right place (most important)
- One-on-One (0.3) - Coming off line
- Reflexes (0.2) - Quick reactions

**Formula:**
```python
"Chip_save": lambda attacker, defender: (
    0.5 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Vision") +
    0.2 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("Positioning") +
    0.3 * defender.get_attr("One-on-One") +
    0.2 * defender.get_attr("Reflexes")
)
```

### Finesse Save
**Attacker Skills:**
- Finishing (0.5) - Shot quality
- Ball Control (0.3) - Technique
- Composure (0.2) - Execution

**Defender Skills (GK):**
- Reflexes (0.5) - Quick reactions
- Positioning (0.3) - Anticipation
- Handling (0.2) - Catching ability

**Formula:**
```python
"Finesse_save": lambda attacker, defender: (
    0.5 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Ball Control") +
    0.2 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("Reflexes") +
    0.3 * defender.get_attr("Positioning") +
    0.2 * defender.get_attr("Handling")
)
```

### Power Save
**Attacker Skills:**
- Finishing (0.5) - Shot quality
- Strength (0.3) - Power
- Composure (0.2) - Execution

**Defender Skills (GK):**
- Handling (0.5) - Holding powerful shots (most important)
- Reflexes (0.3) - Quick reactions
- Positioning (0.2) - Being in right place

**Formula:**
```python
"Power_save": lambda attacker, defender: (
    0.5 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Strength") +
    0.2 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("Handling") +
    0.3 * defender.get_attr("Reflexes") +
    0.2 * defender.get_attr("Positioning")
)
```

## Goalkeeper Intercepts

### Long Pass Intercept
**Attacker Skills:**
- Passing (0.5) - Pass quality
- Vision (0.3) - Placement
- Composure (0.2) - Execution

**Defender Skills (GK):**
- Positioning (0.5) - Being in right place
- Command of Area (0.3) - Dominating space
- Aerial Reach (0.2) - Getting to ball

**Formula:**
```python
"Long_intercept": lambda attacker, defender: (
    0.5 * attacker.get_attr("Passing") +
    0.3 * attacker.get_attr("Vision") +
    0.2 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("Positioning") +
    0.3 * defender.get_attr("Command of Area") +
    0.2 * defender.get_attr("Aerial Reach")
)
```

### Crossing Intercept
**Attacker Skills:**
- Crossing (0.5) - Cross quality
- Vision (0.3) - Placement
- Composure (0.2) - Execution

**Defender Skills (GK):**
- Aerial Reach (0.6) - Claiming crosses (most important)
- Command of Area (0.3) - Dominating box
- Positioning (0.1) - Being in right place

**Formula:**
```python
"Crossing_intercept": lambda attacker, defender: (
    0.5 * attacker.get_attr("Crossing") +
    0.3 * attacker.get_attr("Vision") +
    0.2 * attacker.get_attr("Composure")
) - (
    0.6 * defender.get_attr("Aerial Reach") +
    0.3 * defender.get_attr("Command of Area") +
    0.1 * defender.get_attr("Positioning")
)
```

### Through Ball Intercept
**Attacker Skills:**
- Vision (0.4) - Through ball quality
- Passing (0.3) - Execution
- Composure (0.3) - Timing

**Defender Skills (GK):**
- One-on-One (0.5) - Coming off line (most important)
- Positioning (0.3) - Reading the play
- Reflexes (0.2) - Quick reactions

**Formula:**
```python
"Through_intercept": lambda attacker, defender: (
    0.4 * attacker.get_attr("Vision") +
    0.3 * attacker.get_attr("Passing") +
    0.3 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("One-on-One") +
    0.3 * defender.get_attr("Positioning") +
    0.2 * defender.get_attr("Reflexes")
)
```

## Set Pieces

### Penalty
**Attacker Skills:**
- Finishing (0.5) - Primary finishing ability
- Composure (0.4) - Under pressure
- Vision (0.1) - Placement

**Defender Skills (GK):**
- Reflexes (0.5) - Quick reactions
- Positioning (0.3) - Anticipation
- One-on-One (0.2) - Penalty specialist

**Formula:**
```python
"Penalty": lambda attacker, defender: (
    0.5 * attacker.get_attr("Finishing") +
    0.4 * attacker.get_attr("Composure") +
    0.1 * attacker.get_attr("Vision")
) - (
    0.5 * defender.get_attr("Reflexes") +
    0.3 * defender.get_attr("Positioning") +
    0.2 * defender.get_attr("One-on-One")
)
```

### FreeKick
**Attacker Skills:**
- Finishing (0.4) - Shot quality
- Vision (0.3) - Placement and technique
- Composure (0.2) - Execution
- Ball Control (0.1) - Technique

**Defender Skills (GK):**
- Positioning (0.4) - Setting up the wall and position
- Reflexes (0.3) - Quick reactions
- Command of Area (0.2) - Organizing defense
- Handling (0.1) - Catching ability

**Formula:**
```python
"Freekick": lambda attacker, defender: (
    0.4 * attacker.get_attr("Finishing") +
    0.3 * attacker.get_attr("Vision") +
    0.2 * attacker.get_attr("Composure") +
    0.1 * attacker.get_attr("Ball Control")
) - (
    0.4 * defender.get_attr("Positioning") +
    0.3 * defender.get_attr("Reflexes") +
    0.2 * defender.get_attr("Command of Area") +
    0.1 * defender.get_attr("Handling")
)
```

### Corner
**Attacker Skills:**
- Crossing (0.5) - Cross quality
- Vision (0.3) - Placement
- Composure (0.2) - Execution

**Defender Skills (GK):**
- Aerial Reach (0.5) - Claiming corners
- Command of Area (0.3) - Organizing defense
- Positioning (0.2) - Being in right place

**Formula:**
```python
"Corner": lambda attacker, defender: (
    0.5 * attacker.get_attr("Crossing") +
    0.3 * attacker.get_attr("Vision") +
    0.2 * attacker.get_attr("Composure")
) - (
    0.5 * defender.get_attr("Aerial Reach") +
    0.3 * defender.get_attr("Command of Area") +
    0.2 * defender.get_attr("Positioning")
)
```

## Finisher Types (for chance creation success)

These use the same formulas as the finishing types above, but are evaluated during the finisher phase of chance creation.

### Short_finisher, Long_finisher, Crossing_finisher, Through_finisher, Solo_finisher
These should use the same formulas as their corresponding chance types, but evaluated from the finisher's perspective.

## Notes

1. **Weight Sum**: All weights in each formula sum to 1.0 for both attacker and defender
2. **Attribute Range**: Attributes are 0-20, so X values will typically range from -40 to +40
3. **Sigmoid Parameters**: The current default (a=0.2, c=0, L=1) should work well with these X values
4. **Tuning**: These weights are starting points and should be tuned based on match results
5. **Context**: Some situations might benefit from additional context (e.g., fatigue affecting Stamina, match situation affecting Composure)
