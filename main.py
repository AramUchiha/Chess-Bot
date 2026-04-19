import random
import chess
from display import print_board_with_coords
from evaluation import evaluate
from search import minimax, transposition_table

board = chess.Board()


def ai_move(board: chess.Board) -> chess.Move:
    print("---------Black's Turn---------")
    transposition_table.clear()
    legal_moves = list(board.legal_moves)

    best_moves = []
    best_score = float("inf")
    search_depth = 3

    for move in legal_moves:
        board.push(move)
        score = minimax(board, search_depth - 1, float("-inf"), float("inf"))
        board.pop()

        # print(f"Testing {move.uci()} -> score {score}")

        if score < best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    best_move = random.choice(best_moves)
    board.push(best_move)
    print("Score:", evaluate(board))
    return best_move


def human_move(board: chess.Board) -> chess.Move:
    print("---------White's Turn---------")

    while True:
        print_board_with_coords(board)

        legal_moves = list(board.legal_moves)
        print("Legal moves:", legal_moves)

        move_text = input("Select your move: ")

        try:
            move = chess.Move.from_uci(move_text)
        except ValueError:
            print("Invalid UCI format. Try again.")
            continue

        if move not in board.legal_moves:
            print("That move doesn't work. Try again.")
            continue

        board.push(move)
        return move


def check_game_over(board: chess.Board) -> bool:
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
    while True:
        if board.turn == chess.BLACK:
            move = ai_move(board)
            print("AI played:", move.uci())

            if check_game_over(board):
                break
        else:
            move = human_move(board)
            print("Played:", move.uci())
            if check_game_over(board):
                break


main()
