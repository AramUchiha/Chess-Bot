from __future__ import annotations

import random
import time
from dataclasses import dataclass

import chess

from search import negamax, ordered_legal_moves, transposition_table


@dataclass
class SearchLimits:
    """Search budget for a single move."""

    depth: int = 4
    time_sec: float | None = None


def choose_move(board: chess.Board, limits: SearchLimits) -> chess.Move:
    """Return a legal move for ``board.turn`` using negamax + alpha-beta.

    Clears the transposition table each call. If ``time_sec`` is set, performs
    iterative deepening from depth 1 up to ``limits.depth`` until the budget
    expires (always keeps the last fully completed iteration).
    """
    transposition_table.clear()

    legal = list(board.legal_moves)
    if not legal:
        raise ValueError("choose_move called with no legal moves")

    if len(legal) == 1:
        return legal[0]

    deadline = (
        time.monotonic() + limits.time_sec if limits.time_sec is not None else None
    )

    best_moves: list[chess.Move] = []
    max_depth = max(1, limits.depth)

    def run_depth(d: int) -> tuple[list[chess.Move], float]:
        transposition_table.clear()
        bm: list[chess.Move] = []
        bs = float("-inf")
        for move in ordered_legal_moves(board):
            board.push(move)
            score = -negamax(board, d - 1, float("-inf"), float("inf"))
            board.pop()
            if score > bs:
                bs = score
                bm = [move]
            elif score == bs:
                bm.append(move)
        return bm, bs

    for d in range(1, max_depth + 1):
        if deadline is not None and time.monotonic() >= deadline:
            break
        best_moves, _best_score = run_depth(d)
        if deadline is not None and time.monotonic() >= deadline:
            break

    assert best_moves
    return random.choice(best_moves)
