"""
Match simulator: runs minute-by-minute match simulation.
"""

import random
from typing import Dict, List
from .models import Team, Player
from .matrices import (
    weighted_choice,
    BASE_CREATOR_MATRIX,
    CREATOR_CHANCE_TYPE_MATRIX,
    BASE_CREATOR_DEFEND_MATRIX,
    BASE_FINISH_DEFEND_MATRIX,
    BASE_FINISHER_SHORT_PASS_MATRIX,
    BASE_FINISHER_CROSSING_MATRIX,
    BASE_FINISHER_THROUGH_MATRIX,
    BASE_FINISHER_LONG_PASS_MATRIX,
    CHANCE_TO_FINISH_TYPE_MATRIX,
    get_team_match_creator_matrix,
    build_match_finisher_matrix_weighted,
    build_match_defender_matrix_weighted,
    build_solo_dribble_matrix,
)
from .evaluation import eval_event


def get_players_by_position(team: Team, pos: str) -> List[Player]:
    """Get all players at a specific position."""
    return [p for p in team.players if p.matrix_position == pos]


def select_player_from_pos(team: Team, pos: str, exclude: Player = None) -> Player:
    """Select a random player from a position, optionally excluding one."""
    players = get_players_by_position(team, pos)
    if exclude is not None:
        players = [p for p in players if p != exclude]
    return random.choice(players) if players else None


class MatchSimulator:
    """Simulates a football match minute-by-minute."""
    
    def __init__(
        self,
        home_team: Team,
        away_team: Team,
        minutes: int = 90
    ):
        """
        Initialize match simulator with two teams.
        All matrices are built automatically from team formations.
        """
        self.home_team = home_team
        self.away_team = away_team
        self.minutes = minutes
        self.log = []
        
        # Build all matrices
        self._build_matrices()
    
    def _build_matrices(self):
        """Build all match-specific matrices from team formations."""
        # Creator matrices
        _, self.home_creator_matrix = get_team_match_creator_matrix(self.home_team, BASE_CREATOR_MATRIX)
        _, self.away_creator_matrix = get_team_match_creator_matrix(self.away_team, BASE_CREATOR_MATRIX)
        
        # Chance type matrices (same for both teams, based on position)
        self.home_chance_type_matrix = CREATOR_CHANCE_TYPE_MATRIX
        self.away_chance_type_matrix = CREATOR_CHANCE_TYPE_MATRIX
        
        # Finisher matrices by chance type
        self.home_finisher_matrices = {
            "Short": build_match_finisher_matrix_weighted(BASE_FINISHER_SHORT_PASS_MATRIX, self.home_team),
            "Crossing": build_match_finisher_matrix_weighted(BASE_FINISHER_CROSSING_MATRIX, self.home_team),
            "Through": build_match_finisher_matrix_weighted(BASE_FINISHER_THROUGH_MATRIX, self.home_team),
            "Long": build_match_finisher_matrix_weighted(BASE_FINISHER_LONG_PASS_MATRIX, self.home_team),
            "Solo": build_solo_dribble_matrix(self.home_team),
        }
        self.away_finisher_matrices = {
            "Short": build_match_finisher_matrix_weighted(BASE_FINISHER_SHORT_PASS_MATRIX, self.away_team),
            "Crossing": build_match_finisher_matrix_weighted(BASE_FINISHER_CROSSING_MATRIX, self.away_team),
            "Through": build_match_finisher_matrix_weighted(BASE_FINISHER_THROUGH_MATRIX, self.away_team),
            "Long": build_match_finisher_matrix_weighted(BASE_FINISHER_LONG_PASS_MATRIX, self.away_team),
            "Solo": build_solo_dribble_matrix(self.away_team),
        }
        
        # Defender matrices
        self.home_creator_vs_away_defend = build_match_defender_matrix_weighted(
            BASE_CREATOR_DEFEND_MATRIX, self.home_team, self.away_team
        )
        self.away_creator_vs_home_defend = build_match_defender_matrix_weighted(
            BASE_CREATOR_DEFEND_MATRIX, self.away_team, self.home_team
        )
        self.home_finish_vs_away_defend = build_match_defender_matrix_weighted(
            BASE_FINISH_DEFEND_MATRIX, self.home_team, self.away_team
        )
        self.away_finish_vs_home_defend = build_match_defender_matrix_weighted(
            BASE_FINISH_DEFEND_MATRIX, self.away_team, self.home_team
        )
        
        # Chance to finish type matrix (same for both)
        self.chance_to_finish_matrix = CHANCE_TO_FINISH_TYPE_MATRIX
    
    def decide_event(self) -> bool:
        """Decide if an event occurs this minute."""
        return random.random() < 0.5  # 50% chance per minute
    
    def handle_penalty(self, attacking_team: Team, defending_team: Team, minute: int):
        """Handle a penalty kick."""
        goalkeeper = defending_team.get_goalkeeper()
        # Exclude goalkeeper from penalty takers
        outfield_players = [p for p in attacking_team.players if p.matrix_position != "GK"]
        if not outfield_players:
            # Fallback: if somehow no outfield players, skip (shouldn't happen)
            return
        penalty_taker = random.choice(outfield_players)
        success, prob, X, crit_level, skills_used = eval_event("Penalty", penalty_taker, goalkeeper)
        self.log.append((
            minute, "special_result", "penalty",
            "goal" if success else "miss", f"{prob:.2f}",
            penalty_taker.name, goalkeeper.name, attacking_team.name, skills_used
        ))
    
    def handle_freekick(self, attacking_team: Team, defending_team: Team, minute: int):
        """Handle a free kick."""
        # Exclude goalkeeper from free kick takers
        outfield_players = [p for p in attacking_team.players if p.matrix_position != "GK"]
        if not outfield_players:
            # Fallback: if somehow no outfield players, skip (shouldn't happen)
            return
        free_kick_taker = random.choice(outfield_players)
        goalkeeper = defending_team.get_goalkeeper()
        success, prob, X, crit_level, skills_used = eval_event("Freekick", free_kick_taker, goalkeeper)
        self.log.append((
            minute, "special_result", "free_kick",
            "goal" if success else "saved", f"{prob:.2f}",
            free_kick_taker.name, goalkeeper.name, attacking_team.name, skills_used
        ))
    
    def _handle_counter_attack(
        self, 
        minute: int, 
        counter_creator: Player,  # The defender who becomes the creator
        original_creator: Player,  # The original creator (for reference/exclusion)
        original_attacking_team: Team,
        original_defending_team: Team,
        original_is_home: bool
    ) -> bool:
        """
        Handle a counter attack triggered after a failed event.
        
        Args:
            minute: Current minute
            counter_creator: Player initiating the counter (the defender from the failed event)
            original_creator: Original creator from the failed event (for exclusion if needed)
            original_attacking_team: The team that just failed the attack
            original_defending_team: The team that is now counter attacking
            original_is_home: Whether the original attacking team was home
        
        Returns:
            True if counter attack was handled, False otherwise
        """
        # Swap teams: the defending team becomes the attacking team
        counter_attacking_team = original_defending_team
        counter_defending_team = original_attacking_team
        counter_is_home = not original_is_home
        
        counter_creator_pos = counter_creator.matrix_position
        
        # Randomly select counter chance type from ["Through", "Long", "Solo"]
        counter_chance_type = random.choice(["Through", "Long", "Solo"])
        
        # --- COUNTER CREATION DEFENDER SELECTION ---
        defend_matrix = self.home_creator_vs_away_defend if counter_is_home else self.away_creator_vs_home_defend
        defend_probs = defend_matrix.get(counter_creator_pos, {})
        if not defend_probs:
            possible_positions = set(p.matrix_position for p in counter_defending_team.players)
            defender_pos = random.choice(list(possible_positions))
        else:
            defender_pos = weighted_choice(defend_probs)
            if defender_pos is None:
                possible_positions = set(p.matrix_position for p in counter_defending_team.players)
                defender_pos = random.choice(list(possible_positions))
        
        counter_defender = select_player_from_pos(counter_defending_team, defender_pos)
        if counter_defender is None:
            counter_defender = random.choice(counter_defending_team.players)
        
        # --- EVALUATE COUNTER CREATION ---
        # Use the selected counter chance type (Through, Long, or Solo) for evaluation
        success, prob, X, crit_level, skills_used = eval_event(
            counter_chance_type, counter_creator, counter_defender
        )
        creation_success = success
        critical_success = (crit_level == "crit_2")
        self.log.append((
            minute, "result", "creation",
            "success" if creation_success else "fail",
            f"{prob:.3f}", critical_success,
            counter_creator.name, counter_defender.name, counter_chance_type, counter_attacking_team.name, skills_used
        ))
        
        if not creation_success:
            return True  # Counter creation failed, but counter was attempted
        
        # --- COUNTER FINISHER SELECTION ---
        finisher_matrix = self.home_finisher_matrices[counter_chance_type] if counter_is_home else self.away_finisher_matrices[counter_chance_type]
        possible_finishers = dict(finisher_matrix.get(counter_creator_pos, {}))
        if counter_chance_type == "Solo":
            finisher = counter_creator
            finisher_pos = counter_creator_pos
        else:
            candidate_positions = [pos for pos in possible_finishers if pos != counter_creator_pos]
            if not candidate_positions:
                candidate_positions = list(possible_finishers.keys())
            attempts = 0
            while True:
                if not candidate_positions:
                    candidate_positions = list(possible_finishers.keys())
                finisher_pos = weighted_choice({k: possible_finishers[k] for k in candidate_positions})
                if finisher_pos is None:
                    finisher_pos = random.choice(list(possible_finishers.keys()))
                finisher = select_player_from_pos(counter_attacking_team, finisher_pos, exclude=counter_creator)
                if finisher is not None:
                    break
                attempts += 1
                if attempts > 10:
                    finisher = counter_creator
                    finisher_pos = counter_creator_pos
                    break
        
        # --- COUNTER FINISH DEFENDER SELECTION ---
        fin_defend_matrix = self.home_finish_vs_away_defend if counter_is_home else self.away_finish_vs_home_defend
        defend_probs_fin = dict(fin_defend_matrix.get(finisher_pos, {}))
        adjusted_probs = defend_probs_fin.copy()
        
        num_in_pos = len(get_players_by_position(counter_defending_team, defender_pos))
        if defender_pos in adjusted_probs and num_in_pos == 1:
            adjusted_probs[defender_pos] = 0
        
        total = sum(adjusted_probs.values())
        if total > 0:
            adjusted_probs = {k: v / total for k, v in adjusted_probs.items()}
        else:
            all_positions = set(p.matrix_position for p in counter_defending_team.players)
            adjusted_probs = {p: 1/len(all_positions) for p in all_positions}
        
        attempts = 0
        while True:
            finish_defender_pos = weighted_choice(adjusted_probs)
            if finish_defender_pos is None:
                finish_defender_pos = random.choice(list(adjusted_probs.keys()))
            finish_defender = select_player_from_pos(
                counter_defending_team, finish_defender_pos,
                exclude=counter_defender if num_in_pos == 1 and finish_defender_pos == defender_pos else None
            )
            if finish_defender is not None:
                break
            attempts += 1
            if attempts > 10:
                finish_defender = random.choice(counter_defending_team.players)
                finish_defender_pos = finish_defender.matrix_position
                break
        
        # --- FINISH TYPE SELECTION ---
        finish_type_probs = self.chance_to_finish_matrix[counter_chance_type]
        finish_type = weighted_choice(finish_type_probs)
        if finish_type is None:
            finish_type = random.choice(list(finish_type_probs.keys()))
        
        # --- GOALKEEPER INTERCEPTION CHECK ---
        if counter_chance_type in ["Long", "Through", "Crossing"]:
            goalkeeper = counter_defending_team.get_goalkeeper()
            intercepted, intercept_prob, X_intercept, crit_level_int, skills_used = eval_event(
                f"{counter_chance_type}_intercept", goalkeeper, finisher
            )
            self.log.append((
                minute, "result", "goalkeeper_intercept",
                "success" if intercepted else "fail",
                f"{intercept_prob:.2f}",
                finisher.name, goalkeeper.name,
                counter_chance_type, counter_attacking_team.name, skills_used
            ))
            if intercepted:
                return True  # Counter intercepted, counter ended
        
        # --- EVALUATE COUNTER FINISH ---
        x_bonus = 1.0 if (crit_level == "crit_2") else 0.0
        finish_success, finish_prob, finish_X, crit_level_finish, skills_used = eval_event(
            f"{counter_chance_type}_finisher", finisher, finish_defender, x_bonus=x_bonus
        )
        self.log.append((
            minute, "result", "finish",
            "success" if finish_success else "fail",
            f"{finish_prob:.3f}", crit_level_finish,
            finisher.name, finish_defender.name, finish_type, counter_attacking_team.name, skills_used
        ))
        
        if not finish_success:
            return True  # Counter finisher failed, but counter was attempted
        
        # Determine shot quality modifier based on critical level
        if crit_level_finish == "crit_2":
            shot_x_bonus = 1.0
        elif crit_level_finish == "crit_1":
            shot_x_bonus = 0.5
        else:
            shot_x_bonus = 0.0
        
        # --- EVALUATE SHOT QUALITY ---
        shot_on_target, shot_quality_prob, X_quality, crit_level_quality, skills_used = eval_event(
            finish_type, finisher, finish_defender, x_bonus=shot_x_bonus
        )
        self.log.append((
            minute, "result", "shot_quality",
            "on_target" if shot_on_target else "off_target",
            f"{shot_quality_prob:.2f}",
            finisher.name, finish_defender.name,
            finish_type, counter_attacking_team.name, skills_used
        ))
        
        # --- KEEPER SAVE OR GOAL ---
        if shot_on_target:
            goalkeeper = counter_defending_team.get_goalkeeper()
            saved, save_prob, X_save, crit_level_save, skills_used = eval_event(
                f"{finish_type}_save", goalkeeper, finisher
            )
            self.log.append((
                minute, "result", "save",
                "saved" if saved else "goal",
                f"{save_prob:.2f}",
                finisher.name, goalkeeper.name,
                finish_type, counter_attacking_team.name, skills_used
            ))
            
            # Corner from saved shots
            if saved and random.random() < 0.3:
                self.log.append((minute, "special", "corner_kick", counter_attacking_team.name))
                self.handle_corner(counter_attacking_team, counter_defending_team, minute)
        else:
            self.log.append((
                minute, "result", "finish_outcome", "miss",
                f"{shot_quality_prob:.2f}",
                finisher.name, finish_defender.name,
                finish_type, counter_attacking_team.name, skills_used
            ))
        
        return True  # Counter attack fully handled
    
    def handle_corner(self, attacking_team: Team, defending_team: Team, minute: int):
        """Handle a corner kick sequence."""
        # Select corner taker (creator)
        if hasattr(attacking_team, "corner_taker") and attacking_team.corner_taker in attacking_team.players:
            creator = attacking_team.corner_taker
        else:
            creator = random.choice(attacking_team.players)
        creator_pos = creator.matrix_position
        
        # Pick creation defender
        defend_matrix = self.home_creator_vs_away_defend if attacking_team == self.home_team else self.away_creator_vs_home_defend
        defend_probs = defend_matrix.get(creator_pos, {})
        if not defend_probs:
            present = {p.matrix_position for p in defending_team.players}
            defend_probs = {pos: 1/len(present) for pos in present}
        defender_pos = weighted_choice(defend_probs) or random.choice(list(defend_probs.keys()))
        defender = select_player_from_pos(defending_team, defender_pos) or random.choice(defending_team.players)
        
        # Evaluate corner delivery
        chance_type = "Corner"
        success, prob, X, crit_level, skills_used = eval_event(chance_type, creator, defender)
        crit_s = (crit_level == "crit_2")
        self.log.append((
            minute, "corner", "creation",
            "success" if success else "fail",
            f"{prob:.3f}", crit_s,
            creator.name, defender.name, chance_type, attacking_team.name, skills_used
        ))
        if not success:
            return
        
        # Build top-5 aerial candidates
        def top5_aerial(players, exclude=None):
            pool = [p for p in players if p is not exclude]
            pool.sort(key=lambda p: p.get_attr("Heading") + p.get_attr("Jump Reach"), reverse=True)
            return pool[:5] if len(pool) >= 5 else pool
        
        # Finisher: random from attackers' top-5
        top_attack = top5_aerial(attacking_team.players, exclude=creator)
        if not top_attack:
            return
        finisher = random.choice(top_attack)
        finisher_pos = finisher.matrix_position
        
        # Finish defender: random from defenders' top-5
        top_defend = top5_aerial(defending_team.players, exclude=None)
        if not top_defend:
            top_defend = defending_team.players[:]
        finish_defender = random.choice(top_defend)
        finish_defender_pos = finish_defender.matrix_position
        
        # Duel for the header
        finish_type = "Header"
        # Apply +1 bonus if corner creation had critical success (crit_2)
        x_bonus = 1.0 if crit_s else 0.0
        success, prob, X, crit_level_duel, skills_used = eval_event(f"{finish_type}_duel", finisher, finish_defender, x_bonus=x_bonus)
        crit_s_duel = (crit_level_duel == "crit_2")
        self.log.append((
            minute, "corner", "finish",
            "success" if success else "fail",
            f"{prob:.3f}", crit_s_duel,
            finisher.name, finish_defender.name, finish_type, attacking_team.name, skills_used
        ))
        if not success:
            return
        
        # Shot quality
        shot_on_target, shot_quality_prob, X_quality, crit_level_quality, skills_used = eval_event(
            finish_type, finisher, finish_defender
        )
        self.log.append((
            minute, "corner", "shot_quality",
            "on_target" if shot_on_target else "off_target",
            f"{shot_quality_prob:.2f}",
            finisher.name, finish_defender.name, finish_type, attacking_team.name, skills_used
        ))
        
        # Keeper save if on target
        if shot_on_target:
            goalkeeper = defending_team.get_goalkeeper()
            # Save evaluation from goalkeeper's perspective: goalkeeper as initiator, finisher as defender
            saved, save_prob, X_save, crit_level_save, skills_used = eval_event(
                f"{finish_type}_save", goalkeeper, finisher
            )
            self.log.append((
                minute, "corner", "save",
                "saved" if saved else "goal",
                f"{save_prob:.2f}",
                finisher.name, goalkeeper.name, finish_type, attacking_team.name, skills_used
            ))
        else:
            self.log.append((
                minute, "corner", "finish_outcome", "miss",
                f"{shot_quality_prob:.2f}",
                finisher.name, finish_defender.name, finish_type, attacking_team.name, skills_used
            ))
    
    def run(self):
        """Run the match simulation minute-by-minute."""
        for minute in range(1, self.minutes + 1):
            if not self.decide_event():
                continue
            
            # Select attacking team
            team = self.home_team if random.random() < 0.5 else self.away_team
            is_home = (team == self.home_team)
            opponent_team = self.away_team if is_home else self.home_team
            
            # --- CREATOR SELECTION ---
            creator_matrix = self.home_creator_matrix if is_home else self.away_creator_matrix
            creator_pos = weighted_choice(creator_matrix)
            if creator_pos is None:
                continue
            creator = select_player_from_pos(team, creator_pos)
            if creator is None:
                continue
            
            # --- CREATION DEFENDER SELECTION ---
            defend_matrix = self.home_creator_vs_away_defend if is_home else self.away_creator_vs_home_defend
            defend_probs = defend_matrix.get(creator_pos, {})
            defender_pos = weighted_choice(defend_probs)
            if defender_pos is None:
                possible_positions = set(p.matrix_position for p in opponent_team.players)
                defender_pos = random.choice(list(possible_positions))
            defender = select_player_from_pos(opponent_team, defender_pos)
            if defender is None:
                defender = random.choice(opponent_team.players)
            
            # --- CHANCE TYPE SELECTION ---
            chance_type_matrix = self.home_chance_type_matrix if is_home else self.away_chance_type_matrix
            if creator_pos not in chance_type_matrix:
                continue
            chance_type = weighted_choice(chance_type_matrix[creator_pos])
            if chance_type is None:
                continue
            
            # --- EVALUATE CREATION ---
            success, prob, X, crit_level, skills_used = eval_event(
                chance_type, creator, defender
            )
            creation_success = success
            # For creation, we only care about crit_2 level (critical success)
            critical_success = (crit_level == "crit_2")
            self.log.append((
                minute, "result", "creation",
                "success" if creation_success else "fail",
                f"{prob:.3f}", critical_success,
                creator.name, defender.name, chance_type, team.name, skills_used
            ))
            
            if not creation_success:
                # Check for counter attack after creation failure
                if random.random() < 0.15:  # 15% chance for counter after creation failure
                    self.log.append((minute, "special", "counter_attack", defender.name, "after_creation_fail"))
                    if self._handle_counter_attack(minute, defender, creator, team, opponent_team, is_home):
                        continue  # Counter attack handled, move to next minute
                continue  # Creation failed, move to next minute
            
            # Check for special events during creation
            if random.random() < 0.01:  # 1% chance penalty
                self.log.append((minute, "special", "penalty_awarded", team.name, "during_creation"))
                self.handle_penalty(team, opponent_team, minute)
                continue
            elif random.random() < 0.02:  # 2% chance free kick
                self.log.append((minute, "special", "free_kick_awarded", team.name, "during_creation"))
                self.handle_freekick(team, opponent_team, minute)
                continue
            
            # --- FINISHER SELECTION ---
            finisher_matrix = self.home_finisher_matrices[chance_type] if is_home else self.away_finisher_matrices[chance_type]
            possible_finishers = dict(finisher_matrix.get(creator_pos, {}))
            if chance_type == "Solo":
                finisher = creator
                finisher_pos = creator_pos
            else:
                candidate_positions = [pos for pos in possible_finishers if pos != creator_pos]
                if not candidate_positions:
                    candidate_positions = list(possible_finishers.keys())
                attempts = 0
                while True:
                    if not candidate_positions:
                        candidate_positions = list(possible_finishers.keys())
                    finisher_pos = weighted_choice({k: possible_finishers[k] for k in candidate_positions})
                    if finisher_pos is None:
                        finisher_pos = random.choice(list(possible_finishers.keys()))
                    finisher = select_player_from_pos(team, finisher_pos, exclude=creator)
                    if finisher is not None:
                        break
                    attempts += 1
                    if attempts > 10:
                        finisher = creator
                        finisher_pos = creator_pos
                        break
            
            # Check for special events during finishing
            if random.random() < 0.005:  # 0.5% penalty chance
                self.log.append((minute, "special", "penalty_awarded", team.name, "during_finish"))
                self.handle_penalty(team, opponent_team, minute)
                continue
            elif random.random() < 0.015:  # 1.5% free kick chance
                self.log.append((minute, "special", "free_kick_awarded", team.name, "during_finish"))
                self.handle_freekick(team, opponent_team, minute)
                continue
            
            # --- DEFEND FINISH SELECTION ---
            fin_defend_matrix = self.home_finish_vs_away_defend if is_home else self.away_finish_vs_home_defend
            defend_probs_fin = dict(fin_defend_matrix.get(finisher_pos, {}))
            adjusted_probs = defend_probs_fin.copy()
            
            num_in_pos = len(get_players_by_position(opponent_team, defender_pos))
            if defender_pos in adjusted_probs and num_in_pos == 1:
                adjusted_probs[defender_pos] = 0
            
            total = sum(adjusted_probs.values())
            if total > 0:
                adjusted_probs = {k: v / total for k, v in adjusted_probs.items()}
            else:
                all_positions = set(p.matrix_position for p in opponent_team.players)
                adjusted_probs = {p: 1/len(all_positions) for p in all_positions}
            
            attempts = 0
            while True:
                finish_defender_pos = weighted_choice(adjusted_probs)
                if finish_defender_pos is None:
                    finish_defender_pos = random.choice(list(adjusted_probs.keys()))
                finish_defender = select_player_from_pos(
                    opponent_team, finish_defender_pos,
                    exclude=defender if num_in_pos == 1 and finish_defender_pos == defender_pos else None
                )
                if finish_defender is not None:
                    break
                attempts += 1
                if attempts > 10:
                    finish_defender = random.choice(opponent_team.players)
                    finish_defender_pos = finish_defender.matrix_position
                    break
            
            # --- FINISH TYPE SELECTION ---
            finish_type_probs = self.chance_to_finish_matrix[chance_type]
            finish_type = weighted_choice(finish_type_probs)
            if finish_type is None:
                finish_type = random.choice(list(finish_type_probs.keys()))
            
            # --- GOALKEEPER INTERCEPTION CHECK ---
            if chance_type in ["Long", "Through", "Crossing"]:
                goalkeeper = opponent_team.get_goalkeeper()
                # Intercept evaluation from goalkeeper's perspective: goalkeeper as initiator, finisher as defender
                intercepted, intercept_prob, X_intercept, crit_level_int, skills_used = eval_event(
                    f"{chance_type}_intercept", goalkeeper, finisher
                )
                self.log.append((
                    minute, "result", "goalkeeper_intercept",
                    "success" if intercepted else "fail",
                    f"{intercept_prob:.2f}",
                    finisher.name, goalkeeper.name,
                    chance_type, team.name, skills_used
                ))
                if intercepted:
                    continue
            
            # --- EVALUATE FINISH ---
            # Apply +1 bonus if chance creation had critical success (crit_2 level)
            x_bonus = 1.0 if (crit_level == "crit_2") else 0.0
            finish_success, finish_prob, finish_X, crit_level_finish, skills_used = eval_event(
                f"{chance_type}_finisher", finisher, finish_defender, x_bonus=x_bonus
            )
            self.log.append((
                minute, "result", "finish",
                "success" if finish_success else "fail",
                f"{finish_prob:.3f}", crit_level_finish,
                finisher.name, finish_defender.name, finish_type, team.name, skills_used
            ))
            
            if not finish_success:
                # Check for counter attack after finisher failure
                if random.random() < 0.20:  # 20% chance for counter after finisher failure
                    self.log.append((minute, "special", "counter_attack", finish_defender.name, "after_finisher_fail"))
                    if self._handle_counter_attack(minute, finish_defender, finisher, team, opponent_team, is_home):
                        continue  # Counter attack handled, move to next minute
                continue  # Finisher failed, no shot
            
            # Determine shot quality modifier based on critical level
            # crit_2 = best situation = larger bonus = no pressure on shooter
            # crit_1 = good situation = smaller bonus = moderate pressure on shooter
            if crit_level_finish == "crit_2":
                shot_x_bonus = 1.0
            elif crit_level_finish == "crit_1":
                shot_x_bonus = 0.5
            else:  # "none" - no bonus
                shot_x_bonus = 0.0
            
            # --- EVALUATE SHOT QUALITY ---
            shot_on_target, shot_quality_prob, X_quality, crit_level_quality, skills_used = eval_event(
                finish_type, finisher, finish_defender, x_bonus=shot_x_bonus
            )
            self.log.append((
                minute, "result", "shot_quality",
                "on_target" if shot_on_target else "off_target",
                f"{shot_quality_prob:.2f}",
                finisher.name, finish_defender.name,
                finish_type, team.name, skills_used
            ))
            
            # --- KEEPER SAVE OR GOAL ---
            if shot_on_target:
                goalkeeper = opponent_team.get_goalkeeper()
                # Save evaluation from goalkeeper's perspective: goalkeeper as initiator, finisher as defender
                saved, save_prob, X_save, crit_level_save, skills_used = eval_event(
                    f"{finish_type}_save", goalkeeper, finisher
                )
                self.log.append((
                    minute, "result", "save",
                    "saved" if saved else "goal",
                    f"{save_prob:.2f}",
                    finisher.name, goalkeeper.name,
                    finish_type, team.name, skills_used
                ))
                
                # Corner from saved shots
                if saved and random.random() < 0.3:
                    self.log.append((minute, "special", "corner_kick", team.name))
                    self.handle_corner(team, opponent_team, minute)
            else:
                self.log.append((
                    minute, "result", "finish_outcome", "miss",
                    f"{shot_quality_prob:.2f}",
                    finisher.name, finish_defender.name,
                    finish_type, team.name, skills_used
                ))


def simulate_match(home_team: Team, away_team: Team, minutes: int = 90) -> MatchSimulator:
    """
    Convenience function to simulate a match.
    
    Returns:
        MatchSimulator instance with completed match log
    """
    sim = MatchSimulator(home_team, away_team, minutes)
    sim.run()
    return sim
