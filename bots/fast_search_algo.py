import random
import chess
import time
from typing import List


class FastBot:
    """
    Docstring for BasicSearchBot

    Features:
    1. Basic Piece Weights
    2. Mobility Score
    3. Alpha Beta Pruning Search
    4. Move Ordering for optimal Alph-Beta Pruning Search
    """

    # Target: < 0.07 seconds per move

    def __init__(self):

        # Evaluation Tables:
        pawn_sq_tbl = [0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 10, -20, -20, 10, 10, 5, 5, -5, -10, 0, 0, -10, -5, 5, 0, 0, 0, 20, 20, 0, 0, 0, 0, 0, 0, 20, 20, 0, 0, 0, 5, 5, 10, 25, 25, 10,  5, 5, 10, 10, 20, 30, 30, 20, 10, 10, 50, 50, 50, 50, 50, 50, 50, 50, 0, 0, 0, 0, 0, 0, 0, 0]
        knight_sq_tbl = [-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,5,5,0,-20,-40,-30,5,10,15,15,10,5,-30,-30,0,15,20,20,15,0,-30,-30,5,15,20,20,15,5,-30,-30,0,10,15,15,10,0,-30,-40,-20,0,0,0,0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50]
        biship_sq_tbl = [-20,-10,-10,-10,-10,-10,-10,-20,-10,  5,  0,  0,  0,  0,  5,-10,-10, 10, 10, 10, 10, 10, 10,-10,-10,  0, 10, 10, 10, 10,  0,-10,-10,  5,  5, 10, 10,  5,  5,-10,-10,  0,  5, 10, 10,  5,  0,-10,-10,  0,  0,  0,  0,  0,  0,-10,-20,-10,-10,-10,-10,-10,-10,-20]
        rook_sq_tbl = [0,  0,  0,  5,  5,  0,  0,  0, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5,5, 10, 10, 10, 10, 10, 10,  5,0,  0,  0,  0,  0,  0,  0,  0]
        queen_sq_tbl = [-20,-10,-10, -5, -5,-10,-10,-20,-10,  0,  5,  0,  0,  0,  0,-10,-10,  5,  5,  5,  5,  5,  0,-10,  0,  0,  5,  5,  5,  5,  0, -5, -5,  0,  5,  5,  5,  5,  0, -5,-10,  0,  5,  5,  5,  5,  0,-10,-10,  0,  0,  0,  0,  0,  0,-10,-20,-10,-10, -5, -5,-10,-10,-20]

        # TODO: update to add middle game
        king_sq_tbl = [-50,-30,-30,-30,-30,-30,-30,-50,-30,-30,  0,  0,  0,  0,-30,-30,-30,-10, 20, 30, 30, 20,-10,-30,-30,-10, 30, 40, 40, 30,-10,-30,-30,-10, 30, 40, 40, 30,-10,-30,-30,-10, 20, 30, 30, 20,-10,-30,-30,-20,-10,  0,  0,-10,-20,-30,-50,-40,-30,-20,-20,-30,-40,-50,]

        self.pieceWt = (
            (chess.KING, 20000, king_sq_tbl),
            (chess.QUEEN, 900, queen_sq_tbl),
            (chess.ROOK, 500, rook_sq_tbl),
            (chess.BISHOP, 300, biship_sq_tbl),
            (chess.KNIGHT, 300, knight_sq_tbl),
            (chess.PAWN, 100, pawn_sq_tbl)
        )

        # Evaluation
        self.evaluation_stack = []
        self.curr_eval = 0

        self.board = None
        self.depth = 5

        # Speed Testing Tools
        self.stat_tracking = True
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
        materialScore = 0
        mobilityScore = 0

        for piece, value, table in self.pieceWt:
            white_squares = self.board.pieces(piece, chess.WHITE)
            black_squares = self.board.pieces(piece, chess.BLACK)

            for square in white_squares:
                mobilityScore += table[square]

            for square in black_squares:
                mobilityScore -= table[square]

            materialScore += len(white_squares) * value
            materialScore -= len(black_squares) * value

        total_eval = materialScore + mobilityScore

        if self.board.turn:
            who2move = 1
        else:
            who2move = -1

        return total_eval * who2move    

    def init_evaluate(self) -> int:
        """
        Docstring for evaluate

        Calculates eval of given current position. Using Negmax algorithm
        
        :param self: DumbEvalV2Bot contains self parameters like piece weights and mobility weights
        :param board: The current board / position to be avaluation
        :type board: chess.Board
        :return: current position eval : (materialScore + mobilityScore) * who2Move
        :rtype: int
        """
        materialScore = 0
        mobilityScore = 0

        for piece, value, table in self.pieceWt:
            white_squares = self.board.pieces(piece, chess.WHITE)
            black_squares = self.board.pieces(piece, chess.BLACK)

            for square in white_squares:
                mobilityScore += table[square]

            for square in black_squares:
                mobilityScore -= table[square]

            materialScore += len(white_squares) * value
            materialScore -= len(black_squares) * value

        total_eval = materialScore + mobilityScore

        if self.board.turn:
            who2move = 1
        else:
            who2move = -1

        return total_eval * who2move
        
    # def make_move(self, move):
    #     self.board.push(move)
    #     self.evaluation_stack.append(self.curr_eval)
    
    # def unmake_move(self):
    #     self.board.pop()
    #     self.curr_eval = self.evaluation_stack.pop()
        

    def piece_to_points(self, piece) -> int:
        if piece.piece_type == chess.PAWN:
            return self.pieceWt[-1][1]
        elif piece.piece_type == chess.KNIGHT:
            return self.pieceWt[-2][1]
        elif piece.piece_type == chess.BISHOP:
            return self.pieceWt[-3][1]
        elif piece.piece_type == chess.ROOK:
            return self.pieceWt[-4][1]
        elif piece.piece_type == chess.QUEEN:
            return self.pieceWt[1][1]
        elif piece.piece_type == chess.KING:
            return self.pieceWt[0][1]

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
                    victim_points = self.pieceWt[-1][1]
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
            return self.evaluate();

        max_eval = float("-inf")

        moves = self.orderMoves(self.board.legal_moves)

        if not moves:
            if self.board.is_checkmate():
                return -1000000 - depth # Prioritize immediate checkmates
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

        moves = self.orderMoves(self.board.legal_moves)
        
        for move in moves:
            if self.stat_tracking:
                self.positions_searched += 1

            self.board.push(move)

            current_eval = - self.search(
                self.depth - 1, -beta, -alpha
            )

            self.board.pop()
            
            if current_eval > best_eval:
                best_eval = current_eval
                best_moves = [move]
            elif current_eval == best_eval:
                best_moves.append(move)
            
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
