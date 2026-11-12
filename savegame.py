"""The versioned, JSON-compatible save format shared by save/load and undo."""

from copy import deepcopy

from game import coordinates

SAVE_VERSION = 1


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict) or set(snapshot) != {"position", "notation"}:
        raise ValueError("Invalid save file: expected a game snapshot")
    position = snapshot["position"]
    if not isinstance(position, list) or len(position) != 2:
        raise ValueError("Invalid save file: expected a board and turn")
    board, turn = position
    if not isinstance(board, dict) or turn not in ("w", "b"):
        raise ValueError("Invalid save file: invalid board or turn")
    for square, piece in board.items():
        coordinates(square)
        if not isinstance(piece, str) or piece not in (
            "wK", "wQ", "wR", "wB", "wN", "wP",
            "bK", "bQ", "bR", "bB", "bN", "bP",
        ):
            raise ValueError("Invalid save file: unknown chess piece")
    if list(board.values()).count("wK") != 1 or list(board.values()).count("bK") != 1:
        raise ValueError("Invalid save file: each side needs one king")
    notation = snapshot["notation"]
    if not isinstance(notation, list) or any(not isinstance(label, str) for label in notation):
        raise ValueError("Invalid save file: invalid move notation")


def validate_save(data):
    """Validate everything before the running game is replaced; return an owned copy."""
    fields = {"version", "opponent", "position", "notation", "history"}
    if not isinstance(data, dict) or set(data) != fields:
        raise ValueError("Invalid save file: missing or unknown fields")
    if type(data["version"]) is not int or data["version"] != SAVE_VERSION:
        raise ValueError("Unsupported save file version")
    if data["opponent"] not in ("human", "computer"):
        raise ValueError("Invalid save file: unknown opponent")
    validate_snapshot({"position": data["position"], "notation": data["notation"]})
    history = data["history"]
    if not isinstance(history, list) or len(history) != len(data["notation"]):
        raise ValueError("Invalid save file: incomplete undo history")
    for index, snapshot in enumerate(history):
        validate_snapshot(snapshot)
        if snapshot["notation"] != data["notation"][:index]:
            raise ValueError("Invalid save file: inconsistent undo history")
    return deepcopy(data)
