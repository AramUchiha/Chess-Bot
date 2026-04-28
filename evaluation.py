import chess

# Used by search for terminal nodes; must dominate material scale.
MATE_SCORE = 10_000.0

# Material values in centipawns.
MG_VALUE = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 335,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}
EG_VALUE = {
    chess.PAWN: 120,
    chess.KNIGHT: 300,
    chess.BISHOP: 330,
    chess.ROOK: 520,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# Phase weights (how much each piece contributes to middlegame phase).
PHASE_WEIGHT = {
    chess.PAWN: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 1,
    chess.ROOK: 2,
    chess.QUEEN: 4,
    chess.KING: 0,
}
MAX_PHASE = 24


def _mirror_if_black(square: chess.Square, color: chess.Color) -> chess.Square:
    return square if color == chess.WHITE else chess.square_mirror(square)


# Lightweight piece-square tables. Positive values mean better for White.
PAWN_MG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, -20, -20, 10, 10, 5,
    5, -5, -10, 0, 0, -10, -5, 5,
    0, 0, 0, 22, 22, 0, 0, 0,
    5, 5, 10, 25, 25, 10, 5, 5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0, 0, 0, 0, 0, 0, 0, 0,
]
PAWN_EG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    10, 10, 10, -10, -10, 10, 10, 10,
    10, 10, 10, 0, 0, 10, 10, 10,
    15, 15, 15, 25, 25, 15, 15, 15,
    20, 20, 20, 30, 30, 20, 20, 20,
    30, 30, 30, 40, 40, 30, 30, 30,
    60, 60, 60, 60, 60, 60, 60, 60,
    0, 0, 0, 0, 0, 0, 0, 0,
]
KNIGHT_MG = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50,
]
KNIGHT_EG = KNIGHT_MG
BISHOP_MG = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]
BISHOP_EG = BISHOP_MG
ROOK_MG = [
    0, 0, 5, 10, 10, 5, 0, 0,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    5, 10, 10, 10, 10, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
]
ROOK_EG = ROOK_MG
QUEEN_MG = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20,
]
QUEEN_EG = QUEEN_MG
KING_MG = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20,
]
KING_EG = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50,
]

PST_MG = {
    chess.PAWN: PAWN_MG,
    chess.KNIGHT: KNIGHT_MG,
    chess.BISHOP: BISHOP_MG,
    chess.ROOK: ROOK_MG,
    chess.QUEEN: QUEEN_MG,
    chess.KING: KING_MG,
}
PST_EG = {
    chess.PAWN: PAWN_EG,
    chess.KNIGHT: KNIGHT_EG,
    chess.BISHOP: BISHOP_EG,
    chess.ROOK: ROOK_EG,
    chess.QUEEN: QUEEN_EG,
    chess.KING: KING_EG,
}

FILE_MASKS = [chess.BB_FILES[i] for i in range(8)]


def _pawn_structure_score(board: chess.Board, color: chess.Color) -> int:
    pawns = board.pieces(chess.PAWN, color)
    enemy_pawns = board.pieces(chess.PAWN, not color)
    score = 0
    file_counts = [0] * 8
    enemy_max_rank = [-1] * 8
    enemy_min_rank = [8] * 8
    for sq in pawns:
        file_counts[chess.square_file(sq)] += 1
    for sq in enemy_pawns:
        ef = chess.square_file(sq)
        er = chess.square_rank(sq)
        if er > enemy_max_rank[ef]:
            enemy_max_rank[ef] = er
        if er < enemy_min_rank[ef]:
            enemy_min_rank[ef] = er

    for sq in pawns:
        file_idx = chess.square_file(sq)

        # Doubled pawns.
        if file_counts[file_idx] > 1:
            score -= 12

        # Isolated pawns.
        has_left = file_idx > 0 and (pawns & FILE_MASKS[file_idx - 1]) != 0
        has_right = file_idx < 7 and (pawns & FILE_MASKS[file_idx + 1]) != 0
        if not has_left and not has_right:
            score -= 10

        # Passed pawns.
        rank = chess.square_rank(sq)
        passed = True
        for f in (file_idx - 1, file_idx, file_idx + 1):
            if f < 0 or f > 7:
                continue
            if color == chess.WHITE:
                if enemy_max_rank[f] > rank:
                    passed = False
                    break
            else:
                if enemy_min_rank[f] < rank:
                    passed = False
                    break
        if passed:
            advance = rank if color == chess.WHITE else 7 - rank
            score += 12 + 6 * advance

    return score


def _king_shield_score(board: chess.Board, color: chess.Color) -> int:
    king_sq = board.king(color)
    if king_sq is None:
        return 0
    kf = chess.square_file(king_sq)
    kr = chess.square_rank(king_sq)

    score = 0
    pawns = board.pieces(chess.PAWN, color)
    step = 1 if color == chess.WHITE else -1
    shield_rank = kr + step
    if shield_rank < 0 or shield_rank > 7:
        return 0

    for df in (-1, 0, 1):
        ff = kf + df
        if ff < 0 or ff > 7:
            continue
        shield_sq = chess.square(ff, shield_rank)
        if shield_sq in pawns:
            score += 10
        else:
            score -= 8
    return score


def evaluate_white(board: chess.Board) -> float:
    """Static evaluation in centipawns: positive favors White."""
    mg_score = 0
    eg_score = 0
    phase = 0
    white_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
    black_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))

    for piece_type in (
        chess.PAWN,
        chess.KNIGHT,
        chess.BISHOP,
        chess.ROOK,
        chess.QUEEN,
        chess.KING,
    ):
        mg_base = MG_VALUE[piece_type]
        eg_base = EG_VALUE[piece_type]
        mg_pst = PST_MG[piece_type]
        eg_pst = PST_EG[piece_type]
        w_squares = board.pieces(piece_type, chess.WHITE)
        b_squares = board.pieces(piece_type, chess.BLACK)
        phase += PHASE_WEIGHT[piece_type] * (len(w_squares) + len(b_squares))

        for sq in w_squares:
            mg_score += mg_base + mg_pst[sq]
            eg_score += eg_base + eg_pst[sq]
        for sq in b_squares:
            msq = chess.square_mirror(sq)
            mg_score -= mg_base + mg_pst[msq]
            eg_score -= eg_base + eg_pst[msq]

    # Cheap structural terms.
    mg_score += _pawn_structure_score(board, chess.WHITE)
    mg_score -= _pawn_structure_score(board, chess.BLACK)
    eg_score += _pawn_structure_score(board, chess.WHITE)
    eg_score -= _pawn_structure_score(board, chess.BLACK)

    mg_score += _king_shield_score(board, chess.WHITE)
    mg_score -= _king_shield_score(board, chess.BLACK)

    # Bishop pair.
    if white_bishops >= 2:
        mg_score += 30
        eg_score += 40
    if black_bishops >= 2:
        mg_score -= 30
        eg_score -= 40

    # Blend middlegame/endgame scores based on phase.
    phase = min(phase, MAX_PHASE)
    blended = (mg_score * phase + eg_score * (MAX_PHASE - phase)) / MAX_PHASE

    # Keep check bonus tiny to avoid tactical overfitting in static eval.
    if board.is_check():
        blended += -8 if board.turn == chess.WHITE else 8

    # Return in pawn units to keep compatible with existing search bounds.
    return blended / 100.0


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
