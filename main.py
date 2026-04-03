import chess
import random

board = chess.Board()
piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}


def evaluate() -> int:  # Returns the material score of the current board
    score = 0
    # reward center control
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
    for piece_type, value in piece_values.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * value
        score -= len(board.pieces(piece_type, chess.BLACK)) * value
    return score


def print_board_with_coords(
    board: chess.Board,
) -> None:  # Prints the board with coordinates
    files = "a b c d e f g h"
    print("  " + files)
    for rank in range(7, -1, -1):  # 8 down to 1
        row = []
        for file in range(8):  # a to h
            piece = board.piece_at(chess.square(file, rank))
            row.append(piece.symbol() if piece else ".")
        print(f"{rank + 1} " + " ".join(row))
    print("  " + files)


def ai_move() -> chess.Move:
    print("---------Black's Turn---------")
    legal_moves = list(board.legal_moves)

    best_move = None
    best_score = float("inf")

    for move in legal_moves:
        board.push(move)
        score = evaluate()
        board.pop()

        print(f"Testing {move.uci()} -> score {score}")

        if score < best_score:
            best_score = score
            best_move = move

    board.push(best_move)
    print("AI played:", best_move.uci())
    print("Score:", evaluate())
    return best_move


def human_move() -> chess.Move:
    print("---------White's Turn---------")

    while True:
        print_board_with_coords(board)
        legal_moves = list(board.legal_moves)

        # Legal move checking
        print("Legal moves:", legal_moves)
        move_text = input("Select your move: ")
        try:
            move = chess.Move.from_uci(move_text)
        except ValueError:
            print("Invalid UCI format. Try again.")
            continue

        if move not in board.legal_moves:
            print("That move doesn't work try again: ")
            continue

        board.push(move)
        return move


def check_game_over() -> bool:
    if board.is_checkmate():
        print(board)
        print("Checkmate!")
        return True
    if (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.can_claim_draw()
    ):
        print(board)
        print("Game over (draw).")
        return True
    return False


def main():
    while True:  # Game loop
        if board.turn == chess.BLACK:
            ai_move()
            if check_game_over():
                break

        move = human_move()
        print("Played:", move.uci())
        if check_game_over():
            break


main()
