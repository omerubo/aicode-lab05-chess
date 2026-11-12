import json

from session import Session


def test_captured_display_survives_save_load_and_updates_after_undo():
    original = Session()
    for source, target in [("e2", "e4"), ("d7", "d5"), ("e4", "d5")]:
        original.play(source, target)
    loaded = Session()
    loaded.dispatch({"action": "load", "data": json.loads(json.dumps(original.save()))})

    assert loaded.view()["captured"] == ["bP"]
    view = loaded.dispatch({"action": "undo"})
    assert view["captured"] == []
    assert view["board"]["d5"] == "bP"
    assert view["board"]["e4"] == "wP"
    assert original.view()["captured"] == ["bP"]
    loaded.dispatch({"action": "new"})
    assert loaded.view()["captured"] == []


def test_save_after_undo_keeps_only_captures_in_the_current_continuation():
    session = Session()
    for source, target in [("e2", "e4"), ("d7", "d5"), ("e4", "d5"), ("d8", "d5")]:
        session.play(source, target)
    assert session.view()["captured"] == ["bP", "wP"]
    session.dispatch({"action": "undo"})
    assert session.view()["captured"] == ["bP"]

    loaded = Session()
    loaded.dispatch({"action": "load", "data": json.loads(json.dumps(session.save()))})
    assert loaded.view()["captured"] == ["bP"]
    loaded.dispatch({"action": "undo"})
    assert loaded.view()["captured"] == []
    assert loaded.notation == ["e2-e4", "d7-d5"]
