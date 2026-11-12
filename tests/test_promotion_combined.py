import json
from copy import deepcopy

from session import Session


def promote(session, source, target, piece):
    return session.dispatch(
        {"action": "move", "source": source, "target": target, "promotion": piece})


def test_undo_of_a_promotion_restores_pawn_rook_captured_turn_and_notation():
    session = Session()
    session.dispatch({"action": "promotion-setup"})
    before = deepcopy(session.view())
    promote(session, "b7", "a8", "Q")

    view = session.dispatch({"action": "undo"})

    assert view["board"]["b7"] == "wP"
    assert view["board"]["a8"] == "bR"
    assert view["captured"] == before["captured"] == ["bP", "wP"]
    assert view["turn"] == "w"
    assert view["moves"] == before["moves"]


def test_knight_promotion_survives_save_and_load_and_can_be_undone():
    original = Session()
    original.dispatch({"action": "promotion-setup"})
    promote(original, "b7", "a8", "N")
    loaded = Session()

    view = loaded.dispatch(
        {"action": "load", "data": json.loads(json.dumps(original.save()))})

    assert view["board"]["a8"] == "wN"
    assert "b7" not in view["board"]
    assert view["moves"][-1] == "b7xa8=N"
    assert view["captured"] == original.view()["captured"]
    undone = loaded.dispatch({"action": "undo"})
    assert undone["board"]["b7"] == "wP"
    assert undone["board"]["a8"] == "bR"


def test_captured_display_does_not_count_promoted_pawns_for_either_side():
    session = Session()
    session.dispatch({"action": "promotion-setup"})

    promote(session, "b7", "a8", "Q")
    assert session.view()["captured"] == ["bP", "bR", "wP"]

    promote(session, "g2", "h1", "Q")
    assert session.view()["board"]["h1"] == "bQ"
    assert session.view()["captured"] == ["bP", "bR", "wP", "wR"]


def test_captured_queen_still_shows_after_a_pawn_promotes_to_a_new_queen():
    session = Session()
    session.position = [{"e1": "wK", "d2": "wQ", "b7": "wP", "h8": "bK", "d8": "bR"}, "b"]
    session.play("d8", "d2")
    session.play("b7", "b8", "Q")

    assert session.position[0]["b8"] == "wQ"
    assert session.view()["captured"] == ["wQ"]


def test_computer_promotes_to_a_queen_and_undo_reverses_both_moves():
    session = Session("computer")
    session.position = [{"a8": "wK", "e8": "bK", "h2": "bP"}, "w"]
    session.after_move()
    start = deepcopy(session.position)
    session.dispatch({"action": "move", "source": "a8", "target": "a7"})

    replied = session.dispatch({"action": "computer-move"})

    assert replied["moves"][-1].startswith("h2-h1=Q")
    assert replied["board"]["h1"] == "bQ"
    assert replied["captured"] == []
    view = session.dispatch({"action": "undo"})
    assert session.position == start
    assert view["board"]["h2"] == "bP"
    assert view["turn"] == "w"
    assert view["moves"] == []
