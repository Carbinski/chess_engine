package org;

import com.github.bhlangonijr.chesslib.*;
import com.github.bhlangonijr.chesslib.move.Move;

import java.util.List;
import java.util.Random;

import support.TranspositionTable;

/**
 * Bot_V2 : A lot of marginal improvements on speed
 * New Features:
 * 1. Buffers --> Limit Garbage Collector usage
 * 2. Enhanced Delta Move --> Slightly faster
 * 3. Added En-Passant to LVA-MVV
 */
public class Bot_V2 implements JavaChessBot {
    Board board;
    int depth;

    boolean stat_tracking;
    boolean random_opening;

    int total_moves = 0;
    long total_time = 0;

    private static final int IDX_MAT = 0;
    private static final int IDX_MG = 1;
    private static final int IDX_EG = 2;

    private final int[] delta_buffer = new int[3];
    private final int[][] sort_buffers = new int[64][256]; // Assumes Max Depth of 64 and max 256 moves per position

    TranspositionTable tt = new TranspositionTable(2000000);

    int[] mg_pawn_table   = {0,0,0,0,0,0,0,0,-35,-1,-20,-23,-15,24,38,-22,-26,-4,-4,-10,3,3,33,-12,-27,-2,-5,12,17,6,10,-25,-14,13,6,21,23,12,17,-23,-6,7,26,31,65,56,25,-20,98,134,61,95,68,126,34,-11,0,0,0,0,0,0,0,0};
    int[] eg_pawn_table   = {0,0,0,0,0,0,0,0,13,8,8,10,13,0,2,-7,4,7,-6,1,0,-5,-1,-8,13,9,-3,-7,-7,-8,3,-1,32,24,13,5,-2,4,17,17,94,100,85,67,56,53,82,84,178,173,158,134,147,132,165,187,0,0,0,0,0,0,0,0,};
    int[] mg_knight_table = {-105,-21,-58,-33,-17,-28,-19,-23,-29,-53,-12,-3,-1,18,-14,-19,-23,-9,12,10,19,17,25,-16,-13,4,16,13,28,19,21,-8,-9,17,19,53,37,69,18,22,-47,60,37,65,84,129,73,44,-73,-41,72,36,23,62,7,-17,-167,-89,-34,-49,61,-97,-15,-107,};
    int[] eg_knight_table = {-29,-51,-23,-15,-22,-18,-50,-64,-42,-20,-10,-5,-2,-20,-23,-44,-23,-3,-1,15,10,-3,-20,-22,-18,-6,16,25,16,17,4,-18,-17,3,22,22,22,11,8,-18,-24,-20,10,9,-1,-9,-19,-41,-25,-8,-25,-2,-9,-25,-24,-52,-58,-38,-13,-28,-31,-27,-63,-99,};
    int[] mg_bishop_table = {-33,-3,-14,-21,-13,-12,-39,-21,4,15,16,0,7,21,33,1,0,15,15,15,14,27,18,10,-6,13,13,26,34,12,10,4,-4,5,19,50,37,37,7,-2,-16,37,43,40,35,50,37,-2,-26,16,-18,-13,30,59,18,-47,-29,4,-82,-37,-25,-42,7,-8,};
    int[] eg_bishop_table = {-23,-9,-23,-5,-9,-16,-5,-17,-14,-18,-7,-1,4,-9,-15,-27,-12,-3,8,10,13,3,-7,-15,-6,3,13,19,7,10,-3,-9,-3,9,12,9,14,10,3,2,2,-8,0,-1,-2,6,0,4,-8,-4,7,-12,-3,-13,-4,-14,-14,-21,-11,-8,-7,-9,-17,-24,};
    int[] mg_rook_table   = {-19,-13,1,17,16,7,-37,-26,-44,-16,-20,-9,-1,11,-6,-71,-45,-25,-16,-17,3,0,-5,-33,-36,-26,-12,-1,9,-7,6,-23,-24,-11,7,26,24,35,-8,-20,-5,19,26,36,17,45,61,16,27,32,58,62,80,67,26,44,32,42,32,51,63,9,31,43,};
    int[] eg_rook_table   = {-9,2,3,-1,-5,-13,4,-20,-6,-6,0,2,-9,-9,-11,-3,-4,0,-5,-1,-7,-12,-8,-16,3,5,8,4,-5,-6,-8,-11,4,3,13,1,2,1,-1,2,7,7,7,5,4,-3,-5,-3,11,13,13,11,-3,3,8,3,13,10,18,15,12,12,8,5,};
    int[] mg_queen_table  = {-1,-18,-9,10,-15,-25,-31,-50,-35,-8,11,2,8,15,-3,1,-14,2,-11,-2,-5,2,14,5,-9,-26,-9,-10,-2,-4,3,-3,-27,-27,-16,-16,-1,17,-2,1,-13,-17,7,8,29,56,47,57,-24,-39,-5,1,-16,57,28,54,-28,0,29,12,59,44,43,45,};
    int[] eg_queen_table  = {-33,-28,-22,-43,-5,-32,-20,-41,-22,-23,-30,-16,-16,-23,-36,-32,-16,-27,15,6,9,17,10,5,-18,28,19,47,31,34,39,23,3,22,24,45,57,40,57,36,-20,6,9,49,47,35,19,9,-17,20,32,41,58,25,30,0,-9,22,22,27,27,19,10,20,};
    int[] mg_king_table   = {-15,36,12,-54,8,-28,24,14,1,7,-8,-64,-43,-16,9,8,-14,-14,-22,-46,-44,-30,-15,-27,-49,-1,-27,-39,-46,-44,-33,-51,-17,-20,-12,-27,-30,-25,-14,-36,-9,24,2,-16,-20,6,22,-22,29,-1,-20,-7,-8,-4,-38,-29,-65,23,16,-15,-56,-34,2,13,};
    int[] eg_king_table   = {-53,-34,-21,-11,-28,-14,-24,-43,-27,-11,4,13,14,4,-5,-17,-19,-3,11,21,23,16,7,-9,-18,-4,21,24,27,23,9,-11,-8,22,24,27,26,33,26,3,10,17,23,15,20,45,44,13,-12,17,14,17,17,38,23,11,-74,-35,-18,-18,-11,15,4,-17,};

    int[] piece_values = {0, 100, 300, 300, 500, 900, 20000};
    int[][] mg_tables = {null, mg_pawn_table, mg_knight_table, mg_bishop_table, mg_rook_table, mg_queen_table, mg_king_table};
    int[][] eg_tables = {null, eg_pawn_table, eg_knight_table, eg_bishop_table, eg_rook_table, eg_queen_table, eg_king_table};


    public Bot_V2(int depth, boolean stat_tracking, boolean random_opening) {
        this.depth = depth;
        this.stat_tracking = stat_tracking;
        this.random_opening = random_opening;
    }

    private double get_phase() {
        double current_material = (
                (Long.bitCount(board.getBitboard(Piece.WHITE_KNIGHT)) + Long.bitCount(board.getBitboard(Piece.BLACK_KNIGHT))) * piece_values[2] +
                        (Long.bitCount(board.getBitboard(Piece.WHITE_BISHOP)) + Long.bitCount(board.getBitboard(Piece.BLACK_BISHOP))) * piece_values[3] +
                        (Long.bitCount(board.getBitboard(Piece.WHITE_ROOK))   + Long.bitCount(board.getBitboard(Piece.BLACK_ROOK)))   * piece_values[4] +
                        (Long.bitCount(board.getBitboard(Piece.WHITE_QUEEN))  + Long.bitCount(board.getBitboard(Piece.BLACK_QUEEN)))  * piece_values[5]
        );

        double max_material = 6200.0;
        double phase = current_material / max_material;
        return Math.max(0.0, Math.min(1.0, phase));
    }

    private int get_move_id(Move move) {
        return move.hashCode() & 0xFFFFFF;
    }

    private int get_psqt_index (Piece piece) {
        PieceType pt = piece.getPieceType();
        if (pt == PieceType.NONE) return 0;
        return pt.ordinal() + 1;
    }

    private int get_psqt_tbl_index (Piece piece, int square_idx) {
        return (piece.getPieceSide() == Side.WHITE) ? square_idx : (square_idx ^ 56);
    }

    private int[] evaluate_split() {
        int mat = 0;
        int mg = 0;
        int eg = 0;

        for (PieceType pt : PieceType.values()) {
            if (pt == PieceType.NONE) continue;

            int index = pt.ordinal() + 1;
            int value = piece_values[index];

            long whitePieces = board.getBitboard(Piece.make(Side.WHITE, pt));
            long blackPieces = board.getBitboard(Piece.make(Side.BLACK, pt));

            while (whitePieces != 0L) {
                int square = Long.numberOfTrailingZeros(whitePieces);
                mat += value;
                mg += mg_tables[index][square];
                eg += eg_tables[index][square];
                whitePieces &= (whitePieces - 1);
            }

            while (blackPieces != 0L) {
                int square = Long.numberOfTrailingZeros(blackPieces);
                mat -= value;
                mg -= mg_tables[index][square];
                eg -= eg_tables[index][square];
                blackPieces &= (blackPieces - 1);
            }
        }
        return new int[] {mat, mg, eg};
    }

    private int get_final_score(int mat, int mg, int eg) {
        double phase = get_phase();
        double eg_phase = 1 - phase;

        int score = (int) (mat + (phase * mg) + (eg_phase * eg));
        return (board.getSideToMove() == Side.WHITE) ? score : -score;
    }

    private void delta_move(Move move) {
        Piece moving_piece = board.getPiece(move.getFrom());
        Piece captured_piece = board.getPiece(move.getTo());

        int dt_mat = 0;
        int dt_mg = 0;
        int dt_eg = 0;

        int moving_idx = get_psqt_index(moving_piece);
        int from_tbl_idx = get_psqt_tbl_index(moving_piece, move.getFrom().ordinal());
        int to_tbl_idx = get_psqt_tbl_index(moving_piece, move.getTo().ordinal());

        if (moving_piece.getPieceSide() == Side.WHITE) {
            dt_mg -= mg_tables[moving_idx][from_tbl_idx];
            dt_eg -= eg_tables[moving_idx][from_tbl_idx];
            dt_mg += mg_tables[moving_idx][to_tbl_idx];
            dt_eg += eg_tables[moving_idx][to_tbl_idx];
        } else {
            dt_mg += mg_tables[moving_idx][from_tbl_idx];
            dt_eg += eg_tables[moving_idx][from_tbl_idx];
            dt_mg -= mg_tables[moving_idx][to_tbl_idx];
            dt_eg -= eg_tables[moving_idx][to_tbl_idx];
        }

        if (captured_piece != Piece.NONE) {
            int val_captured = piece_values[captured_piece.getPieceType().ordinal() + 1];
            int captured_idx = get_psqt_index(captured_piece);
            int captured_tbl_idx = get_psqt_tbl_index(captured_piece, move.getTo().ordinal());

            if (captured_piece.getPieceSide() == Side.WHITE) {
                dt_mat -= val_captured;
                dt_mg -= mg_tables[captured_idx][captured_tbl_idx];
                dt_eg -= eg_tables[captured_idx][captured_tbl_idx];
            } else {
                dt_mat += val_captured;
                dt_mg += mg_tables[captured_idx][captured_tbl_idx];
                dt_eg += eg_tables[captured_idx][captured_tbl_idx];
            }
        }

        boolean isPawn = moving_piece.getPieceType() == PieceType.PAWN;
        boolean isPromotionRank = (moving_piece.getPieceSide() == Side.WHITE && move.getTo().getRank() == Rank.RANK_8) ||
                (moving_piece.getPieceSide() == Side.BLACK && move.getTo().getRank() == Rank.RANK_1);

        if (isPawn && isPromotionRank && move.getPromotion() != Piece.NONE) {
            int val_promo = piece_values[move.getPromotion().getPieceType().ordinal() + 1];
            Piece promoPiece = Piece.make(Side.WHITE, move.getPromotion().getPieceType());
            int promo_idx = get_psqt_index(promoPiece);

            if (moving_piece.getPieceSide() == Side.WHITE) {
                dt_mat -= piece_values[PieceType.PAWN.ordinal() + 1];
                dt_mg -= mg_tables[moving_idx][to_tbl_idx]; // Remove pawn positional
                dt_eg -= eg_tables[moving_idx][to_tbl_idx];

                dt_mat += val_promo;
                dt_mg += mg_tables[promo_idx][to_tbl_idx];
                dt_eg += eg_tables[promo_idx][to_tbl_idx];
            } else {
                dt_mat += piece_values[PieceType.PAWN.ordinal() + 1]; // Remove negative pawn
                dt_mg += mg_tables[moving_idx][to_tbl_idx];
                dt_eg += eg_tables[moving_idx][to_tbl_idx];

                dt_mat -= val_promo;
                dt_mg -= mg_tables[promo_idx][to_tbl_idx];
                dt_eg -= eg_tables[promo_idx][to_tbl_idx];
            }
        }

        // Castling Logic
        if (moving_piece.getPieceType() == PieceType.KING &&
                Math.abs(move.getFrom().ordinal() - move.getTo().ordinal()) == 2) {

            Piece rookPiece = null;
            int rookItemFrom = -1;
            int rookItemTo = -1;

            if (move.getTo() == Square.G1) { // White Short
                rookPiece = Piece.WHITE_ROOK;
                rookItemFrom = Square.H1.ordinal();
                rookItemTo = Square.F1.ordinal();
            } else if (move.getTo() == Square.C1) { // White Long
                rookPiece = Piece.WHITE_ROOK;
                rookItemFrom = Square.A1.ordinal();
                rookItemTo = Square.D1.ordinal();
            } else if (move.getTo() == Square.G8) { // Black Short
                rookPiece = Piece.BLACK_ROOK;
                rookItemFrom = Square.H8.ordinal();
                rookItemTo = Square.F8.ordinal();
            } else if (move.getTo() == Square.C8) { // Black Long
                rookPiece = Piece.BLACK_ROOK;
                rookItemFrom = Square.A8.ordinal();
                rookItemTo = Square.D8.ordinal();
            }

            if (rookPiece != null) {
                int r_idx = get_psqt_index(rookPiece);
                int r_from_idx = get_psqt_tbl_index(rookPiece, rookItemFrom);
                int r_to_idx = get_psqt_tbl_index(rookPiece, rookItemTo);

                if (rookPiece.getPieceSide() == Side.WHITE) {
                    dt_mg -= mg_tables[r_idx][r_from_idx];
                    dt_eg -= eg_tables[r_idx][r_from_idx];
                    dt_mg += mg_tables[r_idx][r_to_idx];
                    dt_eg += eg_tables[r_idx][r_to_idx];
                } else {
                    dt_mg += mg_tables[r_idx][r_from_idx];
                    dt_eg += eg_tables[r_idx][r_from_idx];
                    dt_mg -= mg_tables[r_idx][r_to_idx];
                    dt_eg -= eg_tables[r_idx][r_to_idx];
                }
            }
        }

        // En Passant Logic
        if (moving_piece.getPieceType() == PieceType.PAWN &&
                move.getFrom().getFile() != move.getTo().getFile() &&
                captured_piece == Piece.NONE) {

            int captured_sq_idx;
            if (moving_piece.getPieceSide() == Side.WHITE) {
                captured_sq_idx = move.getTo().ordinal() - 8;
            } else {
                captured_sq_idx = move.getTo().ordinal() + 8;
            }

            Piece ep_captured_piece = (moving_piece.getPieceSide() == Side.WHITE) ? Piece.BLACK_PAWN : Piece.WHITE_PAWN;
            int val_captured = piece_values[PieceType.PAWN.ordinal() + 1];
            int idx_captured = get_psqt_index(ep_captured_piece);
            int tbl_captures = get_psqt_tbl_index(ep_captured_piece, captured_sq_idx);

            if (moving_piece.getPieceSide() == Side.WHITE) {
                dt_mat += val_captured;
                dt_mg += mg_tables[idx_captured][tbl_captures];
                dt_eg += eg_tables[idx_captured][tbl_captures];
            } else {
                dt_mat -= val_captured;
                dt_mg -= mg_tables[idx_captured][tbl_captures];
                dt_eg -= eg_tables[idx_captured][tbl_captures];
            }
        }

        delta_buffer[0] = dt_mat;
        delta_buffer[1] = dt_mg;
        delta_buffer[2] = dt_eg;
    }

    /**
     * LVA-MVV
     * @param moves - unordered list of moves
     * @return Ordered moves based on LVA-MVV. Index 0: Captures, Index 1: Quiet Moves
     */
    private List<Move> order_moves(List<Move> moves, int ply) {
        int n = moves.size();

        if (ply >= 64) ply = 63;
        int[] capture_scores = sort_buffers[ply];

        // Rate moves by LVA-MVV
        for (int i = 0; i < n; i++) {
            Move move = moves.get(i);
            Piece victim = board.getPiece(move.getTo());

            int score = 0;
            Piece attacker = board.getPiece(move.getFrom());

            if (victim != Piece.NONE) {
                score = (10 * piece_values[victim.getPieceType().ordinal() + 1]
                        - piece_values[attacker.getPieceType().ordinal() + 1]);
            } else if (attacker.getPieceType() == PieceType.PAWN &&
                    move.getFrom().getFile() != move.getTo().getFile()) {
                score = (10 * piece_values[PieceType.PAWN.ordinal() + 1])
                        - piece_values[PieceType.PAWN.ordinal() + 1];
            }
            capture_scores[i] = score;
        }

        // In-place selection sort
        for (int i = 0; i < n - 1; i++) {
            int bestIdx = i;
            for (int j = i + 1; j < n; j++) {
                if (capture_scores[j] > capture_scores[bestIdx]) {
                    bestIdx = j;
                }
            }

            // Swap scores
            int tempScore = capture_scores[i];
            capture_scores[i] = capture_scores[bestIdx];
            capture_scores[bestIdx] = tempScore;

            // Swap moves
            Move tempMove = moves.get(i);
            moves.set(i, moves.get(bestIdx));
            moves.set(bestIdx, tempMove);
        }

        return moves;
    }

    private int quiesence_search(int alpha, int beta, int mat, int mg, int eg, int ply) {
        int stand_pat = get_final_score(mat, mg, eg); // Stand Pat: No capture
        if (stand_pat >= beta) return beta;
        if (alpha < stand_pat) alpha = stand_pat;

        List<Move> capture_moves = order_moves(board.pseudoLegalCaptures(), ply + 1);

        for (Move move: capture_moves) {
            delta_move(move);

            if (!board.doMove(move)) {
                continue; // Move was illegal
            }

            int score = - quiesence_search(-beta, -alpha,
                    mat + delta_buffer[0],
                    mg + delta_buffer[1],
                    eg + delta_buffer[2],
                    ply + 1
            );
            board.undoMove();

            if (score >= beta) return beta;
            if (score > alpha) alpha = score;
        }

        return alpha;
    }

    private int search(int depth, int alpha, int beta, int mat, int mg, int eg, int ply) {
        long zobrist_key = board.getZobristKey();

        TranspositionTable.TTEntry entry = tt.probe(zobrist_key);
        int tt_move_id = -1;

        if (entry != null) {
            int tt_depth = entry.depth();
            int tt_score = entry.score();
            int tt_flag = entry.flag();
            tt_move_id = entry.move();

            if (tt_depth >= depth) {
                // 0: Exact, 1: Lower_Bound, 2: Upper_Bound
                if (tt_flag == 0) return tt_score;
                else if (tt_flag == 1 && tt_score >= beta) return tt_score;
                else if (tt_flag == 2 && tt_score <= alpha) return tt_score;
            }
        }

        if (depth <= 0) return quiesence_search(alpha, beta, mat, mg, eg, ply);

        List<Move> moves = board.legalMoves();
        if (moves == null || moves.isEmpty()) {
            if (board.isMated()) return -1000000 - depth;
            return 0;
        }

        List<Move> ordered_moves = order_moves(moves, ply);

        if (tt_move_id != -1) {
            for (int i = 0; i < ordered_moves.size(); i++) {
                Move m = ordered_moves.get(i);
                if (get_move_id(m) == tt_move_id) {
                    ordered_moves.set(i, ordered_moves.getFirst());
                    ordered_moves.set(0, m);
                    break;
                }
            }
        }

        int max_score = -2000000;
        Move best_move = null;
        int alpha_orig = alpha;

        for (Move move : ordered_moves) {
            delta_move(move);

            board.doMove(move);
            int score = - search(depth - 1, -beta, -alpha,
                    mat + delta_buffer[0],
                    mg + delta_buffer[1],
                    eg + delta_buffer[2],
                    ply + 1
            );
            board.undoMove();

            if (score > max_score) {
                max_score = score;
                best_move = move;
            }

            alpha = Math.max(alpha, score);
            if (alpha >= beta) {
                break;
            }
        }

        int flag = 0;
        if (max_score <= alpha_orig) flag = 2;
        else if (max_score >= beta) flag = 1;

        int best_move_id = (best_move != null) ? get_move_id(best_move) : 0;

        tt.store(zobrist_key, depth, max_score, flag, best_move_id);

        return max_score;
    }

    @Override
    public Move select_move(Board board) {
        long start_time = 0;
        if (stat_tracking) {
            total_moves += 1;
            start_time = System.currentTimeMillis();
        }

        List<Move> legal_moves = board.legalMoves();

        // Parse FEN to get the Full Move Number (Last field in FEN string)
        String[] fenParts = board.getFen().split(" ");
        int fullMoveNumber = Integer.parseInt(fenParts[5]);

        if (random_opening && fullMoveNumber < 3 && !legal_moves.isEmpty()) {
            return legal_moves.get(new Random().nextInt(legal_moves.size()));
        }

        this.board = board;

        int[] initial_scores = evaluate_split();
        int root_mat = initial_scores[IDX_MAT];
        int root_mg  = initial_scores[IDX_MG];
        int root_eg  = initial_scores[IDX_EG];

        Move global_best_move = null;

        for (int curr_depth = 1; curr_depth <= this.depth; curr_depth++) {
            int iter_best_score = -2000000;
            Move iter_best_move = null;
            int alpha = -2000000;
            int beta = 2000000;

            List<Move> ordered_moves = order_moves(legal_moves, 0);

            if (global_best_move != null) {
                // Try the Best Move from the PREVIOUS iteration first (PV Move)
                ordered_moves.remove(global_best_move);
                ordered_moves.addFirst(global_best_move);
            }

            // TODO: add time management
            int time_limit = Integer.MAX_VALUE;
            boolean time_abort = false;

            for (Move move : ordered_moves) {
                if (System.currentTimeMillis() - start_time > time_limit) {
                    time_abort = true;
                    break;
                }

                delta_move(move);
                this.board.doMove(move);

                int score = - search(
                        curr_depth - 1, -beta, -alpha,
                        root_mat + delta_buffer[0],
                        root_mg + delta_buffer[1],
                        root_eg + delta_buffer[2],
                        1
                );

                this.board.undoMove();

                if (score > iter_best_score) {
                    iter_best_score = score;
                    iter_best_move = move;
                }
                alpha = Math.max(alpha, score);
            }

            if (time_abort) {
                System.out.println("Time up! Aborting depth " + curr_depth);
                break;
            }

            global_best_move = iter_best_move;
        }

        if (stat_tracking) {
            long end_time = System.currentTimeMillis();
            long time_taken = end_time - start_time;
            total_time += time_taken;
        }

        if (global_best_move != null) { return global_best_move;}
        return legal_moves.get(new Random().nextInt(legal_moves.size()));
    }

    @Override
    public long get_total_time() { return total_time; }

    @Override
    public int get_total_moves() { return total_moves; }
}