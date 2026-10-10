import chess
import time
from typing import List


class SlowSearchBot:
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

        self.selected_move = None

        self.debug = True
        self.moves_searched = 0

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
        
        originalTurn = self.board.turn

        # Can use pseudo legal move to speed up
        self.board.turn = chess.WHITE
        wMobility = self.board.legal_moves.count()

        self.board.turn = chess.BLACK
        bMobility = self.board.legal_moves.count()

        self.board.turn = originalTurn


        mobilityScore = self.mobilityWt * (wMobility - bMobility)

        total_eval = materialScore + mobilityScore

        if self.board.turn == chess.WHITE:
            return -1 * total_eval
        else:
            return total_eval
        
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

        if self.debug:
                self.moves_searched += 1

        if depth == 0:
            return self.evaluate()
        
        moves = self.board.legal_moves

        if moves.count() == 0:
            if self.board.is_check():
                return -2147000000
            else:
                return 0

        for move in moves:
            
            self.board.push(move)
            # flip alpha and beta becuase turns switch
            curr_eval = - self.search(depth - 1, -beta, -alpha)
            self.board.pop()

            if curr_eval >= beta:
                return beta

            alpha = max(alpha, curr_eval)

        return alpha

    def select_move(self, board: chess.Board) -> chess.Move:
        self.board = board
        self.moves_searched = 0
        best_move = None 

        alpha, beta = -2147000000, 214700000

        if self.debug:
            start_time = time.perf_counter()
        
        moves = list(self.board.legal_moves)

        for move in moves:
            
            if self.debug:
                self.moves_searched += 1

            self.board.push(move)
            evaluation = -self.search(self.depth - 1, -beta, -alpha)
            self.board.pop()
            
            if evaluation >= alpha:
                alpha = evaluation
                best_move = move

            print(evaluation)
        
        if self.debug:
            end_time = time.perf_counter()
            elapsed_time = end_time - start_time
            print(f"Evaluated {self.moves_searched} positions in {elapsed_time:.4f} seconds")
        
        self.selected_move = best_move
        return best_move
        

