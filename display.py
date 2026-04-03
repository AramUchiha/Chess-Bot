import chess


def print_board_with_coords(board: chess.Board) -> None:
    files = "a b c d e f g h"
    print("  " + files)

    for rank in range(7, -1, -1):
        row = []
        for file in range(8):
            piece = board.piece_at(chess.square(file, rank))
            row.append(piece.symbol() if piece else ".")
        print(f"{rank + 1} " + " ".join(row))

    print("  " + files)
