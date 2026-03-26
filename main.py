from chess import Move


import chess
import random
turn_count = 0
board = chess.Board()
def evaluate(board):
    score = 0

    for every square in chess.SQUARES:
        piece = board.piece_at(square)
        if there is a piece:
            get value
            if white: add
            if black: subtract

    return score
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
        legal_moves = list(board.legal_moves)

    else:
        print("---------Black's Turn---------")
        legal_moves = list(board.legal_moves)
        AI_move = random.choice(legal_moves)
        board.push(AI_move)
        turn_count += 1
        print("AI played:", AI_move.uci())
        continue

    print_board_with_coords(board)   
    print("Legal moves:", legal_moves)
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

