#pragma once

#include "chess.hpp"

class MoveOrdering {
public:
    // MOVE_ORDER_MODE (compile-time):
    //   0 none       — transposition-table move first
    //   1 enpassant  — MVV-LVA, and en passant counts as a pawn capture
    //   2 promotion  — MVV-LVA, and promotions get a bonus
    //   3 either     — MVV-LVA, with both of those checks
    void order_moves(const chess::Board& board, chess::Movelist& moves, chess::Move best);

private:
    void transposition_table_move_first(chess::Movelist& moves, chess::Move best);
};
