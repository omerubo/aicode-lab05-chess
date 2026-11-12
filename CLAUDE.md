# Chess workshop (Lab 5)

Python chess variant served to the browser. Game rules in `game.py`, the computer opponent in
`computer.py`, application actions in `session.py`, save format in `savegame.py`, HTTP server in
`server.py`, UI in `static/`. Run the game with `.venv/bin/python server.py` (port 8000).

## Checks: run all of these before saying work is done

```sh
.venv/bin/python -m pip install -r requirements-dev.txt   # once, or after it changes
.venv/bin/python -m pytest -v                             # must be all green
.venv/bin/python -m pytest --cov --cov-report=term-missing
.venv/bin/ruff check
.venv/bin/ruff format --check
.venv/bin/mypy --strict .
```

- Report the real output. A failing test is reported (quote the failing assertion), not hidden.
- Baseline: the existing code is not ruff-formatted and has no type annotations, so
  `ruff format --check` and `mypy --strict` already fail on untouched files. Don't
  mass-reformat or annotate unrelated code; look for new findings in the code you changed.
  mypy errors other than `no-untyped-def` / `no-untyped-call` deserve a look.
- `server.py` and `static/app.js` have no automated tests; check them by playing the game.

## Design decisions

- **Shared history:** `Session.history` holds one snapshot per individual move (computer moves
  included), oldest first: `{"position": [board, turn], "notation": labels}` describing the
  game *before* that move. Only `Session.play()` records it. Illegal moves add nothing; a new
  game clears it. Save/load stores it, so undo works after loading.
- **Undo against the computer:** one undo reverses the computer's reply *and* the player's
  preceding move, returning to the player's turn. If the computer has not replied yet
  (including after a game-ending player move), undo reverses just the player's move. In a
  two-player game, undo reverses one move. Undo at the start does nothing.
- Undo restores snapshots directly (never replays moves) and then calls `after_move()` so
  derived sidebar data (captured pieces) is recomputed.
- `Session.undone` keeps the positions undo left, for a future redo. It is not yet cleared
  by a new move or by `load()`; redo must handle that.
- Promotion: a pawn reaching the last rank needs a choice of `Q`, `R`, `B` or `N`; notation
  gets `=Q` etc. Undo must bring back the pawn.

## Git workflow

- Remotes: `origin` = course repo (read-only), `team` = our shared repo. Push to `team` only.
- Each feature branch includes its own tests in a dedicated `tests/test_<feature>.py`.
- Never add `.DS_Store`. Don't commit, merge or push without being asked.
