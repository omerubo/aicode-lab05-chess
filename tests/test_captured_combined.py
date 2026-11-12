from copy import deepcopy

import pytest

from game import new_position
from session import Session


def play_all(session, moves):
    for source, target in moves:
        session.dispatch({"action": "move", "source": source, "target": target})


def test_undo_against_the_computer_removes_the_piece_it_captured_from_the_display():
    session = Session("computer")
    # Nb1-c3 hangs the knight; capturing it (Qa5xc3+) is the computer's only best reply.
    session.position = [{"e1": "wK", "b1": "wN", "h8": "bK", "a5": "bQ"}, "w"]
    session.after_move()
    before = deepcopy(session.view())
    play_all(session, [("b1", "c3")])
    replied = session.dispatch({"action": "computer-move"})
    assert replied["moves"] == ["b1-c3", "a5xc3+"]
    assert replied["captured"].count("wN") == before["captured"].count("wN") + 1

    view = session.dispatch({"action": "undo"})

    assert view["captured"] == before["captured"]
    assert view["board"] == before["board"]
    assert view["turn"] == "w"
    assert view["moves"] == []


def test_undo_back_to_the_start_after_several_captures_empties_the_display():
    session = Session()
    moves = [("e2", "e4"), ("d7", "d5"), ("e4", "d5"), ("d8", "d5"),
             ("b1", "c3"), ("d5", "a2"), ("a1", "a2")]
    play_all(session, moves)
    assert session.view()["captured"] == ["bP", "bQ", "wP", "wP"]

    for _ in moves:
        view = session.dispatch({"action": "undo"})

    assert view["captured"] == []
    assert session.position == new_position()
    assert view["moves"] == []


def test_undo_at_the_start_keeps_the_display_empty_and_changes_nothing():
    session = Session()
    before = deepcopy(session.view())

    view = session.dispatch({"action": "undo"})

    assert view["captured"] == []
    assert view == before


@pytest.mark.parametrize("bad", [None, {}, "not a game", {"version": 1}])
def test_failed_load_keeps_board_turn_and_captured_display(bad):
    session = Session()
    play_all(session, [("e2", "e4"), ("d7", "d5"), ("e4", "d5")])
    before = deepcopy(session.view())

    with pytest.raises(ValueError):
        session.dispatch({"action": "load", "data": bad})

    assert session.view() == before
    assert session.view()["captured"] == ["bP"]
    assert session.view()["turn"] == "b"
