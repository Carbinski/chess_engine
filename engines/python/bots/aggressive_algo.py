import chess
import random
from typing import List

class AggressiveBot:
    def select_move(self, board: chess.Board) -> chess.Move:
        move_list = list(board.legal_moves)

        aggressive_moves = []

        for move in move_list:
            board.push(move)

            if board.is_checkmate():
                board.pop()
                return move

            board.pop()

            if board.is_capture(move) or board.gives_check(move):
                aggressive_moves.append(move)

        if aggressive_moves:
            return random.choice(aggressive_moves)
        else:
            return random.choice(move_list)
