package org;

import com.github.bhlangonijr.chesslib.Board;
import com.github.bhlangonijr.chesslib.move.Move;

public interface JavaChessBot {
    Move select_move(Board board);
    
    // Default method to support time-aware bots without breaking old ones
    default Move select_move(Board board, long time_left) {
        return select_move(board);
    }
    
    long get_total_time();
    int get_total_moves();
}
