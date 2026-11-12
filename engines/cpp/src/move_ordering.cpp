#include "move_ordering.hpp"

#include <utility>

void MoveOrdering::order_moves(chess::Movelist& moves, chess::Move best) {
    transposition_table_move_first(moves, best);
}

void MoveOrdering::transposition_table_move_first(chess::Movelist& moves, chess::Move best) {
    if (best == chess::Move::NO_MOVE) {
        return;
    }
    for (int i = 1; i < moves.size(); ++i) {
        if (moves[i] == best) {
            std::swap(moves[0], moves[i]);
            return;
        }
    }
}
