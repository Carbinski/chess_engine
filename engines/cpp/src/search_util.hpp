#pragma once

#include "evaluate.hpp"

inline int with_mate_distance(int eval) {
    constexpr int minimum_checkmate_score = checkmate_score - 100'000;
    if (eval > minimum_checkmate_score) {
        return eval - 1;
    }
    if (eval < -minimum_checkmate_score) {
        return eval + 1;
    }
    return eval;
}

inline bool mate_in_one(bool white_to_move, int eval) {
    return white_to_move ? eval >= checkmate_score - 1 : eval <= -(checkmate_score - 1);
}

inline int worst_eval(bool white_to_move) {
    return white_to_move ? -checkmate_score : checkmate_score;
}

inline bool eval_is_better(bool white_to_move, int eval, int best_eval) {
    if (white_to_move) {
        return eval > best_eval;
    }
    return eval < best_eval;
}
