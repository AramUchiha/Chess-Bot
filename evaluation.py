import chess

piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}

# Used by search for terminal nodes; must dominate material scale.
MATE_SCORE = 10_000.0


def evaluate_white(board: chess.Board) -> float:
    """Static evaluation: positive favors White (always White-centric)."""
    score = 0.0

    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    for square in center_squares:
        piece = board.piece_at(square)
        if piece:
            if piece.color == chess.WHITE:
                score += 0.5
            else:
                score -= 0.5

    if board.is_check():
        if board.turn == chess.WHITE:
            score -= 0.5
        else:
            score += 0.5
    if board.is_checkmate():
        if board.turn == chess.WHITE:
            score -= 20
        else:
            score += 20

    for piece_type, value in piece_values.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

    return score


def evaluate(board: chess.Board) -> float:
    """Alias for backward compatibility."""
    return evaluate_white(board)


def side_relative_score(board: chess.Board, white_score: float) -> float:
    """Convert White-centric score to side-to-move perspective (for negamax)."""
    return white_score if board.turn == chess.WHITE else -white_score


def terminal_side_relative(board: chess.Board, ply: int = 0) -> float | None:
    """If the game is over, return score from the side to move; else None.

    Checkmate score is adjusted by ``ply`` (distance from search root) so that
    shorter mates score better than distant mates without colliding with the
    static evaluation scale.
    """
    if board.is_checkmate():
        return -(MATE_SCORE - ply)
    if board.is_stalemate() or board.is_insufficient_material():
        return 0.0
    if board.is_seventyfive_moves() or board.is_fivefold_repetition():
        return 0.0
    return None
