import random
import chess
import time
from typing import List


class FastBotV4:
    """
    Docstring for BasicSearchBot

    Features:
    1. Piece Weights
    2. Square Piece Scores
    3. Alpha Beta Pruning Search
    4. MVA-LVA
    5. Iterative Eval Function
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

        self.pieceWt = [
            None,
            (100, pawn_sq_tbl),
            (300, knight_sq_tbl),
            (300, biship_sq_tbl),
            (500, rook_sq_tbl),
            (900, queen_sq_tbl),
            (20000, king_sq_tbl)
        ]

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

        # Local lookup improves speed
        board, PIECE_WT = self.board, self.pieceWt

        source, target = move.from_square, move.to_square
        piece = board.piece_at(source)

        val, table = PIECE_WT[piece.piece_type]

        if piece.color:
            delta -= (val + table[source])
        else:
            delta -= -(val + table[source ^ 56])

        if move.promotion:
            p_val, p_table = PIECE_WT[move.promotion]
            if piece.color:
                delta += (p_val + p_table[target])
            else:
                delta += -(p_val + p_table[target ^ 56])
        else:
            if piece.color:
                delta += (val + table[target])
            else:
                delta += -(val + table[target ^ 56])
        
        # Manage Captures
        if board.is_capture(move):
            if board.is_en_passant(move):
                if board.turn == chess.WHITE:
                    cap_sq = target - 8
                else:
                    cap_sq = target + 8
                ep_piece = board.piece_at(cap_sq)

                if ep_piece:
                    c_val, c_table = PIECE_WT[ep_piece.piece_type]
                    if ep_piece.color == chess.WHITE:
                        delta -= (c_val + c_table[cap_sq])
                    else:
                        delta -= -(c_val + c_table[cap_sq ^ 56])
            else:
                captured_piece = board.piece_at(target)
                if captured_piece:
                    c_val, c_table = PIECE_WT[captured_piece.piece_type]
                    if captured_piece.color == chess.WHITE:
                        delta -= (c_val + c_table[target])
                    else:
                        delta -= -(c_val + c_table[target])

        # Manage Castling
        if piece.piece_type == chess.KING and abs(source - target) == 2:
            if move.to_square == chess.G1:
                rook_from, rook_to = chess.H1, chess.F1
            elif move.to_square == chess.C1:
                rook_from, rook_to = chess.A1, chess.D1
            elif move.to_square == chess.G8:
                rook_from, rook_to = chess.H8, chess.F8
            elif move.to_square == chess.C8:
                rook_from, rook_to = chess.A8, chess.D8
            else:
                return delta

            r_val, r_table = PIECE_WT[chess.ROOK]

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
        score = 0
        board, PIECE_WT = self.board, self.pieceWt

        for i in range(1, 7):
            value, table = PIECE_WT[i]
            
            for square in board.pieces(i, chess.WHITE):
                score += (value + table[square])
            
            for square in board.pieces(i, chess.BLACK):
                score -= (value + table[square ^ 56])

        return score
   
    def orderMoves(self, moves: List[chess.Move]) -> List[chess.Move]:
        captures = []
        rest = []

        board = self.board
        PIECE_WT = self.pieceWt
        piece_type_at = self.board.piece_type_at
        is_en_passant = self.board.is_en_passant

        ep_square = self.board.ep_square if self.board.ep_square else -1

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
                rest.append(move)
        
        # Sort moves, return list
        captures.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in captures] + rest

    def search(self, depth: int, alpha: int, beta: int, current_eval: int) -> int:
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
            return current_eval if self.board.turn else -current_eval

        moves = self.orderMoves(self.board.legal_moves)

        if not moves:
            if self.board.is_checkmate():
                return -1000000 - depth
            return 0

        max_eval = float("-inf")
        push = self.board.push
        pop = self.board.pop
        get_delta = self.delta_evaluate

        for move in moves:
            diff = get_delta(move)

            push(move)
            score = - self.search(depth - 1, -beta, -alpha, current_eval + diff)
            pop()

            if (score > max_eval):
                max_eval = score

            alpha = max(alpha, score)
            if alpha >= beta:
                break
        
        return max_eval

    def select_move(self, board: chess.Board) -> chess.Move:
        if self.stat_tracking:
            start_time = time.perf_counter()
            self.positions_searched = 0
            self.total_moves += 1
        
        self.board = board
        root_eval = self.init_evaluate()

        best_eval, best_move = float('-inf'), None
        alpha, beta = float('-inf'), float('inf')

        moves = self.orderMoves(self.board.legal_moves)
        
        for move in moves:
            if self.stat_tracking:
                self.positions_searched += 1
            
            diff = self.delta_evaluate(move)

            self.board.push(move)
            current_eval = - self.search(
                self.depth - 1, -beta, -alpha, root_eval + diff
            )
            self.board.pop()
            
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
