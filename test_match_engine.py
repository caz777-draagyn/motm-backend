"""
Quick test script to verify the match engine runs without errors.
"""

from match_engine.models import Player, Team
from match_engine.constants import OUTFIELD_ATTRS, GOALKEEPER_ATTRS
from match_engine.simulator import simulate_match
from match_engine.statistics import aggregate_match_log_to_stats_v2

# Create test teams
home_players = [
    Player("Jack Smith", "GK", {attr: 10 for attr in GOALKEEPER_ATTRS}, is_goalkeeper=True),
    Player("Harry Brown", "DL", {attr: 10 for attr in OUTFIELD_ATTRS}),
    Player("Oliver Jones", "DC", {attr: 10 for attr in OUTFIELD_ATTRS}),
    Player("Liam Williams", "DC", {attr: 10 for attr in OUTFIELD_ATTRS}),
    Player("Charlie Johnson", "DR", {attr: 10 for attr in OUTFIELD_ATTRS}),
    Player("George Miller", "ML", {attr: 10 for attr in OUTFIELD_ATTRS}),
    Player("Noah Davis", "MC", {attr: 10 for attr in OUTFIELD_ATTRS}),
    Player("Oscar Wilson", "MC", {attr: 10 for attr in OUTFIELD_ATTRS}),
    Player("James Moore", "MR", {attr: 10 for attr in OUTFIELD_ATTRS}),
    Player("Alfie Taylor", "FC", {attr: 10 for attr in OUTFIELD_ATTRS}),
    Player("Thomas Anderson", "FC", {attr: 10 for attr in OUTFIELD_ATTRS}),
]

away_players = [
    Player("William Clark", "GK", {attr: 5 for attr in GOALKEEPER_ATTRS}, is_goalkeeper=True),
    Player("Henry Hall", "DC", {attr: 5 for attr in OUTFIELD_ATTRS}),
    Player("Jacob Lee", "DC", {attr: 5 for attr in OUTFIELD_ATTRS}),
    Player("Leo Walker", "DC", {attr: 5 for attr in OUTFIELD_ATTRS}),
    Player("Charlie White", "DMR", {attr: 5 for attr in OUTFIELD_ATTRS}),
    Player("Freddie Harris", "DML", {attr: 5 for attr in OUTFIELD_ATTRS}),
    Player("Archie Young", "MC", {attr: 5 for attr in OUTFIELD_ATTRS}),
    Player("Ethan King", "MC", {attr: 5 for attr in OUTFIELD_ATTRS}),
    Player("Alexander Wright", "FC", {attr: 5 for attr in OUTFIELD_ATTRS}),
    Player("Joshua Scott", "FC", {attr: 5 for attr in OUTFIELD_ATTRS}),
    Player("Logan Green", "FC", {attr: 5 for attr in OUTFIELD_ATTRS}),
]

home_team = Team("Home United", home_players)
away_team = Team("Away FC", away_players)

print("Testing match engine...")
print(f"Home team: {home_team.name} ({len(home_team.players)} players)")
print(f"Away team: {away_team.name} ({len(away_team.players)} players)")

# Run simulation
print("\nRunning simulation...")
sim = simulate_match(home_team, away_team, minutes=90)
print(f"Simulation completed! Match length: {sim.minutes} minutes")
print(f"Total events logged: {len(sim.log)}")

# Aggregate statistics
print("\nAggregating statistics...")
stats = aggregate_match_log_to_stats_v2(sim)
print("Statistics aggregated successfully!")

# Print basic stats
print("\n=== Match Results ===")
for team_name, team_stats in stats.team.items():
    print(f"\n{team_name}:")
    print(f"  Goals: {team_stats.shooting.goals}")
    print(f"  Shots: {team_stats.shooting.shots}")
    print(f"  Shots on target: {team_stats.shooting.shots_on}")
    print(f"  Creator attempts: {team_stats.creator_off.attempts}")
    print(f"  Creator successes: {team_stats.creator_off.successes}")

# Check skill usage
print("\n=== Skill Usage Sample ===")
for team_name, team_stats in stats.team.items():
    if team_stats.skill_usage.total_usage:
        print(f"\n{team_name} - Top 5 skills used:")
        top_skills = team_stats.skill_usage.total_usage.most_common(5)
        for skill, count in top_skills:
            print(f"  {skill}: {count}")

print("\n[SUCCESS] Match engine test completed successfully!")
