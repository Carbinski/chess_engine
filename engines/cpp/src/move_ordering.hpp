#pragma once

#include "chess.hpp"

class MoveOrdering {
public:
    void order_moves(chess::Movelist& moves, chess::Move best);

private:
    void transposition_table_move_first(chess::Movelist& moves, chess::Move best);
};
