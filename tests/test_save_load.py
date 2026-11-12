import json
from copy import deepcopy

import pytest

from game import new_position
from session import Session


def play_capture(session):
    session.play("e2", "e4")
    session.play("d7", "d5")
    session.play("e4", "d5")


@pytest.mark.parametrize("opponent", ["human", "computer"])
def test_save_to_file_and_load_in_fresh_session(tmp_path, opponent):
    original = Session(opponent)
    play_capture(original)
    path = tmp_path / "chess.save.json"
    path.write_text(json.dumps(original.dispatch({"action": "save"})), encoding="utf-8")

    loaded = Session()
    view = loaded.dispatch({"action": "load", "data": json.loads(path.read_text(encoding="utf-8"))})

    assert view == original.view()
    assert loaded.opponent == opponent
    assert loaded.position[1] == "b"
    assert loaded.position[0]["d5"] == "wP"
    assert len(loaded.position[0]) == 31
    assert loaded.notation == ["e2-e4", "d7-d5", "e4xd5"]
    assert loaded.history == original.history


def test_every_pre_move_snapshot_survives_loading_and_retains_captured_pieces():
    original = Session()
    expected = []
    for source, target in [("e2", "e4"), ("d7", "d5"), ("e4", "d5")]:
        expected.append({"position": deepcopy(original.position), "notation": original.notation.copy()})
        original.play(source, target)
    loaded = Session()
    loaded.load(json.loads(json.dumps(original.save())))

    assert loaded.history == expected
    assert loaded.history[0] == {"position": new_position(), "notation": []}
    before_capture = loaded.history[-1]
    assert before_capture["position"][0]["d5"] == "bP"
    assert before_capture["position"][0]["e4"] == "wP"
    assert before_capture["position"][1] == "w"
    assert before_capture["notation"] == ["e2-e4", "d7-d5"]


def test_loading_replaces_an_existing_game_and_its_history():
    source = Session("computer")
    source.play("d2", "d4")
    target = Session()
    play_capture(target)

    target.load(source.save())

    assert target.view() == source.view()
    assert len(target.history) == 1
    assert target.history[0]["position"] == new_position()


def test_saved_and_loaded_data_do_not_alias_the_game_or_its_history():
    original = Session()
    play_capture(original)
    before = original.save()
    saved = original.save()
    loaded = Session()
    loaded.load(saved)

    saved["position"][0].clear()
    saved["notation"].clear()
    saved["history"][0]["position"][0].clear()
    saved["history"][1]["notation"].append("changed")

    assert original.save() == before
    assert loaded.save() == before
    loaded.play("g8", "f6")
    assert original.save() == before


def test_illegal_move_does_not_add_an_undo_snapshot():
    session = Session()
    before = session.save()
    with pytest.raises(ValueError):
        session.play("e2", "e5")
    assert session.save() == before


def test_new_game_clears_loaded_history():
    session = Session("computer")
    play_capture(session)
    session.load(session.save())
    session.dispatch({"action": "new"})

    assert session.history == []
    assert session.notation == []
    assert session.position == new_position()
    assert session.opponent == "human"


def test_loaded_computer_game_can_continue_on_the_computers_turn():
    original = Session("computer")
    original.dispatch({"action": "move", "source": "e2", "target": "e4"})
    loaded = Session()
    loaded.load(original.save())

    assert loaded.computer_to_move()
    view = loaded.dispatch({"action": "computer-move"})
    assert view["turn"] == "w"
    assert len(view["moves"]) == 2
    assert loaded.history[-1]["position"] == original.position


def test_finished_game_keeps_its_status_after_loading():
    original = Session()
    for source, target in [("f2", "f3"), ("e7", "e5"), ("g2", "g4"), ("d8", "h4")]:
        original.play(source, target)
    loaded = Session()
    view = loaded.dispatch({"action": "load", "data": original.save()})

    assert view["status"] == "checkmate"
    assert view["winner"] == "Black"
    assert view["moves"][-1] == "d8-h4#"
    assert len(loaded.history) == 4


@pytest.mark.parametrize("data", [None, [], "not a game", {}, {"version": 1}])
def test_invalid_file_shape_does_not_replace_the_running_game(data):
    session = Session()
    play_capture(session)
    before = session.save()

    with pytest.raises(ValueError):
        session.dispatch({"action": "load", "data": data})
    assert session.save() == before


@pytest.mark.parametrize("field,value", [
    ("version", 2), ("version", True), ("opponent", "unknown"),
    ("position", []), ("position", [{}, "w"]),
    ("position", [{"a1": "wK", "h8": "bK", "z9": "wP"}, "w"]),
    ("position", [{"a1": "wK", "h8": "bK", "d4": "wDragon"}, "w"]),
    ("position", [{"a1": "wK", "h8": "bK"}, "x"]),
    ("notation", "e2-e4"), ("notation", [None]),
    ("history", None), ("history", []),
    ("history", [{}]),
    ("history", [{"position": new_position(), "notation": ["e2-e4"]}]),
])
def test_invalid_saved_fields_are_rejected_atomically(field, value):
    session = Session("computer")
    session.play("e2", "e4")
    before = session.save()
    invalid = deepcopy(before)
    invalid[field] = value

    with pytest.raises(ValueError):
        session.load(invalid)
    assert session.save() == before
