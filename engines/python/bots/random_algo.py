import chess
import random
from typing import List

class RandomBot:
    def select_move(self, board: chess.Board) -> chess.Move:
        move_list = list(board.legal_moves)
        return random.choice(move_list)
