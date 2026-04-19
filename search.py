import chess
from evaluation import evaluate

transposition_table = {}


def move_ordering_score(board: chess.Board, move: chess.Move) -> int:
    score = 0

    # Captures (use MVV-LVA idea)
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)

        if victim and attacker:
            score += 10 * victim.piece_type - attacker.piece_type
        else:
            score += 10

    # Promotions
    if move.promotion:
        score += 20
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


def minimax(board: chess.Board, depth: int, alpha: float, beta: float) -> float:
    if board.is_game_over():
        return evaluate(board)

    if depth == 0:
        return quiescence_search(board, alpha, beta)

    position_key = (board.fen(), depth)
    if position_key in transposition_table:
        return transposition_table[position_key]

    legal_moves = sorted(
        board.legal_moves,
        key=lambda move: move_ordering_score(board, move),
        reverse=True,
    )
    best_score = float("-inf")
    for move in legal_moves:
        board.push(move)
        score = minimax(board, depth - 1, -beta, -alpha)
        board.pop()
        best_score = max(best_score, score)
        alpha = max(alpha, best_score)
        if beta <= alpha:
            break

    transposition_table[position_key] = best_score
    return best_score
