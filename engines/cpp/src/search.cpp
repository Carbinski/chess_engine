#include "search.hpp"
#include "evaluate.hpp"
#include "logging.hpp"
#include "move_ordering.hpp"
#include "search_util.hpp"

#include <algorithm>
#include <exception>
#include <iostream>
#include <optional>

using namespace chess;

namespace {

void log_completed_search(std::string_view engine_name,
                          const Board& board,
                          int depth_completed,
                          const SearchCounters& counters,
                          int budget_ms,
                          bool full_budget,
                          std::optional<int> committed_eval,
                          const Move& move,
                          std::chrono::steady_clock::time_point search_start) {
    logging::SearchStats stats;
    stats.engine = std::string(engine_name);
    stats.side = board.sideToMove() == Color::WHITE ? "w" : "b";
    stats.depth = depth_completed;
    stats.nodes = counters.nodes;
    stats.tt_probes = counters.tt_probes;
    stats.tt_hits = counters.tt_hits;
    stats.tt_cutoffs = counters.tt_cutoffs;
    stats.first_cutoffs = counters.first_cutoffs;
    stats.budget_ms = budget_ms;
    stats.full_budget = full_budget;
    stats.score = committed_eval;
    stats.elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                        std::chrono::steady_clock::now() - search_start)
                        .count();
    if (move != Move::NO_MOVE) {
        stats.move = uci::moveToUci(move);
    }
    if (logging::should_include_fen()) {
        stats.fen = board.getFen();
    }
    logging::log_search(std::move(stats));
}

}

Freya::Freya() {}

bool Freya::check_time_expired() {
    if (out_of_time_) {
        return true;
    }
    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start_).count();
    if (elapsed >= budget_ms_) {
        out_of_time_ = true;
    }
    return out_of_time_;
}

chess::Move Freya::select_move(const chess::Board& board, std::optional<int> time_remaining_ms) {
    start_ = std::chrono::steady_clock::now();
    budget_ms_ = time_remaining_ms.value_or(0) / 75;
    out_of_time_ = false;
    counters_ = {};
    counters_.nodes = 1;  // root; search() counts every position below it
    move_ordering_.clear();

    Board position = board;

    Movelist moves;
    movegen::legalmoves(moves, position);

    Move best_move = Move::NO_MOVE;
    std::optional<int> committed_eval;
    int depth_completed = 0;
    if (!moves.empty()) {
        best_move = moves[0];
        const bool white_to_move = position.sideToMove() == Color::WHITE;
        for (int depth = 1; ; ++depth) {
            move_ordering_.order_moves(moves, best_move, position);

            int best_eval = worst_eval(white_to_move);
            int alpha = -checkmate_score;
            int beta = checkmate_score;
            Move iteration_best = best_move;

            for (int i = 0; i < moves.size(); ++i) {
                const Move& move = moves[i];
                if (check_time_expired()) {
                    break;
                }

                position.makeMove(move);
                const int eval = with_mate_distance(search(position, depth - 1, alpha, beta));
                position.unmakeMove(move);
                if (out_of_time_) {
                    break;
                }
                if (eval_is_better(white_to_move, eval, best_eval)) {
                    best_eval = eval;
                    iteration_best = move;
                    if (eval_is_better(white_to_move, eval, white_to_move ? alpha : beta)) {
                        (white_to_move ? alpha : beta) = eval;
                        if (beta <= alpha) {
                            if (i == 0) {
                                ++counters_.first_cutoffs;
                            }
                            move_ordering_.record_cutoff(position, moves, i, depth);
                            break;
                        }
                    }
                }
                if (mate_in_one(white_to_move, eval)) {
                    break;
                }
            }

            if (out_of_time_) {
                break;
            }
            best_move = iteration_best;
            committed_eval = best_eval;
            depth_completed = depth;

            if (check_time_expired()) {
                break;
            }
        }
    }

    const bool full_budget = out_of_time_;
    log_completed_search(name(), board, depth_completed, counters_, budget_ms_, full_budget, committed_eval,
                         best_move, start_);
    return best_move;
}

int Freya::search(chess::Board& board, int depth, int alpha, int beta) {
    ++counters_.nodes;
    if (check_time_expired()) {
        return 0;
    }
    if (depth == 0) {
        return evaluate(board);
    }

    const std::uint64_t hash = board.hash();
    Move hash_move = Move::NO_MOVE;
    ++counters_.tt_probes;
    if (const std::optional<Entry> entry = transposition_table_.get_position(hash)) {
        ++counters_.tt_hits;
        hash_move = entry->best;
        if (entry->depth >= depth) {
            if (entry->flag == Bound::Exact) {
                ++counters_.tt_cutoffs;
                return entry->score;
            }
            if (entry->flag == Bound::Lower) alpha = std::max(entry->score, alpha);
            else if (entry->flag == Bound::Upper) beta = std::min(entry->score, beta);
            if (alpha >= beta) {
                ++counters_.tt_cutoffs;
                return entry->score;
            }
        }
    }

    Movelist moves;
    movegen::legalmoves(moves, board);
    if (moves.empty()) {
        return evaluate_game_over(board);
    }
    move_ordering_.order_moves(moves, hash_move, board);

    const int original_alpha = alpha;
    const int original_beta = beta;
    const bool white_to_move = board.sideToMove() == Color::WHITE;
    int best_eval = worst_eval(white_to_move);
    Move best_move = Move::NO_MOVE;

    for (int i = 0; i < moves.size(); ++i) {
        const Move& move = moves[i];
        board.makeMove(move);
        const int eval = with_mate_distance(search(board, depth - 1, alpha, beta));
        board.unmakeMove(move);
        if (out_of_time_) {
            return 0;
        }

        if (eval_is_better(white_to_move, eval, best_eval)) {
            best_eval = eval;
            best_move = move;
            if (eval_is_better(white_to_move, eval, white_to_move ? alpha : beta)) {
                (white_to_move ? alpha : beta) = eval;
                if (beta <= alpha) {
                    if (i == 0) {
                        ++counters_.first_cutoffs;
                    }
                    move_ordering_.record_cutoff(board, moves, i, depth);
                    break;
                }
            }
        }
        if (mate_in_one(white_to_move, eval)) {
            break;
        }
    }

    Bound bound = Bound::Exact;
    if (best_eval <= original_alpha) {
        bound = Bound::Upper;
    } else if (best_eval >= original_beta) {
        bound = Bound::Lower;
    }
    transposition_table_.store_position(Entry{hash, depth, best_eval, bound, best_move});
    return best_eval;
}

std::string_view Freya::name() const {
    return "Freya";
}
