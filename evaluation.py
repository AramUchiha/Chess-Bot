import chess

piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}


def evaluate(board: chess.Board) -> float:
    score = 0.0

    # Reward center control
    center_squares = [chess.D4, chess.E4, chess.D5, chess.E5]
    for square in center_squares:
        piece = board.piece_at(square)
        if piece:
            if piece.color == chess.WHITE:
                score += 0.5
            else:
                score -= 0.5

    # Check bonus
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

    # Material
    for piece_type, value in piece_values.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value

    return score
