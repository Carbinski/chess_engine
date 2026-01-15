package org;

import com.github.bhlangonijr.chesslib.Board;
import com.github.bhlangonijr.chesslib.move.Move;

public interface JavaChessBot {
    Move select_move(Board board);
    long get_total_time();
    int get_total_moves();
}
