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

struct Ply {
    bool white_to_move = false;
    int alpha = 0;
    int beta = 0;
    int best_eval = 0;
    chess::Move best_move = chess::Move::NO_MOVE;

    enum class Result {
        Continue,
        Cutoff,
        Mate
    };

    static Ply start(bool white_to_move, int alpha, int beta, chess::Move best = chess::Move::NO_MOVE) {
        return Ply{white_to_move, alpha, beta, worst_eval(white_to_move), best};
    }

    void apply_eval(int eval, chess::Move move) {
        if (eval_is_better(white_to_move, eval, best_eval)) {
            best_eval = eval;
            best_move = move;
            if (eval_is_better(white_to_move, eval, white_to_move ? alpha : beta)) {
                (white_to_move ? alpha : beta) = eval;
            }
        }
    }

    Result result() const {
        if (beta <= alpha) {
            return Result::Cutoff;
        }
        if (mate_in_one(white_to_move, best_eval)) {
            return Result::Mate;
        }
        return Result::Continue;
    }
};
