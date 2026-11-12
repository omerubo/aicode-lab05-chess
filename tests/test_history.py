from copy import deepcopy

import pytest

from game import new_position
from session import Session


def test_history_records_independent_pre_move_board_turn_and_notation():
    session = Session()
    expected = []
    for source, target in [("e2", "e4"), ("d7", "d5"), ("e4", "d5")]:
        expected.append({"position": deepcopy(session.position), "notation": session.notation.copy()})
        session.play(source, target)

    assert session.history == expected
    assert session.history[0] == {"position": new_position(), "notation": []}
    before_capture = session.history[-1]
    assert before_capture["position"][0]["d5"] == "bP"
    assert before_capture["position"][0]["e4"] == "wP"
    assert before_capture["position"][1] == "w"
    assert before_capture["notation"] == ["e2-e4", "d7-d5"]
    assert session.position[0]["d5"] == "wP"
    assert session.position[1] == "b"
    assert session.notation == ["e2-e4", "d7-d5", "e4xd5"]


def test_snapshot_does_not_expose_mutable_live_state():
    session = Session()
    session.play("e2", "e4")
    snapshot = session.snapshot()
    snapshot["position"][0].clear()
    snapshot["notation"].append("changed")

    assert session.position[0]["e4"] == "wP"
    assert len(session.position[0]) == 32
    assert session.notation == ["e2-e4"]
    assert session.history[0]["position"] == new_position()
    assert session.history[0]["notation"] == []


def test_illegal_move_keeps_game_and_history_unchanged():
    session = Session()
    session.play("e2", "e4")
    before = session.snapshot()
    history = deepcopy(session.history)

    with pytest.raises(ValueError):
        session.play("e4", "e5")

    assert session.snapshot() == before
    assert session.history == history


@pytest.mark.parametrize("opponent", ["human", "computer"])
def test_new_game_clears_history(opponent):
    session = Session()
    session.play("e2", "e4")
    session.dispatch({"action": "new", "opponent": opponent})

    assert session.history == []
    assert session.snapshot() == {"position": new_position(), "notation": []}
    assert session.opponent == opponent


def test_player_and_computer_moves_each_record_one_snapshot():
    session = Session("computer")
    session.dispatch({"action": "move", "source": "e2", "target": "e4"})
    before_reply = session.snapshot()
    session.dispatch({"action": "computer-move"})

    assert len(session.history) == 2
    assert session.history[0] == {"position": new_position(), "notation": []}
    assert session.history[1] == before_reply
    assert session.history[1]["position"][1] == "b"
    assert session.position[1] == "w"


def test_promotion_setup_records_all_moves_without_aliasing_the_live_board():
    session = Session()
    session.dispatch({"action": "promotion-setup"})

    assert len(session.history) == 8
    assert session.history[-1]["position"][0]["h3"] == "bP"
    assert session.history[-1]["position"][0]["g2"] == "wP"
    assert session.position[0]["g2"] == "bP"
    assert len(session.history[-1]["notation"]) == 7
