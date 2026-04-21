import chess
import unittest

from engine import SearchLimits, choose_move


class TestChooseMove(unittest.TestCase):
    def test_mate_in_one(self) -> None:
        board = chess.Board("7k/8/6KQ/8/8/8/8/8 w - - 0 1")
        mate_uci = set()
        for m in board.legal_moves:
            b = board.copy(stack=False)
            b.push(m)
            if b.is_checkmate():
                mate_uci.add(m.uci())

        move = choose_move(board, SearchLimits(depth=4))
        self.assertIn(move.uci(), mate_uci)

    def test_plays_as_black(self) -> None:
        board = chess.Board()
        board.push(chess.Move.from_uci("e2e4"))
        move = choose_move(board, SearchLimits(depth=2))
        self.assertIn(move, board.legal_moves)


if __name__ == "__main__":
    unittest.main()
