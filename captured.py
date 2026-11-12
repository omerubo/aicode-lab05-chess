"""Pieces for the captured-pieces sidebar."""
from collections import Counter
from itertools import pairwise

from game import other


def captured_pieces(positions):
    """Pieces captured across consecutive positions (oldest first), sorted.

    A move can only remove the opponent's pieces, so for each move count what the side not
    moving lost. A promotion only changes the mover's own pieces, so it never counts.
    """
    captured: list[str] = []
    for before, after in pairwise(positions):
        side = other(before[1])
        lost = (Counter(p for p in before[0].values() if p[0] == side)
                - Counter(p for p in after[0].values() if p[0] == side))
        captured.extend(lost.elements())
    return sorted(captured)
