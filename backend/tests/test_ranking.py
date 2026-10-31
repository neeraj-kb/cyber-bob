"""Unit tests for deterministic defense ranking, tie-breaking, and empty qualifier handling."""
from app.models import DefenseResult, DisruptionBreakdown
from app.ranking import rank_defenses


def create_dummy_defense(
    defense_id: str,
    confirmed_left: int,
    uncertain_left: int,
    disruption: int,
    effort: int,
) -> DefenseResult:
    return DefenseResult(
        defense_id=defense_id,
        name=f"Defense {defense_id}",
        type="block_link",
        target_id="target",
        removed_nodes=[],
        removed_edges=[],
        confirmed_paths_left=confirmed_left,
        uncertain_paths_left=uncertain_left,
        critical_assets_reachable=[] if confirmed_left == 0 else ["crit-1"],
        disruption=disruption,
        disruption_breakdown=DisruptionBreakdown(total_disruption=disruption),
        effort=effort,
        meets_target=False,
    )


def test_ranking_disqualifies_defenses_with_confirmed_paths():
    d1 = create_dummy_defense("def-1", confirmed_left=0, uncertain_left=0, disruption=5, effort=2)
    d2 = create_dummy_defense("def-2", confirmed_left=1, uncertain_left=0, disruption=1, effort=1)

    ranked = rank_defenses([d1, d2])

    # def-1 qualifies (0 confirmed paths left)
    assert ranked[0].defense_id == "def-1"
    assert ranked[0].meets_target is True
    assert ranked[0].rank == 1

    # def-2 disqualified because confirmed_paths_left > 0
    assert ranked[1].defense_id == "def-2"
    assert ranked[1].meets_target is False
    assert ranked[1].rank is None
    assert "Disqualified" in ranked[1].ranking_reason


def test_ranking_sorts_by_disruption_then_effort_then_id():
    # Both qualify (0 confirmed paths)
    # d1 has higher disruption (6) vs d2 (3) -> d2 ranks 1
    d1 = create_dummy_defense("def-b", confirmed_left=0, uncertain_left=0, disruption=6, effort=2)
    d2 = create_dummy_defense("def-a", confirmed_left=0, uncertain_left=1, disruption=3, effort=3)

    ranked = rank_defenses([d1, d2])

    assert ranked[0].defense_id == "def-a"
    assert ranked[0].rank == 1
    assert ranked[1].defense_id == "def-b"
    assert ranked[1].rank == 2


def test_ranking_tie_break_by_effort_then_id():
    # Same disruption (4), but d1 has effort 1 and d2 has effort 3
    d1 = create_dummy_defense("def-z", confirmed_left=0, uncertain_left=0, disruption=4, effort=1)
    d2 = create_dummy_defense("def-a", confirmed_left=0, uncertain_left=0, disruption=4, effort=3)

    ranked = rank_defenses([d1, d2])
    assert ranked[0].defense_id == "def-z"
    assert ranked[0].rank == 1
    assert ranked[1].defense_id == "def-a"
    assert ranked[1].rank == 2

    # Same disruption and effort: tie-break by defense_id
    d3 = create_dummy_defense("def-2", confirmed_left=0, uncertain_left=0, disruption=4, effort=1)
    ranked2 = rank_defenses([d1, d3])
    assert ranked2[0].defense_id == "def-2"
    assert ranked2[1].defense_id == "def-z"


def test_no_candidate_defense_qualifies():
    d1 = create_dummy_defense("def-1", confirmed_left=2, uncertain_left=0, disruption=2, effort=1)
    d2 = create_dummy_defense("def-2", confirmed_left=1, uncertain_left=1, disruption=5, effort=2)

    ranked = rank_defenses([d1, d2])

    for d in ranked:
        assert d.meets_target is False
        assert d.rank is None
        assert "human expert review" in d.ranking_reason.lower()

