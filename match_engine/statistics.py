"""
Statistics collection and aggregation for match simulations.
Tracks team stats, player stats, and individual skill usage.
"""

from collections import defaultdict, Counter
from typing import Dict, List
from .models import Team
from .simulator import MatchSimulator
from .evaluation import EVENT_SKILL_WEIGHTS
from .constants import OUTFIELD_ATTRS, GOALKEEPER_ATTRS

# GK-only skills (skills that should NOT appear for outfield players)
GK_ONLY_SKILLS = {"Aerial Reach", "Command of Area", "Handling", "One-on-One", "Reflexes"}


def filter_skills_for_player(skills: Dict[str, float], is_goalkeeper: bool) -> Dict[str, float]:
    """
    Filter skills based on player type (GK vs outfield).
    
    Args:
        skills: Dictionary of skill -> weight (or count)
        is_goalkeeper: Whether the player is a goalkeeper
    
    Returns:
        Filtered dictionary with only appropriate skills for the player type
    """
    if is_goalkeeper:
        # GKs can use all skills (they have both GK and some outfield skills)
        return skills
    else:
        # Outfield players should NOT have GK-only skills
        return {skill: weight for skill, weight in skills.items() if skill not in GK_ONLY_SKILLS}


def filter_skills_list_for_player(skills: List[str], is_goalkeeper: bool) -> List[str]:
    """
    Filter skills list based on player type (GK vs outfield).
    
    Args:
        skills: List of skill names
        is_goalkeeper: Whether the player is a goalkeeper
    
    Returns:
        Filtered list with only appropriate skills for the player type
    """
    if is_goalkeeper:
        # GKs can use all skills
        return skills
    else:
        # Outfield players should NOT have GK-only skills
        return [skill for skill in skills if skill not in GK_ONLY_SKILLS]


class OffDefSplit:
    """Holds per-type (Counter) and totals for a phase."""
    def __init__(self):
        self.attempt_by_type = Counter()
        self.success_by_type = Counter()

    @property
    def attempts(self):
        return sum(self.attempt_by_type.values())
    
    @property
    def successes(self):
        return sum(self.success_by_type.values())


class ShootingSplit:
    """Shooting split by finish type."""
    def __init__(self):
        self.shots_by_type = Counter()
        self.shots_on_by_type = Counter()
        self.goals_by_type = Counter()

    @property
    def shots(self):
        return sum(self.shots_by_type.values())
    
    @property
    def shots_on(self):
        return sum(self.shots_on_by_type.values())
    
    @property
    def goals(self):
        return sum(self.goals_by_type.values())


class GoalkeeperStats:
    """Goalkeeper-specific statistics."""
    def __init__(self):
        # Intercept statistics by chance type (Long, Crossing, Through)
        self.intercept_attempts_by_type = Counter()  # Attempted intercepts per chance type
        self.intercept_successes_by_type = Counter()  # Successful intercepts per chance type
        
        # Corner intercept statistics
        self.corner_intercepts_attempted = 0  # Number of corners where GK attempted intercept
        self.corner_intercepts_successful = 0  # Number of successful corner intercepts
        
        # Shot statistics by finish type (FirstTime, Controlled, Header, Chip, Finesse, Power, Penalty, Freekick)
        self.shots_conceded_by_type = Counter()  # Total shots faced per finish type
        self.shots_on_target_by_type = Counter()  # Shots on target faced per finish type
        self.saves_by_type = Counter()  # Saves made per finish type
    
    @property
    def intercept_attempts(self):
        return sum(self.intercept_attempts_by_type.values())
    
    @property
    def intercept_successes(self):
        return sum(self.intercept_successes_by_type.values())
    
    @property
    def shots_conceded(self):
        return sum(self.shots_conceded_by_type.values())
    
    @property
    def shots_on_target(self):
        return sum(self.shots_on_target_by_type.values())
    
    @property
    def saves(self):
        return sum(self.saves_by_type.values())
    
    def merge(self, other: 'GoalkeeperStats'):
        """Merge another GoalkeeperStats into this one."""
        self.intercept_attempts_by_type.update(other.intercept_attempts_by_type)
        self.intercept_successes_by_type.update(other.intercept_successes_by_type)
        self.corner_intercepts_attempted += other.corner_intercepts_attempted
        self.corner_intercepts_successful += other.corner_intercepts_successful
        self.shots_conceded_by_type.update(other.shots_conceded_by_type)
        self.shots_on_target_by_type.update(other.shots_on_target_by_type)
        self.saves_by_type.update(other.saves_by_type)


class SkillUsage:
    """Tracks individual skill usage in evaluations (unweighted: each skill counts as +1)."""
    def __init__(self):
        # skill_name -> event_type -> count
        # e.g., {"Finishing": {"FirstTime": 5, "Power": 3}, "Crossing": {"Crossing": 10}}
        self.usage_by_event = defaultdict(Counter)
        # Total count per skill
        self.total_usage = Counter()
    
    def add_usage(self, skills: List[str], event_type: str):
        """Record skill usage for an event (unweighted: +1 per skill)."""
        for skill in skills:
            self.usage_by_event[skill][event_type] += 1
            self.total_usage[skill] += 1
    
    def merge(self, other: 'SkillUsage'):
        """Merge another SkillUsage into this one."""
        for skill, event_counts in other.usage_by_event.items():
            self.usage_by_event[skill].update(event_counts)
        self.total_usage.update(other.total_usage)


class WeightedSkillUsage:
    """Tracks individual skill usage with weights (skills weighted by their contribution to evaluation)."""
    def __init__(self):
        # skill_name -> event_type -> weighted_sum
        # e.g., {"Finishing": {"FirstTime": 12.4, "Power": 8.7}, "Crossing": {"Crossing": 15.2}}
        self.usage_by_event = defaultdict(lambda: defaultdict(float))
        # Total weighted usage per skill
        self.total_usage = defaultdict(float)
    
    def add_usage(self, skills_with_weights: Dict[str, float], event_type: str):
        """Record weighted skill usage for an event."""
        for skill, weight in skills_with_weights.items():
            self.usage_by_event[skill][event_type] += weight
            self.total_usage[skill] += weight
    
    def merge(self, other: 'WeightedSkillUsage'):
        """Merge another WeightedSkillUsage into this one."""
        for skill, event_weights in other.usage_by_event.items():
            for event_type, weight in event_weights.items():
                self.usage_by_event[skill][event_type] += weight
                self.total_usage[skill] += weight


class TeamStatsV2:
    def __init__(self, name: str):
        self.name = name
        self.creator_off = OffDefSplit()
        self.creator_def = OffDefSplit()
        self.finisher_off = OffDefSplit()
        self.finisher_def = OffDefSplit()
        self.shooting = ShootingSplit()
        self.skill_usage = SkillUsage()  # Team-level skill usage (unweighted)
        self.weighted_skill_usage = WeightedSkillUsage()  # Team-level skill usage (weighted)
        self.result_frequency = Counter()  # Track wins, draws, losses
        self.score_frequency = Counter()  # Track specific match scores (e.g., "1-0", "2-1")

    def merge(self, other: 'TeamStatsV2'):
        self.creator_off.attempt_by_type.update(other.creator_off.attempt_by_type)
        self.creator_off.success_by_type.update(other.creator_off.success_by_type)
        self.creator_def.attempt_by_type.update(other.creator_def.attempt_by_type)
        self.creator_def.success_by_type.update(other.creator_def.success_by_type)
        self.finisher_off.attempt_by_type.update(other.finisher_off.attempt_by_type)
        self.finisher_off.success_by_type.update(other.finisher_off.success_by_type)
        self.finisher_def.attempt_by_type.update(other.finisher_def.attempt_by_type)
        self.finisher_def.success_by_type.update(other.finisher_def.success_by_type)
        self.shooting.shots_by_type.update(other.shooting.shots_by_type)
        self.shooting.shots_on_by_type.update(other.shooting.shots_on_by_type)
        self.shooting.goals_by_type.update(other.shooting.goals_by_type)
        self.result_frequency.update(other.result_frequency)
        self.score_frequency.update(other.score_frequency)
        self.skill_usage.merge(other.skill_usage)
        self.weighted_skill_usage.merge(other.weighted_skill_usage)


class PlayerStatsV2:
    def __init__(self, name: str, team: str, position: str = ""):
        self.name = name
        self.team = team
        self.position = position
        self.creator_off = OffDefSplit()
        self.creator_def = OffDefSplit()
        self.finisher_off = OffDefSplit()
        self.finisher_def = OffDefSplit()
        self.shooting = ShootingSplit()
        self.assists_by_chance_type = Counter()
        self.skill_usage = SkillUsage()  # Player-level skill usage (unweighted)
        self.weighted_skill_usage = WeightedSkillUsage()  # Player-level skill usage (weighted)
        self.goalkeeper_stats = GoalkeeperStats()  # Goalkeeper-specific stats (only populated for GKs)
        
        # Corner statistics
        self.corners_taken = 0  # Number of corners taken by this player
        self.corners_successful = 0  # Number of successful corner deliveries (not intercepted by GK)
        self.corner_shots = 0  # Number of shots taken from corners
        self.corner_shots_success = 0  # Number of successful corner finisher events
        self.corner_goals = 0  # Number of goals scored from corners

    @property
    def goals(self):
        return self.shooting.goals
    
    @property
    def shots(self):
        return self.shooting.shots
    
    @property
    def shots_on(self):
        return self.shooting.shots_on
    
    @property
    def assists(self):
        return sum(self.assists_by_chance_type.values())

    def merge(self, other: 'PlayerStatsV2'):
        self.creator_off.attempt_by_type.update(other.creator_off.attempt_by_type)
        self.creator_off.success_by_type.update(other.creator_off.success_by_type)
        self.creator_def.attempt_by_type.update(other.creator_def.attempt_by_type)
        self.creator_def.success_by_type.update(other.creator_def.success_by_type)
        self.finisher_off.attempt_by_type.update(other.finisher_off.attempt_by_type)
        self.finisher_off.success_by_type.update(other.finisher_off.success_by_type)
        self.finisher_def.attempt_by_type.update(other.finisher_def.attempt_by_type)
        self.finisher_def.success_by_type.update(other.finisher_def.success_by_type)
        self.shooting.shots_by_type.update(other.shooting.shots_by_type)
        self.shooting.shots_on_by_type.update(other.shooting.shots_on_by_type)
        self.shooting.goals_by_type.update(other.shooting.goals_by_type)
        self.assists_by_chance_type.update(other.assists_by_chance_type)
        self.skill_usage.merge(other.skill_usage)
        self.weighted_skill_usage.merge(other.weighted_skill_usage)
        self.goalkeeper_stats.merge(other.goalkeeper_stats)
        self.corners_taken += other.corners_taken
        self.corners_successful += other.corners_successful
        self.corner_shots += other.corner_shots
        self.corner_shots_success += other.corner_shots_success
        self.corner_goals += other.corner_goals


class MatchStatsV2:
    def __init__(self, home_team: Team, away_team: Team):
        self.team = {
            home_team.name: TeamStatsV2(home_team.name),
            away_team.name: TeamStatsV2(away_team.name),
        }
        self.player = {}  # (team, name) -> PlayerStatsV2
        self.home_team = home_team
        self.away_team = away_team
        # Map player names to positions
        self._player_positions = {}
        for team in [home_team, away_team]:
            for player in team.players:
                self._player_positions[(team.name, player.name)] = player.matrix_position

    def ps(self, team_name: str, player_name: str) -> PlayerStatsV2:
        """Get or create player stats."""
        key = (team_name, player_name)
        if key not in self.player:
            position = self._player_positions.get(key, "")
            self.player[key] = PlayerStatsV2(player_name, team_name, position)
        return self.player[key]

    def merge(self, other: 'MatchStatsV2'):
        for t in self.team:
            self.team[t].merge(other.team[t])
        for key, pst in other.player.items():
            self.ps(*key).merge(pst)


def aggregate_match_log_to_stats_v2(sim: MatchSimulator) -> MatchStatsV2:
    """Aggregate match log into statistics with skill usage tracking."""
    ms = MatchStatsV2(sim.home_team, sim.away_team)
    home, away = sim.home_team.name, sim.away_team.name

    # Remember last successful creation per (minute, team) for assist credit
    last_creation = {}  # (minute, team) -> {"creator": str, "chance_type": str}
    # Remember corner creator per (minute, team) for assist credit on corner goals
    corner_creator = {}  # (minute, team) -> str (corner taker name)

    for entry in sim.log:
        minute, section, tag = entry[:3]
        rest = entry[3:]

        # Extract skills_used if present (last element)
        skills_used = []
        if len(rest) > 0 and isinstance(rest[-1], list):
            skills_used = rest[-1]
            rest = rest[:-1]

        # ------- CREATION PHASE -------
        if section == "result" and tag == "creation":
            outcome, prob, crit_s, creator, defender, chance_type, atk_team = rest[:7]
            def_team = away if atk_team == home else home

            # Team offense & defense
            ms.team[atk_team].creator_off.attempt_by_type[chance_type] += 1
            ms.team[def_team].creator_def.attempt_by_type[chance_type] += 1

            # Player ledgers
            ms.ps(atk_team, creator).creator_off.attempt_by_type[chance_type] += 1
            ms.ps(def_team, defender).creator_def.attempt_by_type[chance_type] += 1

            # Skill usage (unweighted) - filter GK-only skills based on player position
            event_type = chance_type
            creator_pos = ms.ps(atk_team, creator).position
            defender_pos = ms.ps(def_team, defender).position
            creator_is_gk = (creator_pos == "GK")
            defender_is_gk = (defender_pos == "GK")
            
            creator_skills = filter_skills_list_for_player(skills_used, creator_is_gk)
            defender_skills = filter_skills_list_for_player(skills_used, defender_is_gk)
            
            ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
            ms.team[def_team].skill_usage.add_usage(skills_used, event_type)
            ms.ps(atk_team, creator).skill_usage.add_usage(creator_skills, event_type)
            ms.ps(def_team, defender).skill_usage.add_usage(defender_skills, event_type)
            
            # Weighted skill usage - filter GK-only skills based on player position
            skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
            if skill_weights:
                creator_weights = filter_skills_for_player(skill_weights, creator_is_gk)
                defender_weights = filter_skills_for_player(skill_weights, defender_is_gk)
                ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.team[def_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.ps(atk_team, creator).weighted_skill_usage.add_usage(creator_weights, event_type)
                ms.ps(def_team, defender).weighted_skill_usage.add_usage(defender_weights, event_type)

            if outcome == "success":
                ms.team[atk_team].creator_off.success_by_type[chance_type] += 1
                ms.ps(atk_team, creator).creator_off.success_by_type[chance_type] += 1
                last_creation[(minute, atk_team)] = {"creator": creator, "chance_type": chance_type}
            else:
                ms.team[def_team].creator_def.success_by_type[chance_type] += 1
                ms.ps(def_team, defender).creator_def.success_by_type[chance_type] += 1

        # ------- FINISH DUEL -------
        elif section == "result" and tag == "finish":
            outcome, prob, pressure_level, finisher, fdef, finish_type, atk_team = rest[:7]
            def_team = away if atk_team == home else home

            ms.team[atk_team].finisher_off.attempt_by_type[finish_type] += 1
            ms.team[def_team].finisher_def.attempt_by_type[finish_type] += 1
            ms.ps(atk_team, finisher).finisher_off.attempt_by_type[finish_type] += 1
            ms.ps(def_team, fdef).finisher_def.attempt_by_type[finish_type] += 1

            # Skill usage (unweighted) - filter GK-only skills based on player position
            event_type = f"{finish_type}_finisher"
            finisher_pos = ms.ps(atk_team, finisher).position
            fdef_pos = ms.ps(def_team, fdef).position
            finisher_is_gk = (finisher_pos == "GK")
            fdef_is_gk = (fdef_pos == "GK")
            
            finisher_skills = filter_skills_list_for_player(skills_used, finisher_is_gk)
            fdef_skills = filter_skills_list_for_player(skills_used, fdef_is_gk)
            
            ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
            ms.team[def_team].skill_usage.add_usage(skills_used, event_type)
            ms.ps(atk_team, finisher).skill_usage.add_usage(finisher_skills, event_type)
            ms.ps(def_team, fdef).skill_usage.add_usage(fdef_skills, event_type)
            
            # Weighted skill usage - filter GK-only skills based on player position
            skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
            if skill_weights:
                finisher_weights = filter_skills_for_player(skill_weights, finisher_is_gk)
                fdef_weights = filter_skills_for_player(skill_weights, fdef_is_gk)
                ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.team[def_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.ps(atk_team, finisher).weighted_skill_usage.add_usage(finisher_weights, event_type)
                ms.ps(def_team, fdef).weighted_skill_usage.add_usage(fdef_weights, event_type)

            if outcome == "success":
                ms.team[atk_team].finisher_off.success_by_type[finish_type] += 1
                ms.ps(atk_team, finisher).finisher_off.success_by_type[finish_type] += 1
            else:
                ms.team[def_team].finisher_def.success_by_type[finish_type] += 1
                ms.ps(def_team, fdef).finisher_def.success_by_type[finish_type] += 1

        # ------- SHOT QUALITY -------
        elif section == "result" and tag == "shot_quality":
            outcome, prob, finisher, fdef, finish_type, atk_team = rest[:6]
            def_team = away if atk_team == home else home
            
            ms.team[atk_team].shooting.shots_by_type[finish_type] += 1
            ms.ps(atk_team, finisher).shooting.shots_by_type[finish_type] += 1
            
            # Track shots conceded and shots on target for the defending team's goalkeeper
            def_team_obj = ms.away_team if atk_team == home else ms.home_team
            def_goalkeeper = None
            for player in def_team_obj.players:
                if player.matrix_position == "GK":
                    def_goalkeeper = player.name
                    break
            
            if def_goalkeeper:
                def_gk_stats = ms.ps(def_team, def_goalkeeper).goalkeeper_stats
                def_gk_stats.shots_conceded_by_type[finish_type] += 1
                if outcome == "on_target":
                    def_gk_stats.shots_on_target_by_type[finish_type] += 1

            # Skill usage (unweighted) - filter GK-only skills based on player position
            event_type = finish_type
            finisher_pos = ms.ps(atk_team, finisher).position
            finisher_is_gk = (finisher_pos == "GK")
            
            finisher_skills = filter_skills_list_for_player(skills_used, finisher_is_gk)
            
            ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
            ms.ps(atk_team, finisher).skill_usage.add_usage(finisher_skills, event_type)
            
            # Weighted skill usage - filter GK-only skills based on player position
            skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
            if skill_weights:
                finisher_weights = filter_skills_for_player(skill_weights, finisher_is_gk)
                ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.ps(atk_team, finisher).weighted_skill_usage.add_usage(finisher_weights, event_type)

            if outcome == "on_target":
                ms.team[atk_team].shooting.shots_on_by_type[finish_type] += 1
                ms.ps(atk_team, finisher).shooting.shots_on_by_type[finish_type] += 1

        # ------- SAVE / GOAL RESOLUTION -------
        elif section == "result" and tag == "save":
            outcome, prob, finisher, goalkeeper, finish_type, atk_team = rest[:6]
            def_team = away if atk_team == home else home

            # Track saves for goalkeeper
            if outcome == "saved":
                gk_stats = ms.ps(def_team, goalkeeper).goalkeeper_stats
                gk_stats.saves_by_type[finish_type] += 1

            # Skill usage (unweighted) - filter GK-only skills based on player position
            # For saves: GK is initiator (has GK skills), finisher is defender (outfield, should not have GK skills)
            event_type = f"{finish_type}_save"
            finisher_pos = ms.ps(atk_team, finisher).position
            goalkeeper_pos = ms.ps(def_team, goalkeeper).position
            finisher_is_gk = (finisher_pos == "GK")
            goalkeeper_is_gk = (goalkeeper_pos == "GK")
            
            finisher_skills = filter_skills_list_for_player(skills_used, finisher_is_gk)
            goalkeeper_skills = filter_skills_list_for_player(skills_used, goalkeeper_is_gk)
            
            ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
            ms.team[def_team].skill_usage.add_usage(skills_used, event_type)
            ms.ps(atk_team, finisher).skill_usage.add_usage(finisher_skills, event_type)
            ms.ps(def_team, goalkeeper).skill_usage.add_usage(goalkeeper_skills, event_type)
            
            # Weighted skill usage - filter GK-only skills based on player position
            skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
            if skill_weights:
                finisher_weights = filter_skills_for_player(skill_weights, finisher_is_gk)
                goalkeeper_weights = filter_skills_for_player(skill_weights, goalkeeper_is_gk)
                ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.team[def_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.ps(atk_team, finisher).weighted_skill_usage.add_usage(finisher_weights, event_type)
                ms.ps(def_team, goalkeeper).weighted_skill_usage.add_usage(goalkeeper_weights, event_type)

            if outcome == "goal":
                ms.team[atk_team].shooting.goals_by_type[finish_type] += 1
                ms.ps(atk_team, finisher).shooting.goals_by_type[finish_type] += 1
                # Assist if creator from same minute/team
                k = (minute, atk_team)
                if k in last_creation:
                    creation_info = last_creation[k]
                    if isinstance(creation_info, dict) and "creator" in creation_info and "chance_type" in creation_info:
                        creator = creation_info["creator"]
                        ch_type = creation_info["chance_type"]
                        if creator != finisher:
                            ms.ps(atk_team, creator).assists_by_chance_type[ch_type] += 1

        # ------- CORNERS -------
        elif section == "corner":
            phase = tag  # tag is already "gk_intercept", "delivery", "finish", etc.
            if phase == "gk_intercept":
                # GK intercept evaluation: creator vs goalkeeper
                outcome, prob, crit_s, creator, goalkeeper, chance_type, atk_team = rest[:7]
                def_team = away if atk_team == home else home
                
                # Track corner taken
                ms.ps(atk_team, creator).corners_taken += 1
                
                # Track GK intercept attempt
                gk_stats = ms.ps(def_team, goalkeeper).goalkeeper_stats
                gk_stats.corner_intercepts_attempted += 1
                
                # Skill usage (unweighted) - filter GK-only skills based on player position
                event_type = chance_type
                creator_pos = ms.ps(atk_team, creator).position
                creator_is_gk = (creator_pos == "GK")
                goalkeeper_pos = ms.ps(def_team, goalkeeper).position
                goalkeeper_is_gk = (goalkeeper_pos == "GK")
                
                creator_skills = filter_skills_list_for_player(skills_used, creator_is_gk)
                goalkeeper_skills = filter_skills_list_for_player(skills_used, goalkeeper_is_gk)
                
                ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
                ms.ps(atk_team, creator).skill_usage.add_usage(creator_skills, event_type)
                ms.ps(def_team, goalkeeper).skill_usage.add_usage(goalkeeper_skills, event_type)
                
                # Weighted skill usage
                skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
                if skill_weights:
                    creator_weights = filter_skills_for_player(skill_weights, creator_is_gk)
                    goalkeeper_weights = filter_skills_for_player(skill_weights, goalkeeper_is_gk)
                    ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                    ms.ps(atk_team, creator).weighted_skill_usage.add_usage(creator_weights, event_type)
                    ms.ps(def_team, goalkeeper).weighted_skill_usage.add_usage(goalkeeper_weights, event_type)

                if outcome == "intercepted":
                    # GK intercepted the corner
                    gk_stats.corner_intercepts_successful += 1
                # If not intercepted, corner delivery successful (tracked in "delivery" phase)

            elif phase == "delivery":
                # Corner delivery successful (GK did not intercept)
                outcome, prob, crit_s, creator, goalkeeper, chance_type, atk_team = rest[:7]
                def_team = away if atk_team == home else home
                
                # Track successful corner delivery
                ms.ps(atk_team, creator).corners_successful += 1
                
                # Store corner creator for potential assist credit
                corner_creator[(minute, atk_team)] = creator

            elif phase == "finish":
                # Log format: outcome, prob, crit_s, finisher, fdef, finish_type, atk_team
                outcome, prob, crit_s, finisher, fdef, finish_type, atk_team = rest[:7]
                def_team = away if atk_team == home else home
                # Note: For corners, the event is "Corner_finisher"
                event_type = "Corner_finisher"
                
                # Track corner finisher attempts
                ms.ps(atk_team, finisher).corner_shots += 1  # Corner shot attempt
                
                finisher_pos = ms.ps(atk_team, finisher).position
                finisher_is_gk = (finisher_pos == "GK")
                
                finisher_skills = filter_skills_list_for_player(skills_used, finisher_is_gk)
                
                ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
                ms.ps(atk_team, finisher).skill_usage.add_usage(finisher_skills, event_type)
                
                # Weighted skill usage - filter GK-only skills based on player position
                skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
                if skill_weights:
                    finisher_weights = filter_skills_for_player(skill_weights, finisher_is_gk)
                    ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                    ms.ps(atk_team, finisher).weighted_skill_usage.add_usage(finisher_weights, event_type)

                if outcome == "success":
                    ms.ps(atk_team, finisher).corner_shots_success += 1
                # Corner shots are tracked separately in shot_quality phase

            elif phase == "shot_quality":
                outcome, prob, finisher, fdef, finish_type, atk_team = rest[:6]
                def_team = away if atk_team == home else home
                
                ms.team[atk_team].shooting.shots_by_type[finish_type] += 1
                if outcome == "on_target":
                    ms.team[atk_team].shooting.shots_on_by_type[finish_type] += 1
                ms.ps(atk_team, finisher).shooting.shots_by_type[finish_type] += 1
                if outcome == "on_target":
                    ms.ps(atk_team, finisher).shooting.shots_on_by_type[finish_type] += 1
                
                # Track shots conceded and shots on target for the defending team's goalkeeper
                def_team_obj = ms.away_team if atk_team == home else ms.home_team
                def_goalkeeper = None
                for player in def_team_obj.players:
                    if player.matrix_position == "GK":
                        def_goalkeeper = player.name
                        break
                
                if def_goalkeeper:
                    def_gk_stats = ms.ps(def_team, def_goalkeeper).goalkeeper_stats
                    def_gk_stats.shots_conceded_by_type[finish_type] += 1
                    if outcome == "on_target":
                        def_gk_stats.shots_on_target_by_type[finish_type] += 1

                # Skill usage (unweighted) - filter GK-only skills based on player position
                event_type = finish_type
                finisher_pos = ms.ps(atk_team, finisher).position
                finisher_is_gk = (finisher_pos == "GK")
                
                finisher_skills = filter_skills_list_for_player(skills_used, finisher_is_gk)
                
                ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
                ms.ps(atk_team, finisher).skill_usage.add_usage(finisher_skills, event_type)
                
                # Weighted skill usage - filter GK-only skills based on player position
                skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
                if skill_weights:
                    finisher_weights = filter_skills_for_player(skill_weights, finisher_is_gk)
                    ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                    ms.ps(atk_team, finisher).weighted_skill_usage.add_usage(finisher_weights, event_type)

            elif phase == "save":
                outcome, prob, finisher, goalkeeper, finish_type, atk_team = rest[:6]
                def_team = away if atk_team == home else home
                
                # Track saves for goalkeeper
                if outcome == "saved":
                    gk_stats = ms.ps(def_team, goalkeeper).goalkeeper_stats
                    gk_stats.saves_by_type[finish_type] += 1
                
                if outcome == "goal":
                    ms.team[atk_team].shooting.goals_by_type[finish_type] += 1
                    ms.ps(atk_team, finisher).shooting.goals_by_type[finish_type] += 1
                    # Track corner goal
                    ms.ps(atk_team, finisher).corner_goals += 1
                    
                    # Credit assist to corner taker if different from finisher
                    k = (minute, atk_team)
                    # Only credit assist if corner_creator exists (delivery phase was logged)
                    if k in corner_creator:
                        creator = corner_creator.get(k)
                        if creator and creator != finisher:
                            ms.ps(atk_team, creator).assists_by_chance_type["Corner"] += 1
                    # Don't check last_creation for corner goals - corners are handled separately
                    # Corner goals should always have corner_creator if the delivery was successful

                # Skill usage (unweighted) - filter GK-only skills based on player position
                # For saves: GK is initiator (has GK skills), finisher is defender (outfield, should not have GK skills)
                event_type = f"{finish_type}_save"
                finisher_pos = ms.ps(atk_team, finisher).position
                finisher_is_gk = (finisher_pos == "GK")
                
                finisher_skills = filter_skills_list_for_player(skills_used, finisher_is_gk)
                
                ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
                ms.ps(atk_team, finisher).skill_usage.add_usage(finisher_skills, event_type)
                
                # Weighted skill usage - filter GK-only skills based on player position
                skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
                if skill_weights:
                    finisher_weights = filter_skills_for_player(skill_weights, finisher_is_gk)
                    ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                    ms.ps(atk_team, finisher).weighted_skill_usage.add_usage(finisher_weights, event_type)

            elif phase == "finish_outcome":
                # Corner shot went off target (miss)
                outcome, prob, finisher, fdef, finish_type, atk_team = rest[:6]
                def_team = away if atk_team == home else home
                
                # Shot was already tracked in shot_quality phase, nothing more to do here
                # Just track skill usage if needed
                event_type = finish_type
                finisher_pos = ms.ps(atk_team, finisher).position
                finisher_is_gk = (finisher_pos == "GK")
                
                finisher_skills = filter_skills_list_for_player(skills_used, finisher_is_gk)
                
                ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
                ms.ps(atk_team, finisher).skill_usage.add_usage(finisher_skills, event_type)
                
                # Weighted skill usage - filter GK-only skills based on player position
                skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
                if skill_weights:
                    finisher_weights = filter_skills_for_player(skill_weights, finisher_is_gk)
                    ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                    ms.ps(atk_team, finisher).weighted_skill_usage.add_usage(finisher_weights, event_type)

        # ------- PENALTIES / FREEKICKS -------
        # Handle shot quality (on/off target)
        elif section == "special_result" and tag == "penalty":
            outcome, prob, taker, goalkeeper, atk_team = rest[:5]
            def_team = away if atk_team == home else home
            finish_type = "Penalty"
            
            ms.team[atk_team].shooting.shots_by_type[finish_type] += 1
            ms.ps(atk_team, taker).shooting.shots_by_type[finish_type] += 1
            
            # Track shots conceded for goalkeeper
            gk_stats = ms.ps(def_team, goalkeeper).goalkeeper_stats
            gk_stats.shots_conceded_by_type[finish_type] += 1
            
            if outcome == "on_target":
                ms.team[atk_team].shooting.shots_on_by_type[finish_type] += 1
                ms.ps(atk_team, taker).shooting.shots_on_by_type[finish_type] += 1
                gk_stats.shots_on_target_by_type[finish_type] += 1

            # Skill usage (unweighted) - filter GK-only skills based on player position
            event_type = finish_type
            taker_pos = ms.ps(atk_team, taker).position
            taker_is_gk = (taker_pos == "GK")
            taker_skills = filter_skills_list_for_player(skills_used, taker_is_gk)
            
            ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
            ms.ps(atk_team, taker).skill_usage.add_usage(taker_skills, event_type)
            
            # Weighted skill usage - filter GK-only skills based on player position
            skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
            if skill_weights:
                taker_weights = filter_skills_for_player(skill_weights, taker_is_gk)
                ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.ps(atk_team, taker).weighted_skill_usage.add_usage(taker_weights, event_type)

        # Handle penalty save (goal/saved)
        elif section == "special_result" and tag == "penalty_save":
            outcome, prob, taker, goalkeeper, atk_team = rest[:5]
            def_team = away if atk_team == home else home
            finish_type = "Penalty"
            gk_stats = ms.ps(def_team, goalkeeper).goalkeeper_stats
            
            if outcome == "goal":
                ms.team[atk_team].shooting.goals_by_type[finish_type] += 1
                ms.ps(atk_team, taker).shooting.goals_by_type[finish_type] += 1
            elif outcome == "saved":
                gk_stats.saves_by_type[finish_type] += 1
            
            # Skill usage for save event
            event_type = "Penalty_save"
            gk_pos = ms.ps(def_team, goalkeeper).position
            gk_is_gk = (gk_pos == "GK")
            gk_skills = filter_skills_list_for_player(skills_used, gk_is_gk)
            
            ms.team[def_team].skill_usage.add_usage(skills_used, event_type)
            ms.ps(def_team, goalkeeper).skill_usage.add_usage(gk_skills, event_type)
            
            skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
            if skill_weights:
                gk_weights = filter_skills_for_player(skill_weights, gk_is_gk)
                ms.team[def_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.ps(def_team, goalkeeper).weighted_skill_usage.add_usage(gk_weights, event_type)

        # Handle penalty miss (off target)
        elif section == "special_result" and tag == "penalty_miss":
            # Already tracked as shot in penalty log, nothing more to do
            pass

        # Handle freekick shot quality (on/off target)
        elif section == "special_result" and tag == "free_kick":
            outcome, prob, taker, goalkeeper, atk_team = rest[:5]
            def_team = away if atk_team == home else home
            finish_type = "Freekick"
            
            ms.team[atk_team].shooting.shots_by_type[finish_type] += 1
            ms.ps(atk_team, taker).shooting.shots_by_type[finish_type] += 1
            
            # Track shots conceded for goalkeeper
            gk_stats = ms.ps(def_team, goalkeeper).goalkeeper_stats
            gk_stats.shots_conceded_by_type[finish_type] += 1
            
            if outcome == "on_target":
                ms.team[atk_team].shooting.shots_on_by_type[finish_type] += 1
                ms.ps(atk_team, taker).shooting.shots_on_by_type[finish_type] += 1
                gk_stats.shots_on_target_by_type[finish_type] += 1

            # Skill usage (unweighted) - filter GK-only skills based on player position
            event_type = finish_type
            taker_pos = ms.ps(atk_team, taker).position
            taker_is_gk = (taker_pos == "GK")
            taker_skills = filter_skills_list_for_player(skills_used, taker_is_gk)
            
            ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
            ms.ps(atk_team, taker).skill_usage.add_usage(taker_skills, event_type)
            
            # Weighted skill usage - filter GK-only skills based on player position
            skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
            if skill_weights:
                taker_weights = filter_skills_for_player(skill_weights, taker_is_gk)
                ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.ps(atk_team, taker).weighted_skill_usage.add_usage(taker_weights, event_type)

        # Handle freekick save (goal/saved)
        elif section == "special_result" and tag == "free_kick_save":
            outcome, prob, taker, goalkeeper, atk_team = rest[:5]
            def_team = away if atk_team == home else home
            finish_type = "Freekick"
            gk_stats = ms.ps(def_team, goalkeeper).goalkeeper_stats
            
            if outcome == "goal":
                ms.team[atk_team].shooting.goals_by_type[finish_type] += 1
                ms.ps(atk_team, taker).shooting.goals_by_type[finish_type] += 1
            elif outcome == "saved":
                gk_stats.saves_by_type[finish_type] += 1
            
            # Skill usage for save event
            event_type = "Freekick_save"
            gk_pos = ms.ps(def_team, goalkeeper).position
            gk_is_gk = (gk_pos == "GK")
            gk_skills = filter_skills_list_for_player(skills_used, gk_is_gk)
            
            ms.team[def_team].skill_usage.add_usage(skills_used, event_type)
            ms.ps(def_team, goalkeeper).skill_usage.add_usage(gk_skills, event_type)
            
            skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
            if skill_weights:
                gk_weights = filter_skills_for_player(skill_weights, gk_is_gk)
                ms.team[def_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.ps(def_team, goalkeeper).weighted_skill_usage.add_usage(gk_weights, event_type)

        # Handle freekick miss (off target)
        elif section == "special_result" and tag == "free_kick_miss":
            # Already tracked as shot in free_kick log, nothing more to do
            pass

        # ------- GOALKEEPER INTERCEPT -------
        elif section == "result" and tag == "goalkeeper_intercept":
            outcome, prob, finisher, goalkeeper, chance_type, atk_team = rest[:6]
            def_team = away if atk_team == home else home

            # Track intercept attempts and successes for goalkeeper
            # chance_type is "Long", "Crossing", or "Through" - map to intercept type
            intercept_type = chance_type  # Long_intercept, Crossing_intercept, Through_intercept
            gk_stats = ms.ps(def_team, goalkeeper).goalkeeper_stats
            gk_stats.intercept_attempts_by_type[intercept_type] += 1
            if outcome == "success":
                gk_stats.intercept_successes_by_type[intercept_type] += 1

            # Skill usage (unweighted) - filter GK-only skills based on player position
            # For intercepts: GK is initiator (has GK skills), finisher is defender (outfield, should not have GK skills)
            event_type = f"{chance_type}_intercept"
            finisher_pos = ms.ps(atk_team, finisher).position
            goalkeeper_pos = ms.ps(def_team, goalkeeper).position
            finisher_is_gk = (finisher_pos == "GK")
            goalkeeper_is_gk = (goalkeeper_pos == "GK")
            
            finisher_skills = filter_skills_list_for_player(skills_used, finisher_is_gk)
            goalkeeper_skills = filter_skills_list_for_player(skills_used, goalkeeper_is_gk)
            
            ms.team[atk_team].skill_usage.add_usage(skills_used, event_type)
            ms.team[def_team].skill_usage.add_usage(skills_used, event_type)
            ms.ps(atk_team, finisher).skill_usage.add_usage(finisher_skills, event_type)
            ms.ps(def_team, goalkeeper).skill_usage.add_usage(goalkeeper_skills, event_type)
            
            # Weighted skill usage - filter GK-only skills based on player position
            skill_weights = EVENT_SKILL_WEIGHTS.get(event_type, {})
            if skill_weights:
                finisher_weights = filter_skills_for_player(skill_weights, finisher_is_gk)
                goalkeeper_weights = filter_skills_for_player(skill_weights, goalkeeper_is_gk)
                ms.team[atk_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.team[def_team].weighted_skill_usage.add_usage(skill_weights, event_type)
                ms.ps(atk_team, finisher).weighted_skill_usage.add_usage(finisher_weights, event_type)
                ms.ps(def_team, goalkeeper).weighted_skill_usage.add_usage(goalkeeper_weights, event_type)

    return ms
