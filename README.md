# Chess workshop

A local chess game in Python, for two players or against the computer. Requires Python 3.10
or later. Ask your coding agent to create `.venv` and install `requirements-dev.txt` in it.
Activate the environment in each terminal you use:

```sh
source .venv/bin/activate
```

```sh
python3 server.py
# Open http://127.0.0.1:8000
python -m pytest
```

Start a game against another person or against the computer. Against the computer you
play White; it looks one move ahead and plays the move that leaves it the most material,
preferring checkmate. Select a piece, then a highlighted destination. White moves first.
Standard movement, captures, check, checkmate and stalemate apply: you cannot leave your
own king in check, checkmate wins, and stalemate is a draw. Pawns initially remain pawns at
the far rank; a later branch adds promotion to a piece the player chooses. There is no clock.

**Not supported: castling and en passant.** Neither move exists in this game. The other
draw rules (insufficient material, threefold repetition, the fifty-move rule) are not
implemented either.

To reach promotion quickly from a new game, play a2-a4, h7-h5, a4-a5, h5-h4, a5-a6,
h4-h3, a6-b7, h3-g2. White can then play b7 to a8. In tests, the `promotion-setup` action
plays the same moves.

## Files

- `game.py`: board and turn in a position list; movement, check, checkmate and stalemate.
- `session.py`: game actions, the opponent, displayed move notation, and sidebar information.
- `computer.py`: the computer opponent.
- `savegame.py`: validation of the versioned JSON save format.
- `server.py`: one in-memory game, HTTP actions, and static files. Restarting loses the game.
- `static/`: browser presentation and square selection. All movement decisions run in Python.
- `tests/`: starter behavior checks.

## Shared game history

`Session.history` is a list of snapshots, oldest first, with one entry per successful
individual move, including each computer move. Each snapshot has the shape
`{"position": [board, turn], "notation": labels}` and describes the game **before**
that move. The board and notation are independent copies, created by `Session.snapshot()`.
`Session.play()` already records the snapshot; feature branches must not add it twice.
An illegal move adds no history, and a new game clears it.

Undo pops a snapshot, restores its `position` and `notation`, and calls
`after_move()` to refresh derived sidebar information. Restore snapshots directly,
without replaying moves through `play()`.

**Decision for undo against the computer:** one undo reverses the computer's reply
and the player's preceding move, returning to the player's turn. If the computer has
not replied yet (including a game-ending player move), reverse just the player's move.
In a two-player game, undo reverses one individual move. Undo at the beginning does nothing.

## Save and load

Click **Save game** to download `chess.save.json`. Click **Load game** and select the
file to resume it, including in a fresh server instance. Loading replaces the current
game and restores its board, turn, notation, opponent mode, and undo history. Invalid
files leave the current game unchanged. The browser accepts files up to 900 KB.
If a loaded game is waiting for the computer, the browser asks it to make its next move.

New game clears `history`. Save/load preserves all snapshots, so moves played before
saving remain available to undo after loading.

The save API is `{"action": "save"}`; the load API is
`{"action": "load", "data": saved_object}`. The current format version is `1`.

## Working together

Start your two branches from `main`. One partner implements save/load; the other implements
undo. Merge both into `main`, then merge the supplied `feature/captured-pieces` and
`feature/promotion` branches into `main` in that order. After each merge, run the existing
tests and try the combined game before asking your agent to repair anything. Add checks
for the behavior you establish. Implement redo together using the undo mechanism you created.

Save/load must restore the game in a fresh instance, including whether the opponent is a
person or the computer, and preserve enough information to undo moves made before saving.
Undo must restore captured pieces and the side to move; decide together what it does
against the computer. Undo at the beginning does nothing. Move notation should describe the
currently played continuation. New game clears the previous game.

The captured-pieces display shows pieces actually captured, with their type at capture.
Promotion alone is not a capture. Undoing a capture removes it from the display.

Redo restores the undone move, including capture and promotion; against the computer,
decide what it restores. A different move after undo discards redo. For this workshop,
save/load should also preserve the ability to redo.

Establish checks for interactions as you integrate features. Supplied branches are workshop
contributions to inspect and integrate, not a guarantee of correctness in every combination.
