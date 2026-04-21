import chess
from display import print_board_with_coords
from engine import SearchLimits, choose_move
from evaluation import evaluate_white


def human_move(board: chess.Board) -> chess.Move:
    print("---------Your turn---------")

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


def main() -> None:
    board = chess.Board()
    limits = SearchLimits(depth=4)

    while True:
        if board.turn == chess.BLACK:
            print("---------Engine (Black)---------")
            move = choose_move(board, limits)
            board.push(move)
            print("Engine played:", move.uci())
            print("Eval (White-centric):", evaluate_white(board))

            if check_game_over(board):
                break
        else:
            move = human_move(board)
            print("Played:", move.uci())
            if check_game_over(board):
                break


if __name__ == "__main__":
    main()
