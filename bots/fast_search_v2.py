import random
import chess
import time
from typing import List


class FastBotV2:
    """
    Docstring for BasicSearchBot

    Features:
    1. Piece Weights
    2. Pice Square Score
    3. Alpha Beta Pruning Search
    4. Iteratives Eval Function
    """

    # Target: < 0.07 seconds per move

    def __init__(self):

        # Evaluation Tables:
        pawn_sq_tbl = [0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 10, -20, -20, 10, 10, 5, 5, -5, -10, 0, 0, -10, -5, 5, 0, 0, 0, 20, 20, 0, 0, 0, 0, 0, 0, 20, 20, 0, 0, 0, 5, 5, 10, 25, 25, 10,  5, 5, 10, 10, 20, 30, 30, 20, 10, 10, 50, 50, 50, 50, 50, 50, 50, 50, 0, 0, 0, 0, 0, 0, 0, 0]
        knight_sq_tbl = [-50,-40,-30,-30,-30,-30,-40,-50,-40,-20,0,5,5,0,-20,-40,-30,5,10,15,15,10,5,-30,-30,0,15,20,20,15,0,-30,-30,5,15,20,20,15,5,-30,-30,0,10,15,15,10,0,-30,-40,-20,0,0,0,0,-20,-40,-50,-40,-30,-30,-30,-30,-40,-50]
        biship_sq_tbl = [-20,-10,-10,-10,-10,-10,-10,-20,-10,  5,  0,  0,  0,  0,  5,-10,-10, 10, 10, 10, 10, 10, 10,-10,-10,  0, 10, 10, 10, 10,  0,-10,-10,  5,  5, 10, 10,  5,  5,-10,-10,  0,  5, 10, 10,  5,  0,-10,-10,  0,  0,  0,  0,  0,  0,-10,-20,-10,-10,-10,-10,-10,-10,-20]
        rook_sq_tbl = [0, 0, 0, 5, 5, 0, 0, 0, -5, 0, 0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5, -5,  0,  0,  0,  0,  0,  0, -5,5, 10, 10, 10, 10, 10, 10,  5,0,  0,  0,  0,  0,  0,  0,  0]
        queen_sq_tbl = [-20,-10,-10, -5, -5,-10,-10,-20,-10,  0,  5,  0,  0,  0,  0,-10,-10,  5,  5,  5,  5,  5,  0,-10,  0,  0,  5,  5,  5,  5,  0, -5, -5,  0,  5,  5,  5,  5,  0, -5,-10,  0,  5,  5,  5,  5,  0,-10,-10,  0,  0,  0,  0,  0,  0,-10,-20,-10,-10, -5, -5,-10,-10,-20]

        # TODO: update to add middle game
        king_sq_tbl = [-50,-30,-30,-30,-30,-30,-30,-50,-30,-30,  0,  0,  0,  0,-30,-30,-30,-10, 20, 30, 30, 20,-10,-30,-30,-10, 30, 40, 40, 30,-10,-30,-30,-10, 30, 40, 40, 30,-10,-30,-30,-10, 20, 30, 30, 20,-10,-30,-30,-20,-10,  0,  0,-10,-20,-30,-50,-40,-30,-20,-20,-30,-40,-50,]

        self.pieceWt = {
            chess.KING: (20000, king_sq_tbl),
            chess.QUEEN: (900, queen_sq_tbl),
            chess.ROOK: (500, rook_sq_tbl),
            chess.BISHOP: (300, biship_sq_tbl),
            chess.KNIGHT: (300, knight_sq_tbl),
            chess.PAWN: (100, pawn_sq_tbl)
        }

        # Evaluation
        self.evaluation_stack = []
        self.curr_eval = 0

        self.board = None
        self.depth = 4

        # Speed Testing Tools
        self.stat_tracking = False  
        self.positions_searched = 0
        self.total_positions_searched = 0
        self.total_time = 0
        self.total_moves = 0

    def delta_evaluate(self, move) -> int:
        
        delta = 0

        source, target = move.from_square, move.to_square

        piece = self.board.piece_at(source)
        captured_piece = self.board.piece_at(target)

        val, table = self.pieceWt[piece.piece_type]

        # Remove value of start position + start table value
        if piece.color == chess.WHITE:
            delta -= (val + table[source])
        else:
            delta -= -(val + table[source ^ 56])

        # Add value of new positiont + final table value
        if move.promotion:
            p_val, p_table = self.pieceWt[move.promotion]

            if piece.color == chess.WHITE:
                delta += (p_val + p_table[target])
            else:
                delta += -(p_val + p_table[target ^ 56])
        else:
            if piece.color == chess.WHITE:
                delta += (val + table[target])
            else:
                delta += -(val + table[target ^ 56])
        
        # Manage Captures
        if captured_piece:
            c_val, c_table = self.pieceWt[captured_piece.piece_type]
            if captured_piece.color == chess.WHITE:
                delta -= (c_val + c_table[target])
            else:
                delta -= -(c_val + c_table[target])
        elif self.board.is_en_passant(move):
            if self.board.turn == chess.WHITE:
                captured_square = target - 8
            else:
                captured_square = target + 8

            ep_piece = self.board.piece_at(captured_square)
            c_val, c_table = self.pieceWt[ep_piece.piece_type]

            if ep_piece.color == chess.WHITE:
                delta -= (c_val + c_table[captured_square])
            else:
                delta -= -(c_val + c_table[captured_square ^ 56])

        # Manage Castling
        if self.board.is_castling(move):
            if self.board.turn == chess.WHITE:
                if move.to_square == chess.G1:
                    rook_from, rook_to = chess.H1, chess.F1
                elif move.to_square == chess.C1:
                    rook_from, rook_to = chess.A1, chess.D1
            else:
                if move.to_square == chess.G8:
                    rook_from, rook_to = chess.H8, chess.F8
                elif move.to_square == chess.C8:
                    rook_from, rook_to = chess.A8, chess.D8

            r_val, r_table = self.pieceWt[chess.ROOK]

            if self.board.turn == chess.WHITE:
                delta -= (r_val + r_table[rook_from])
                delta += (r_val + r_table[rook_to])
            else:
                delta -= -(r_val + r_table[rook_from ^ 56])
                delta += -(r_val + r_table[rook_to ^ 56])

        return delta

    def init_evaluate(self) -> int:
        """
        Docstring for init_evaluate

        Calculates eval of given current position. Takes the entire position to calculate. Using Negmax algorithm
        
        :param self: DumbEvalV2Bot contains self parameters like piece weights and mobility weights
        :param board: The current board / position to be avaluation
        :type board: chess.Board
        :return: current position eval : (materialScore + mobilityScore) * who2Move
        :rtype: int
        """
        materialScore = 0
        mobilityScore = 0

        for piece, item in self.pieceWt.items():
            value, table = item
            white_squares = self.board.pieces(piece, chess.WHITE)
            black_squares = self.board.pieces(piece, chess.BLACK)

            for square in white_squares:
                mobilityScore += table[square]

            for square in black_squares:
                mobilityScore -= table[square ^ 56]

            materialScore += len(white_squares) * value
            materialScore -= len(black_squares) * value

        total_eval = materialScore + mobilityScore

        return total_eval
        
    def evaluate(self) -> int:
        if self.board.turn:
            return self.curr_eval
        else:
            return -self.curr_eval

    def make_move(self, move):
        delta = self.delta_evaluate(move)

        self.curr_eval += delta
        self.evaluation_stack.append(self.curr_eval)

        self.board.push(move)

    def unmake_move(self):
        self.board.pop()
        self.evaluation_stack.pop()
        self.curr_eval = self.evaluation_stack[-1]
        
    def piece_to_points(self, piece) -> int:
        return self.pieceWt[piece.piece_type][0]
        
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

        moves = self.board.legal_moves
        # moves = self.orderMoves(self.board.legal_moves)

        if not moves:
            if self.board.is_checkmate():
                return -1000000 - depth # Prioritize immediate checkmates
            return 0

        for move in moves:
            self.make_move(move)
            score = - self.search(depth - 1, -beta, -alpha)
            self.unmake_move()

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

            # FORCE RANDOM INITIAL MOVES
            # if self.total_moves <= 2:
            #     return random.choice(list(board.legal_moves))

        self.curr_eval = self.init_evaluate()
        self.evaluation_stack.append(self.curr_eval)

        best_eval = float('-inf')
        best_move = None
    
        alpha = float('-inf')
        beta = float('inf')

        moves = self.board.legal_moves
        # moves = self.orderMoves(self.board.legal_moves)
        
        for move in moves:
            if self.stat_tracking:
                self.positions_searched += 1

            self.make_move(move)

            current_eval = - self.search(
                self.depth - 1, -beta, -alpha
            )

            self.unmake_move()
            
            if current_eval > best_eval:
                best_eval = current_eval
                best_move = move
            
            alpha = max(alpha, best_eval)

        if self.stat_tracking:
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"Evaluated {self.positions_searched} positions in {elapsed_time:.4f} seconds")
            # print(best_eval)
            # print(best_move)

            self.total_time += elapsed_time
            self.total_positions_searched += self.positions_searched

        if best_move:
            return best_move   
        print("ERROR: No best move found")
        return -1
