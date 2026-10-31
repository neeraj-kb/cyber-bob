"""Deterministic ranking decision engine."""
from typing import List
from app.models import DefenseResult


def rank_defenses(candidate_defenses: List[DefenseResult]) -> List[DefenseResult]:
    """
    Apply deterministic ranking rules with zero hidden weights:
    
    1. Qualification Gate:
       - A defense qualifies iff confirmed_paths_left == 0.
       - If confirmed_paths_left > 0, meets_target = False and disqualified.
       
    2. Ranking among qualifying defenses:
       - Primary: lowest disruption
       - Secondary: lowest effort
       - Tertiary: defense_id (alphabetical stable tie-break)
       
    3. Uncertainty Flagging:
       - Flag defenses leaving uncertain paths for mandatory human triage.
       
    4. No Qualifier Handling:
       - If no defense qualifies, return meets_target=False on all,
         rank=None, and explicit recommendations to apply compensating controls.
    """
    qualifying: List[DefenseResult] = []
    disqualified: List[DefenseResult] = []

    for defense in candidate_defenses:
        if defense.confirmed_paths_left == 0:
            defense.meets_target = True
            qualifying.append(defense)
        else:
            defense.meets_target = False
            defense.rank = None
            defense.ranking_reason = (
                f"Disqualified: leaves {defense.confirmed_paths_left} confirmed attack path(s) "
                f"to critical asset(s) ({', '.join(defense.critical_assets_reachable) or 'none'})."
            )
            disqualified.append(defense)

    if qualifying:
        # Sort qualifying: lowest disruption asc, lowest effort asc, defense_id asc
        qualifying.sort(key=lambda d: (d.disruption, d.effort, d.defense_id))
        
        for rank_idx, defense in enumerate(qualifying, start=1):
            defense.rank = rank_idx
            
            reasons = [
                f"Meets target with 0 confirmed paths to critical assets.",
                f"Disruption score: {defense.disruption}.",
                f"Effort score: {defense.effort}."
            ]
            if defense.uncertain_paths_left > 0:
                reasons.append(
                    f"FLAGGED FOR REVIEW: Leaves {defense.uncertain_paths_left} uncertain attack path(s) active."
                )
            if rank_idx == 1:
                reasons.insert(0, "RECOMMENDED: Lowest business disruption among qualifying defenses.")
            
            defense.ranking_reason = " ".join(reasons)
    else:
        # No defense qualified
        for defense in disqualified:
            defense.ranking_reason += " No candidate defense qualified; human expert review and custom controls required."

    # Return qualifying first in rank order, then disqualified sorted by disruption
    disqualified.sort(key=lambda d: (d.confirmed_paths_left, d.disruption, d.effort, d.defense_id))
    return qualifying + disqualified

