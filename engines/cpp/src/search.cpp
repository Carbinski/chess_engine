#include "search.hpp"
#include "evaluate.hpp"
#include "logging.hpp"

#include <exception>
#include <iostream>

using namespace chess;

namespace {

void log_completed_search(std::string_view engine_name,
                          const Board& board,
                          int depth_completed,
                          std::uint64_t nodes,
                          int budget_ms,
                          bool full_budget,
                          std::optional<int> committed_eval,
                          const Move& move,
                          std::chrono::steady_clock::time_point search_start) {
    try {
        logging::SearchStats stats;
        stats.engine = std::string(engine_name);
        stats.side = board.sideToMove() == Color::WHITE ? "w" : "b";
        stats.depth = depth_completed;
        stats.nodes = nodes;
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
    } catch (const std::exception& ex) {
        std::cerr << "logging failed: " << ex.what() << '\n';
    } catch (...) {
        std::cerr << "logging failed\n";
    }
}

}

bool eval_is_better(bool white_to_move, int eval, int best_eval) {
    if (white_to_move) {
        return eval > best_eval;
    }
    return eval < best_eval;
}

TreeSearch::TreeSearch() {}

bool TreeSearch::check_time_expired() {
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

chess::Move TreeSearch::select_move(const chess::Board& board, std::optional<int> time_remaining_ms) {
    start_ = std::chrono::steady_clock::now();
    budget_ms_ = time_remaining_ms.value_or(0) / 75;
    out_of_time_ = false;
    nodes_ = 1;  // root; search() counts every position below it

    Movelist moves;
    movegen::legalmoves(moves, board);

    Move best_move = Move::NO_MOVE;
    std::optional<int> committed_eval;
    int depth_completed = 0;
    if (!moves.empty()) {
        best_move = moves[0];
        const bool white_to_move = board.sideToMove() == Color::WHITE;
        for (int depth = 1; ; ++depth) {
            int best_eval = white_to_move ? -1'000'000 : 1'000'000;
            int alpha = -1'000'000;
            int beta = 1'000'000;
            Move iteration_best = best_move;

            for (const auto& move : moves) {
                if (check_time_expired()) {
                    break;
                }

                Board position = board;
                position.makeMove(move);
                const int eval = search(position, depth - 1, alpha, beta);
                if (out_of_time_) {
                    break;
                }
                if (eval_is_better(white_to_move, eval, best_eval)) {
                    best_eval = eval;
                    iteration_best = move;
                    if (eval_is_better(white_to_move, eval, white_to_move ? alpha : beta)) {
                        (white_to_move ? alpha : beta) = eval;
                        if (beta <= alpha) {
                            break;
                        }
                    }
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
    log_completed_search(name(), board, depth_completed, nodes_, budget_ms_, full_budget, committed_eval,
                         best_move, start_);
    return best_move;
}

int TreeSearch::search(chess::Board& board, int depth, int alpha, int beta) {
    ++nodes_;
    if (check_time_expired()) {
        return 0;
    }
    if (depth == 0) {
        return evaluate(board);
    }

    Movelist moves;
    movegen::legalmoves(moves, board);
    Board position = board;

    if (moves.empty()) {
        return evaluate(board);
    }

    const bool white_to_move = board.sideToMove() == Color::WHITE;
    int best_eval = white_to_move ? -1'000'000 : 1'000'000;

    for (const auto& move : moves) {
        position.makeMove(move);
        int eval = search(position, depth - 1, alpha, beta);
        position.unmakeMove(move);
        if (out_of_time_) {
            return 0;
        }

        if (eval_is_better(white_to_move, eval, best_eval)) {
            best_eval = eval;
            if (eval_is_better(white_to_move, eval, white_to_move ? alpha : beta)) {
                (white_to_move ? alpha : beta) = eval;
                if (beta <= alpha) {
                    break;
                }
            }
        }
    }

    return best_eval;
}

std::string_view TreeSearch::name() const {
    return "TreeSearch";
}
