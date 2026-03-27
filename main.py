from chess import Move

import chess
import random
turn_count = 0
board = chess.Board()
piece_values = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0
}
def is_capture(self, move: Move) -> bool:
        """Checks if the given pseudo-legal move is a capture."""
        touched = BB_SQUARES[move.from_square] ^ BB_SQUARES[move.to_square]
        return bool(touched & self.occupied_co[not self.turn]) or self.is_en_passant(move)
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
        for i in range(legal_moves):
            if i == is_capture(True):
                x = is_capture
                AI_move == x
            
                AI_move = largest(piece_values)
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

