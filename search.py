import chess
from evaluation import evaluate

transposition_table = {}


def move_ordering_score(board: chess.Board, move: chess.Move) -> int:
    score = 0

    if board.is_capture(move):
        score += 10

    if move.promotion:
        score += 20

    board.push(move)
    if board.is_check():
        score += 15
    board.pop()

    return score


def quiescence_search(board: chess.Board, alpha: float, beta: float) -> float:
    stand_pat = evaluate(board)

    if stand_pat >= beta:
        return beta

    if alpha < stand_pat:
        alpha = stand_pat

    capture_moves = sorted(
        [move for move in board.legal_moves if board.is_capture(move)],
        key=lambda move: move_ordering_score(board, move),
        reverse=True,
    )

    for move in capture_moves:
        board.push(move)
        score = -quiescence_search(board, -beta, -alpha)
        board.pop()

        if score >= beta:
            return beta

        if score > alpha:
            alpha = score

    return alpha


def minimax(
    board: chess.Board,
    depth: int,
    maximizing_player: bool,
    alpha: float,
    beta: float,
) -> float:
    if board.is_game_over():
        return evaluate(board)

    if depth == 0:
        return quiescence_search(board, alpha, beta)

    position_key = (board.fen(), depth, maximizing_player)
    if position_key in transposition_table:
        return transposition_table[position_key]

    legal_moves = sorted(
        board.legal_moves,
        key=lambda move: move_ordering_score(board, move),
        reverse=True,
    )

    if maximizing_player:
        best_score = float("-inf")
        for move in legal_moves:
            board.push(move)
            score = minimax(board, depth - 1, False, alpha, beta)
            board.pop()

            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break

        transposition_table[position_key] = best_score
        return best_score

    best_score = float("inf")
    for move in legal_moves:
        board.push(move)
        score = minimax(board, depth - 1, True, alpha, beta)
        board.pop()

        best_score = min(best_score, score)
        beta = min(beta, best_score)
        if beta <= alpha:
            break

    transposition_table[position_key] = best_score
    return best_score
