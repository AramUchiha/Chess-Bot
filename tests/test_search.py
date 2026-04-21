import chess
import unittest

from evaluation import MATE_SCORE
from search import negamax, transposition_table


class TestNegamax(unittest.TestCase):
    def test_mate_in_one_white(self) -> None:
        """White delivers immediate checkmate in one move."""
        board = chess.Board("7k/8/6KQ/8/8/8/8/8 w - - 0 1")
        mate_uci = set()
        for m in board.legal_moves:
            b = board.copy(stack=False)
            b.push(m)
            if b.is_checkmate():
                mate_uci.add(m.uci())

        self.assertTrue(mate_uci)

        transposition_table.clear()
        best_score = float("-inf")
        best_moves: list[chess.Move] = []
        depth = 4
        for move in board.legal_moves:
            board.push(move)
            score = -negamax(board, depth - 1, float("-inf"), float("inf"))
            board.pop()
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)

        self.assertGreater(best_score, MATE_SCORE / 2)
        chosen = {m.uci() for m in best_moves}
        self.assertTrue(chosen.issubset(mate_uci))

    def test_black_to_move_negamax_finite(self) -> None:
        board = chess.Board()
        board.push(chess.Move.from_uci("e2e4"))
        transposition_table.clear()
        score = negamax(board, 2, float("-inf"), float("inf"))
        self.assertFalse(score != score)  # not NaN
        self.assertLess(abs(score), MATE_SCORE / 2)

    def test_terminal_mate_score_increases_with_ply(self) -> None:
        """Closer mates are more valuable (less negative for the mated side)."""
        from evaluation import terminal_side_relative

        b = chess.Board("7k/8/6KQ/8/8/8/8/8 w - - 0 1")
        b.push(chess.Move.from_uci("h6h7"))
        self.assertTrue(b.is_checkmate())
        s0 = terminal_side_relative(b, ply=0)
        s5 = terminal_side_relative(b, ply=5)
        self.assertIsNotNone(s0)
        self.assertIsNotNone(s5)
        assert s0 is not None and s5 is not None
        self.assertGreater(s5, s0)


if __name__ == "__main__":
    unittest.main()
