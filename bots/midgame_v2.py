import random
import chess
from typing import List
import time


class MidGameBotV2:

    def __init__(self):

        mg_pawn_table   = [0,0,0,0,0,0,0,0,-35,-1,-20,-23,-15,24,38,-22,-26,-4,-4,-10,3,3,33,-12,-27,-2,-5,12,17,6,10,-25,-14,13,6,21,23,12,17,-23,-6,7,26,31,65,56,25,-20,98,134,61,95,68,126,34,-11,0,0,0,0,0,0,0,0]
        eg_pawn_table   = [0,0,0,0,0,0,0,0,13,8,8,10,13,0,2,-7,4,7,-6,1,0,-5,-1,-8,13,9,-3,-7,-7,-8,3,-1,32,24,13,5,-2,4,17,17,94,100,85,67,56,53,82,84,178,173,158,134,147,132,165,187,0,0,0,0,0,0,0,0,]
        mg_knight_table = [-105,-21,-58,-33,-17,-28,-19,-23,-29,-53,-12,-3,-1,18,-14,-19,-23,-9,12,10,19,17,25,-16,-13,4,16,13,28,19,21,-8,-9,17,19,53,37,69,18,22,-47,60,37,65,84,129,73,44,-73,-41,72,36,23,62,7,-17,-167,-89,-34,-49,61,-97,-15,-107,]
        eg_knight_table = [-29,-51,-23,-15,-22,-18,-50,-64,-42,-20,-10,-5,-2,-20,-23,-44,-23,-3,-1,15,10,-3,-20,-22,-18,-6,16,25,16,17,4,-18,-17,3,22,22,22,11,8,-18,-24,-20,10,9,-1,-9,-19,-41,-25,-8,-25,-2,-9,-25,-24,-52,-58,-38,-13,-28,-31,-27,-63,-99,]
        mg_bishop_table = [-33,-3,-14,-21,-13,-12,-39,-21,4,15,16,0,7,21,33,1,0,15,15,15,14,27,18,10,-6,13,13,26,34,12,10,4,-4,5,19,50,37,37,7,-2,-16,37,43,40,35,50,37,-2,-26,16,-18,-13,30,59,18,-47,-29,4,-82,-37,-25,-42,7,-8,]
        eg_bishop_table = [-23,-9,-23,-5,-9,-16,-5,-17,-14,-18,-7,-1,4,-9,-15,-27,-12,-3,8,10,13,3,-7,-15,-6,3,13,19,7,10,-3,-9,-3,9,12,9,14,10,3,2,2,-8,0,-1,-2,6,0,4,-8,-4,7,-12,-3,-13,-4,-14,-14,-21,-11,-8,-7,-9,-17,-24,]
        mg_rook_table   = [-19,-13,1,17,16,7,-37,-26,-44,-16,-20,-9,-1,11,-6,-71,-45,-25,-16,-17,3,0,-5,-33,-36,-26,-12,-1,9,-7,6,-23,-24,-11,7,26,24,35,-8,-20,-5,19,26,36,17,45,61,16,27,32,58,62,80,67,26,44,32,42,32,51,63,9,31,43,]
        eg_rook_table   = [-9,2,3,-1,-5,-13,4,-20,-6,-6,0,2,-9,-9,-11,-3,-4,0,-5,-1,-7,-12,-8,-16,3,5,8,4,-5,-6,-8,-11,4,3,13,1,2,1,-1,2,7,7,7,5,4,-3,-5,-3,11,13,13,11,-3,3,8,3,13,10,18,15,12,12,8,5,]
        mg_queen_table  = [-1,-18,-9,10,-15,-25,-31,-50,-35,-8,11,2,8,15,-3,1,-14,2,-11,-2,-5,2,14,5,-9,-26,-9,-10,-2,-4,3,-3,-27,-27,-16,-16,-1,17,-2,1,-13,-17,7,8,29,56,47,57,-24,-39,-5,1,-16,57,28,54,-28,0,29,12,59,44,43,45,]
        eg_queen_table  = [-33,-28,-22,-43,-5,-32,-20,-41,-22,-23,-30,-16,-16,-23,-36,-32,-16,-27,15,6,9,17,10,5,-18,28,19,47,31,34,39,23,3,22,24,45,57,40,57,36,-20,6,9,49,47,35,19,9,-17,20,32,41,58,25,30,0,-9,22,22,27,27,19,10,20,]
        mg_king_table   = [-15,36,12,-54,8,-28,24,14,1,7,-8,-64,-43,-16,9,8,-14,-14,-22,-46,-44,-30,-15,-27,-49,-1,-27,-39,-46,-44,-33,-51,-17,-20,-12,-27,-30,-25,-14,-36,-9,24,2,-16,-20,6,22,-22,29,-1,-20,-7,-8,-4,-38,-29,-65,23,16,-15,-56,-34,2,13,]
        eg_king_table   = [-53,-34,-21,-11,-28,-14,-24,-43,-27,-11,4,13,14,4,-5,-17,-19,-3,11,21,23,16,7,-9,-18,-4,21,24,27,23,9,-11,-8,22,24,27,26,33,26,3,10,17,23,15,20,45,44,13,-12,17,14,17,17,38,23,11,-74,-35,-18,-18,-11,15,4,-17,]

        self.pieceWt = [
            None,
            (100, mg_pawn_table, eg_pawn_table),
            (300, mg_knight_table, eg_knight_table),
            (300, mg_bishop_table, eg_bishop_table),
            (500, mg_rook_table, eg_rook_table),
            (900, mg_queen_table, eg_queen_table),
            (20000, mg_king_table, eg_king_table)
        ]

        self.board = None
        self.depth = 5

        self.stat_tracking = True
        self.random_opening = False
        self.total_moves = 0
        self.total_time = 0

    def get_phase(self) -> float:
        board, PIECE_WT = self.board, self.pieceWt

        materials = (
            board.knights.bit_count() * PIECE_WT[2][0] +
            board.bishops.bit_count() * PIECE_WT[3][0] +
            board.rooks.bit_count() * PIECE_WT[4][0] +
            board.queens.bit_count() * PIECE_WT[5][0]
        )

        phase = materials / 6200
        return round(max(0.0, min(1.0, phase)), 2)

    def evaluate(self) -> float:
        score = 0
        board, PIECE_WT = self.board, self.pieceWt
        phase = self.get_phase()
        eg_phase = 1 - phase

        for i in range(1, 7):
            value, mg_table, eg_table = PIECE_WT[i]
            
            for square in board.pieces(i, chess.WHITE):
                score += (value + (phase * mg_table[square]) + (eg_phase * eg_table[square]))
            
            for square in board.pieces(i, chess.BLACK):
                score -= (value + (phase * mg_table[square ^ 56]) + (eg_phase * eg_table[square ^ 56]))

        if self.board.turn:
            who2move = 1
        else:
            who2move = -1

        return score * who2move
   
    def orderMoves(self, moves: List[chess.Move]) -> List[chess.Move]:
        captures, ignore = [], []
        board, PIECE_WT = self.board, self.pieceWt

        piece_type_at = board.piece_type_at
        is_en_passant = board.is_en_passant

        ep_square = board.ep_square if board.ep_square else -1

        for move in moves:
            victim_type = piece_type_at(move.to_square)

            if victim_type:
                attacker_type = piece_type_at(move.from_square)
                score = (10 * PIECE_WT[victim_type][0]) - PIECE_WT[attacker_type][0]
                captures.append((score, move))
            elif move.to_square == ep_square and is_en_passant(move):
                score = (100 * 10) - 100
                captures.append((score, move))
            else:
                ignore.append(move)
        
        captures.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in captures] + ignore

    def search(self, depth: int, alpha: int, beta: int) -> int:      
        if depth == 0:
            return self.evaluate()

        moves = self.orderMoves(self.board.legal_moves)

        if not moves:
            if self.board.is_checkmate():
                return -1000000 - depth
            return 0

        max_eval = float("-inf")
        push, pop = self.board.push, self.board.pop

        for move in moves:
            push(move)
            score = - self.search(depth - 1, -beta, -alpha)
            pop()

            if (score > max_eval):
                max_eval = score

            alpha = max(alpha, score)

            if alpha >= beta:
                break
        
        return max_eval

    def select_move(self, board: chess.Board) -> chess.Move:  
        self.total_moves += 1 

        if self.random_opening and self.total_moves < 3:
            return random.choice(list(board.generate_legal_moves()))
        
        
        if self.stat_tracking:
            start_time = time.perf_counter()

        self.board = board
        
        best_eval, best_move = float('-inf'), None
        alpha, beta = float('-inf'), float('inf')

        moves = self.orderMoves(self.board.legal_moves)
        
        for move in moves:            
            self.board.push(move)
            current_eval = - self.search(
                self.depth - 1, -beta, -alpha,
            )
            self.board.pop()
            
            if current_eval > best_eval:
                best_eval = current_eval
                best_move = move
            
            alpha = max(alpha, best_eval)

        if self.stat_tracking:
            end_time = time.perf_counter()
            self.total_time += end_time - start_time
            print(f"MOVE: {best_move} | EVAL: {best_eval} | GAMESTAGE: {self.get_phase()} | TIME: {end_time - start_time}")

        return best_move
