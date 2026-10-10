import random
import chess
import time
from typing import List


class BasicSearchBot:
    """
    Docstring for BasicSearchBot

    Features:
    1. Basic Piece Weights
    2. Mobility Score
    3. Alpha Beta Pruning Search
    4. Move Ordering for optimal Alph-Beta Pruning Search
    """

    def __init__(self):
        self.kingWt = 20000
        self.queenWt = 900
        self.rookWt = 500
        self.bishopWt = 300
        self.knightWt = 300
        self.pawnWt = 100

        self.mobilityWt = 1
        self.board = None
        self.depth = 3

        self.stat_tracking = False
        self.positions_searched = 0
        self.total_positions_searched = 0
        self.total_time = 0
        self.total_moves = 0

    def evaluate(self) -> int:
        """
        Docstring for evaluate

        Calculates eval of given current position. Using Negmax algorithm
        
        :param self: DumbEvalV2Bot contains self parameters like piece weights and mobility weights
        :param board: The current board / position to be avaluation
        :type board: chess.Board
        :return: current position eval : (materialScore + mobilityScore) * who2Move
        :rtype: int
        """
        
        wP = len(self.board.pieces(chess.PAWN, chess.WHITE))
        wN = len(self.board.pieces(chess.KNIGHT, chess.WHITE))
        wB = len(self.board.pieces(chess.BISHOP, chess.WHITE))
        wR = len(self.board.pieces(chess.ROOK, chess.WHITE))
        wQ = len(self.board.pieces(chess.QUEEN, chess.WHITE))

        bP = len(self.board.pieces(chess.PAWN, chess.BLACK))
        bN = len(self.board.pieces(chess.KNIGHT, chess.BLACK))
        bB = len(self.board.pieces(chess.BISHOP, chess.BLACK))
        bR = len(self.board.pieces(chess.ROOK, chess.BLACK))
        bQ = len(self.board.pieces(chess.QUEEN, chess.BLACK))

        wK = len(self.board.pieces(chess.KING, chess.WHITE))
        bK = len(self.board.pieces(chess.KING, chess.BLACK))

        materialScore = (
            self.kingWt  * (wK-bK) +
            self.queenWt * (wQ-bQ) +
            self.rookWt  * (wR-bR) +
            self.bishopWt * (wB-bB) +
            self.knightWt * (wN-bN) +
            self.pawnWt  * (wP-bP)
        )

        # Can use pseudo legal move to speed up
        wMobility = self.board.pseudo_legal_moves.count()

        self.board.turn = not self.board.turn
        bMobility = self.board.pseudo_legal_moves.count()

        self.board.turn = not self.board.turn 

        mobilityScore = self.mobilityWt * (wMobility - bMobility)

        total_eval = materialScore + mobilityScore

        if self.board.turn:
            who2move = 1
        else:
            who2move = -1

        return total_eval * who2move
        
    def piece_to_points(self, piece) -> int:
        if piece.piece_type == chess.PAWN:
            return self.pawnWt
        elif piece.piece_type == chess.KNIGHT:
            return self.knightWt
        elif piece.piece_type == chess.BISHOP:
            return self.bishopWt
        elif piece.piece_type == chess.ROOK:
            return self.rookWt
        elif piece.piece_type == chess.QUEEN:
            return self.queenWt
        elif piece.piece_type == chess.KING:
            return self.kingWt

        print("[ERROR] square_to_point : NO VALID PIECES FOUND")
        return -1
        
    def orderMoves(self, moves: List[chess.Move]) -> List[chess.Move]:
        move_scores = []
        
        for move in moves:
            score = 0

            # Bonus for giving checks
            if self.board.gives_check(move):
                score += 50
            
            # Bonus for castling
            if self.board.is_castling(move):
                score += 60

            # Bonus for captures
            if self.board.is_capture(move):
                if self.board.is_en_passant(move):
                    victim_points = self.pawnWt
                else:
                    victim_points = self.piece_to_points(self.board.piece_at(move.to_square))

                attacker_points = self.piece_to_points(self.board.piece_at(move.from_square))
                
                score += (10 * victim_points) - attacker_points
            
            # Bonus for promotion
            if move.promotion:
                score += 900
                if move.promotion == chess.QUEEN:
                    score += 100
            
            move_scores.append((score, move))

        # Sort moves, return list
        move_scores.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in move_scores]

    def search(self, depth: int, alpha: int, beta: int) -> int:
        """
        Docstring for search

        Recursive searching function using alpha-beta pruning
        
        :param self: Stores board, number of positions searched
        :param depth: Depth that needs to be searched
        :type depth: int
        :param alpha: maximum value player can guarantee at any point of search
        :type alpha: int
        :param beta: minimum value player can gaurantee at any point of search
        :type beta: int
        :return: max alpha : maximum value for the position
        :rtype: int

        """
        if self.stat_tracking:
            self.positions_searched += 1
        
        if depth == 0:
            return self.evaluate()

        max_eval = float("-inf")

        moves = list(self.board.legal_moves)
        moves = self.orderMoves(moves)

        if not moves:
            if self.board.is_checkmate():
                return -1000000
            return 0

        for move in moves:
            self.board.push(move)
            score = - self.search(depth - 1, -beta, -alpha)
            self.board.pop()

            if (score > max_eval):
                max_eval = score

            alpha = max(alpha, score)

            if alpha >= beta:
                break
        
        return max_eval

    def select_move(self, board: chess.Board) -> chess.Move:
        self.board = board

        if self.stat_tracking:
            start_time = time.perf_counter()
            self.positions_searched = 0
            self.total_moves += 1

        best_eval = float('-inf')
        best_moves = []
    
        alpha = float('-inf')
        beta = float('inf')

        moves = board.legal_moves
        moves = self.orderMoves(moves)
        
        for move in moves:
            if self.stat_tracking:
                self.positions_searched += 1

            self.board.push(move)

            current_eval = - self.search(
                self.depth - 1, alpha, beta
            )

            self.board.pop()
            
            if current_eval > best_eval:
                best_eval = current_eval
                best_moves = [move]
            
            alpha = max(alpha, best_eval)

        if self.stat_tracking:
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"Evaluated {self.positions_searched} positions in {elapsed_time:.4f} seconds")

            self.total_time += elapsed_time
            self.total_positions_searched += self.positions_searched

        if best_moves:
            return random.choice(best_moves)    
        print("ERROR: No best move found")
        return -1
