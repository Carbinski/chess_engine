import time
import chess

class ChessEngine:
    # ... existing __init__ and other methods ...

    def orderMoves(self, moves: list[chess.Move]) -> list[chess.Move]:
        captures, ignore = [], []
        board, PIECE_WT = self.board, self.pieceWt
        piece_type_at = board.piece_type_at
        is_en_passant = board.is_en_passant
        ep_square = board.ep_square if board.ep_square else -1

        for move in moves:
            victim_type = piece_type_at(move.to_square)
            if victim_type:
                attacker_type = piece_type_at(move.from_square)
                # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
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

        # Generate and order moves
        moves = self.orderMoves(self.board.legal_moves)

        if not moves:
            if self.board.is_checkmate():
                return -1000000 - depth # Prefer faster mates
            return 0 # Stalemate

        max_eval = float("-inf")
        push, pop = self.board.push, self.board.pop

        for move in moves:
            push(move)
            # NegaMax recursive call
            score = -self.search(depth - 1, -beta, -alpha)
            pop()

            if score > max_eval:
                max_eval = score

            alpha = max(alpha, score)
            if alpha >= beta:
                break
        
        return max_eval

    def select_move(self, board: chess.Board, time_limit: float = 2.0) -> chess.Move:  
        self.total_moves += 1 
        self.board = board

        # Random opening book (optional)
        if self.random_opening and self.total_moves < 3:
            return random.choice(list(board.generate_legal_moves()))
        
        start_time = time.time()
        
        # Get all legal moves initially
        moves = list(board.legal_moves)
        
        # We need a default best move in case depth 1 fails or time runs out instantly
        if not moves:
            return None 
        best_global_move = moves[0] 
        best_global_eval = float('-inf')

        # --- ITERATIVE DEEPENING LOOP ---
        # We iterate from depth 1 up to self.depth
        for current_depth in range(1, self.depth + 1):
            
            # Check time: if we exceeded limit, stop searching deeper
            if time.time() - start_time > time_limit:
                break

            # Local variables for this depth iteration
            iteration_best_move = None
            iteration_best_eval = float('-inf')
            alpha = float('-inf')
            beta = float('inf')
            
            # Store scores for sorting next iteration
            move_scores = [] 

            # Root search loop
            for move in moves:
                self.board.push(move)
                
                # Search deeper
                score = -self.search(current_depth - 1, -beta, -alpha)
                
                self.board.pop()
                
                move_scores.append((score, move))

                if score > iteration_best_eval:
                    iteration_best_eval = score
                    iteration_best_move = move
                
                # Update alpha at root (PV node)
                alpha = max(alpha, score)
                
                # OPTIONAL: Check time inside the move loop to return even faster
                if time.time() - start_time > time_limit:
                    break

            # If we finished the full iteration without timing out, update the global best
            if time.time() - start_time <= time_limit:
                best_global_move = iteration_best_move
                best_global_eval = iteration_best_eval
                
                # Sort moves for the NEXT iteration based on scores from THIS iteration
                # This ensures the best move is searched first next time (huge optimization)
                move_scores.sort(key=lambda x: x[0], reverse=True)
                moves = [item[1] for item in move_scores]
                
                print(f"Depth {current_depth} finished. Best: {best_global_move} Eval: {best_global_eval}")
            else:
                print(f"Depth {current_depth} interrupted by time.")

        if self.stat_tracking:
            elapsed = time.time() - start_time
            print(f"FINAL MOVE: {best_global_move} | EVAL: {best_global_eval} | TIME: {elapsed:.3f}")

        return best_global_move