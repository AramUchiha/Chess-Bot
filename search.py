import chess
from dataclasses import dataclass

from evaluation import MATE_SCORE, evaluate_white, side_relative_score, terminal_side_relative

FLAG_EXACT = 0
FLAG_LOWER = 1
FLAG_UPPER = 2


@dataclass
class TTEntry:
    depth: int
    score: float
    flag: int


transposition_table: dict[str, TTEntry] = {}


def tt_board_key(board: chess.Board) -> str:
    """Position identity for TT (board + side + castling + EP); omits clocks."""
    parts = board.fen().split()
    return " ".join(parts[:4])


def _is_mate_band(score: float) -> bool:
    return abs(score) > MATE_SCORE / 2


def tt_probe(key: str, depth: int, alpha: float, beta: float) -> float | None:
    entry = transposition_table.get(key)
    if entry is None or entry.depth < depth:
        return None
    if _is_mate_band(entry.score):
        return None
    if entry.flag == FLAG_EXACT:
        return entry.score
    if entry.flag == FLAG_LOWER and entry.score >= beta:
        return entry.score
    if entry.flag == FLAG_UPPER and entry.score <= alpha:
        return entry.score
    return None


def tt_store(key: str, depth: int, score: float, flag: int) -> None:
    old = transposition_table.get(key)
    if old is None or depth >= old.depth:
        transposition_table[key] = TTEntry(depth=depth, score=score, flag=flag)


def move_ordering_score(board: chess.Board, move: chess.Move) -> int:
    score = 0

    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)

        if victim and attacker:
            score += 10 * victim.piece_type - attacker.piece_type
        else:
            score += 10

    if move.promotion:
        score += 20
    return score


def ordered_legal_moves(board: chess.Board) -> list[chess.Move]:
    return sorted(
        board.legal_moves,
        key=lambda m: move_ordering_score(board, m),
        reverse=True,
    )


def quiescence_search(board: chess.Board, alpha: float, beta: float, ply: int) -> float:
    t = terminal_side_relative(board, ply)
    if t is not None:
        return t

    stand_pat = side_relative_score(board, evaluate_white(board))

    if stand_pat >= beta:
        return beta

    if alpha < stand_pat:
        alpha = stand_pat

    if board.is_check():
        moves = list(board.legal_moves)
    else:
        moves = [m for m in board.legal_moves if board.is_capture(m)]

    moves.sort(key=lambda m: move_ordering_score(board, m), reverse=True)

    for move in moves:
        board.push(move)
        score = -quiescence_search(board, -beta, -alpha, ply + 1)
        board.pop()

        if score >= beta:
            return beta

        if score > alpha:
            alpha = score

    return alpha


def negamax(board: chess.Board, depth: int, alpha: float, beta: float, ply: int = 0) -> float:
    t = terminal_side_relative(board, ply)
    if t is not None:
        return t

    key = tt_board_key(board)
    alpha_orig = alpha
    cached = tt_probe(key, depth, alpha, beta)
    if cached is not None:
        return cached

    if depth == 0:
        return quiescence_search(board, alpha, beta, ply)

    best = float("-inf")
    for move in ordered_legal_moves(board):
        board.push(move)
        score = -negamax(board, depth - 1, -beta, -alpha, ply + 1)
        board.pop()
        best = max(best, score)
        alpha = max(alpha, best)
        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = FLAG_UPPER
    elif best >= beta:
        flag = FLAG_LOWER
    else:
        flag = FLAG_EXACT

    if not _is_mate_band(best):
        tt_store(key, depth, best, flag)
    return best
