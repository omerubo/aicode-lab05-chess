import json
from copy import deepcopy

import pytest

from game import new_position
from session import Session


def capture_game():
    session = Session()
    for source, target in [("e2", "e4"), ("d7", "d5"), ("e4", "d5")]:
        session.dispatch({"action": "move", "source": source, "target": target})
    return session


def test_file_loaded_in_fresh_game_can_undo_capture_and_all_earlier_moves(tmp_path):
    original = capture_game()
    path = tmp_path / "capture.save.json"
    path.write_text(json.dumps(original.dispatch({"action": "save"})), encoding="utf-8")
    loaded = Session()
    loaded.dispatch({"action": "load", "data": json.loads(path.read_text(encoding="utf-8"))})

    view = loaded.dispatch({"action": "undo"})

    assert view["board"]["d5"] == "bP"
    assert view["board"]["e4"] == "wP"
    assert len(view["board"]) == 32
    assert view["turn"] == "w"
    assert view["moves"] == ["e2-e4", "d7-d5"]
    assert len(loaded.history) == 2
    for _ in range(3):
        loaded.dispatch({"action": "undo"})
    assert loaded.position == new_position()
    assert loaded.history == []
    assert loaded.notation == []
    assert original.notation == ["e2-e4", "d7-d5", "e4xd5"]


def test_undo_save_load_continue_uses_only_the_current_continuation():
    original = capture_game()
    original.dispatch({"action": "undo"})
    original.dispatch({"action": "undo"})
    loaded = Session()
    loaded.dispatch({"action": "load", "data": json.loads(json.dumps(original.save()))})
    loaded.dispatch({"action": "move", "source": "c7", "target": "c5"})

    assert loaded.notation == ["e2-e4", "c7-c5"]
    assert loaded.history[-1]["notation"] == ["e2-e4"]
    assert loaded.position[0]["d7"] == "bP"
    loaded.dispatch({"action": "undo"})
    assert loaded.snapshot() == original.snapshot()
    loaded.dispatch({"action": "undo"})
    assert loaded.position == new_position()


@pytest.mark.parametrize("computer_has_replied", [False, True])
def test_loaded_computer_game_undo_returns_to_the_players_previous_turn(computer_has_replied):
    original = Session("computer")
    original.dispatch({"action": "move", "source": "e2", "target": "e4"})
    if computer_has_replied:
        original.dispatch({"action": "computer-move"})
    saved = original.save()
    loaded = Session()
    loaded.dispatch({"action": "load", "data": json.loads(json.dumps(saved))})

    view = loaded.dispatch({"action": "undo"})

    assert view["opponent"] == "computer"
    assert view["turn"] == "w"
    assert loaded.position == new_position()
    assert loaded.history == []
    assert loaded.notation == []
    assert original.save() == saved


def test_failed_load_preserves_the_ability_to_undo_a_capture():
    session = capture_game()
    before = deepcopy(session.save())
    invalid = deepcopy(before)
    invalid["history"] = []
    with pytest.raises(ValueError):
        session.dispatch({"action": "load", "data": invalid})

    assert session.save() == before
    session.dispatch({"action": "undo"})
    assert session.position[0]["d5"] == "bP"
    assert session.position[0]["e4"] == "wP"
    assert session.notation == ["e2-e4", "d7-d5"]
