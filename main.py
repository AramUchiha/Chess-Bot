import chess
turn_count = 0
board = chess.Board()
def print_board_with_coords(board: chess.Board) -> None:
        files = "a b c d e f g h"
        print("  " + files)
        for rank in range(7, -1, -1):  # 8 down to 1
            row = []
            for file in range(8):      # a to h
                piece = board.piece_at(chess.square(file, rank))
                row.append(piece.symbol() if piece else ".")
            print(f"{rank+1} " + " ".join(row))
        print("  " + files)
while True:
    if turn_count % 2 == 0:
        print("---------White's Turn---------")
    else:
        print("---------Black's Turn---------")

    print_board_with_coords(board)   
    print("Legal moves:", len(list(board.legal_moves)))
    move = input("Select your move: ")
    try:
        move = chess.Move.from_uci(move)
    except ValueError:
        print("Invalid UCI format. Try again.")
        continue
    if move not in board.legal_moves:
        print("That move doesn't work try again: ")
        continue

    board.push(move)
    turn_count+=1
    print("Played:", move.uci())
    if board.is_checkmate():
        print(board)
        print("Checkmate!")
        break
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        print(board)
        print("Game over (draw).")
        break

