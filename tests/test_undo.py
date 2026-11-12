from copy import deepcopy

import pytest

from game import new_position
from session import Session


def play_all(session, moves):
    for source, target in moves:
        session.dispatch({"action": "move", "source": source, "target": target})


def undo(session):
    return session.dispatch({"action": "undo"})


def test_single_undo_restores_previous_board_turn_and_notation():
    session = Session()
    play_all(session, [("e2", "e4")])
    after_first = deepcopy(session.position)
    play_all(session, [("d7", "d5")])

    view = undo(session)

    assert session.position == after_first
    assert view["board"] == after_first[0]
    assert view["turn"] == "b"
    assert view["moves"] == ["e2-e4"]
    assert "d5" not in view["board"]
    assert view["board"]["d7"] == "bP"
    assert len(session.history) == 1


def test_undo_of_a_capture_restores_the_captured_piece():
    session = Session()
    play_all(session, [("e2", "e4"), ("d7", "d5"), ("e4", "d5")])
    assert len(session.position[0]) == 31

    view = undo(session)

    assert view["board"]["d5"] == "bP"
    assert view["board"]["e4"] == "wP"
    assert len(view["board"]) == 32
    assert view["turn"] == "w"
    assert view["moves"] == ["e2-e4", "d7-d5"]


def test_repeated_undo_returns_exactly_to_the_starting_position():
    session = Session()
    moves = [("e2", "e4"), ("d7", "d5"), ("e4", "d5"), ("d8", "d5"), ("b1", "c3")]
    play_all(session, moves)

    for _ in moves:
        view = undo(session)

    assert session.position == new_position()
    assert view["board"] == new_position()[0]
    assert view["turn"] == "w"
    assert view["moves"] == []
    assert session.history == []


@pytest.mark.parametrize("opponent", ["human", "computer"])
def test_undo_at_the_start_does_nothing(opponent):
    session = Session(opponent)
    before = deepcopy(session.view())

    view = undo(session)
    view = undo(session)

    assert view == before
    assert session.position == new_position()
    assert session.history == []
    assert session.undone == []


def test_undo_after_moves_then_at_start_does_nothing_more():
    session = Session()
    play_all(session, [("e2", "e4")])
    undo(session)
    undone = deepcopy(session.undone)

    view = undo(session)

    assert view["board"] == new_position()[0]
    assert view["moves"] == []
    assert session.undone == undone


def test_undo_against_the_computer_reverses_its_reply_and_the_players_move():
    session = Session("computer")
    play_all(session, [("e2", "e4")])
    session.dispatch({"action": "computer-move"})
    assert len(session.notation) == 2

    view = undo(session)

    assert session.position == new_position()
    assert view["turn"] == "w"
    assert view["moves"] == []
    assert session.history == []


def test_undo_against_the_computer_before_it_replies_reverses_only_the_players_move():
    session = Session("computer")
    play_all(session, [("e2", "e4")])
    session.dispatch({"action": "computer-move"})
    after_round_one = deepcopy(session.snapshot())
    play_all(session, [("d2", "d4")])
    assert session.computer_to_move()

    view = undo(session)

    # Only d2-d4 is reversed; the earlier round (two moves) stays.
    assert session.snapshot() == after_round_one
    assert view["turn"] == "w"
    assert len(view["moves"]) == 2
    assert len(session.history) == 2


def test_undo_of_a_game_ending_player_move_against_the_computer_reverses_only_that_move():
    session = Session("computer")
    session.position = [{"g1": "wK", "a2": "wR", "g8": "bK", "b7": "bP",
                         "f7": "bP", "g7": "bP", "h7": "bP"}, "w"]
    # Earlier moves, played directly so the computer's random choice can't change them.
    session.play("a2", "a1")
    session.play("b7", "b6")
    before_mate = deepcopy(session.snapshot())
    play_all(session, [("a1", "a8")])
    assert session.view()["status"] == "checkmate"

    view = undo(session)

    assert session.snapshot() == before_mate
    assert view["turn"] == "w"
    assert view["status"] is None
    assert view["moves"] == ["a2-a1", "b7-b6"]


def test_undo_against_the_computer_steps_back_one_full_round_at_a_time():
    session = Session("computer")
    play_all(session, [("e2", "e4")])
    session.dispatch({"action": "computer-move"})
    after_round_one = deepcopy(session.snapshot())
    play_all(session, [("d2", "d4")])
    session.dispatch({"action": "computer-move"})

    undo(session)
    assert session.snapshot() == after_round_one
    assert session.position[1] == "w"
    assert len(session.notation) == 2

    undo(session)
    assert session.snapshot() == {"position": new_position(), "notation": []}


@pytest.mark.parametrize("opponent", ["human", "computer"])
def test_new_game_clears_the_undo_history(opponent):
    session = Session()
    play_all(session, [("e2", "e4"), ("e7", "e5"), ("g1", "f3")])
    undo(session)
    assert session.history and session.undone

    session.dispatch({"action": "new", "opponent": opponent})
    view = undo(session)

    assert session.history == []
    assert session.undone == []
    assert view["board"] == new_position()[0]
    assert view["moves"] == []
    assert view["opponent"] == opponent


def test_undo_of_a_pawn_reaching_the_last_rank_returns_a_pawn():
    session = Session()
    session.dispatch({"action": "promotion-setup"})
    play_all(session, [("b7", "a8")])

    view = undo(session)

    assert view["board"]["b7"] == "wP"
    assert view["board"]["a8"] == "bR"
    assert view["turn"] == "w"
    assert len(view["moves"]) == 8


def test_undo_keeps_the_undone_positions_for_a_later_redo():
    session = Session()
    play_all(session, [("e2", "e4")])
    after_first = deepcopy(session.snapshot())
    play_all(session, [("e7", "e5")])
    after_second = deepcopy(session.snapshot())

    undo(session)
    undo(session)

    assert session.undone == [after_second, after_first]
    # Stored snapshots are independent of the live game.
    play_all(session, [("d2", "d4")])
    assert session.undone == [after_second, after_first]


def test_play_continues_normally_after_undo():
    session = Session()
    play_all(session, [("e2", "e4"), ("e7", "e5")])
    undo(session)

    play_all(session, [("c7", "c5")])

    assert session.notation == ["e2-e4", "c7-c5"]
    assert session.position[0]["c5"] == "bP"
    assert "e5" not in session.position[0]
    assert len(session.history) == 2
    assert session.history[1]["notation"] == ["e2-e4"]
