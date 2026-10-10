from collections import Counter
import chess
import random
from typing import Tuple

"""
class chess.Board(
    fen: str | None = 
    'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', 
    *, chess960: bool = False
)
"""
class DumbEvalBot:

    def calculate_eval(self, board: chess.Board) -> Tuple[int, int]:
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)
        black_knights = board.pieces(chess.KNIGHT, chess.BLACK)
        black_bishops = board.pieces(chess.BISHOP, chess.BLACK)
        black_rooks = board.pieces(chess.ROOK, chess.BLACK)
        black_queens = board.pieces(chess.QUEEN, chess.BLACK)
        black_king = board.pieces(chess.KING, chess.BLACK)

        black_eval = (
            200 * len(black_king)
            + 1 * len(black_pawns) 
            + 3 * len(black_bishops) 
            + 3 * len(black_knights)
            + 5 * len(black_rooks)
            + 9 * len(black_queens)
        )

        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        white_knights = board.pieces(chess.KNIGHT, chess.WHITE)
        white_bishops = board.pieces(chess.BISHOP, chess.WHITE)
        white_rooks = board.pieces(chess.ROOK, chess.WHITE)
        white_queens = board.pieces(chess.QUEEN, chess.WHITE)
        white_king = board.pieces(chess.KING, chess.WHITE)

        white_eval = (
            200 * len(white_king)
            + 1 * len(white_pawns) 
            + 3 * len(white_knights) 
            + 3 * len(white_bishops)
            + 5 * len(white_rooks)
            + 9 * len(white_queens)
        )
        
        return white_eval, black_eval

    def select_move(self, board: chess.Board) -> chess.Move:
        move_list = list(board.legal_moves)
        fen_data = board.fen().split(" ")
        current_move = fen_data[1]
        
        best_score = -1000
        best_moves = []

        for move in move_list:
            board.push(move)

            if board.is_checkmate():
                board.pop()
                return move
            
            white_eval, black_eval = self.calculate_eval(board)

            board.pop()

            if current_move == "w":
                current_score = white_eval - black_eval
            else:
                current_score = black_eval - white_eval
            
            if current_score > best_score:
                best_score = current_score
                best_moves = [move]
            elif current_score == best_score:
                best_moves.append(move)

        # print(best_score)
        # print(best_move)

        if best_moves:
            return random.choice(best_moves)
        else:
            return random.choice(move_list)
