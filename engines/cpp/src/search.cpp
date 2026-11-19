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

Helios::Helios() {}

chess::Move Helios::select_move(const chess::Board& board, std::optional<int> time_remaining_ms) {
    start_ = std::chrono::steady_clock::now();
    budget_ms_ = time_remaining_ms.value_or(0) / 75;
    out_of_time_ = false;
    counters_ = {};
    counters_.nodes = 1;  // root; search() and quiescence() count every position below it
    move_ordering_.clear();

    Board position = board;
    set_evaluation(position);

    Movelist moves;
    movegen::legalmoves(moves, position);
    if (moves.empty()) {
        log_completed_search(name(), board, 0, counters_, budget_ms_, out_of_time_, std::nullopt,
                             Move::NO_MOVE, start_);
        return Move::NO_MOVE;
    }

    Move best_move = moves[0];
    std::optional<int> committed_eval;
    int depth_completed = 0;
    const bool white_to_move = position.sideToMove() == Color::WHITE;
    for (int depth = 1; ; ++depth) {
        MoveOrdering::Picker picker = move_ordering_.pick(moves, best_move, position);
        Ply ply = Ply::start(white_to_move, -checkmate_score, checkmate_score, best_move);

        for (int tried = 0;; ++tried) {
            const std::optional<Move> picked = picker.next();
            if (!picked) {
                break;
            }
            const Move move = *picked;
            if (check_time_expired()) {
                break;
            }

            make_move(position, move);
            position.makeMove(move);
            const int eval = with_mate_distance(search(position, depth - 1, ply.alpha, ply.beta));
            position.unmakeMove(move);
            unmake_move(move);
            if (out_of_time_) {
                break;
            }
            ply.apply_eval(eval, move);
            const Ply::Result result = ply.result();
            if (result == Ply::Result::Cutoff) {
                if (tried == 0) {
                    ++counters_.first_cutoffs;
                }
                move_ordering_.record_cutoff(position, picker, depth);
                break;
            }
            if (result == Ply::Result::Mate) {
                break;
            }
        }

        if (out_of_time_) {
            break;
        }
        best_move = ply.best_move;
        committed_eval = ply.best_eval;
        depth_completed = depth;

        if (check_time_expired()) {
            break;
        }
    }

    const bool full_budget = out_of_time_;
    log_completed_search(name(), board, depth_completed, counters_, budget_ms_, full_budget, committed_eval,
                         best_move, start_);
    return best_move;
}

int Helios::search(chess::Board& board, int depth, int alpha, int beta) {
    if (depth == 0) {
        return quiescence(board, alpha, beta);
    }

    ++counters_.nodes;
    if (check_time_expired()) return 0;
    if (is_insufficient_material(board)) return 0;

    Movelist moves;
    movegen::legalmoves(moves, board);
    if (moves.empty()) return mate_or_stalemate(board);
    if (is_path_draw(board)) return 0;

    const std::uint64_t hash = board.hash();
    const TtHit hit = probe_tt(hash, depth, alpha, beta);
    if (hit.cutoff) return *hit.cutoff;

    MoveOrdering::Picker picker = move_ordering_.pick(moves, hit.hash_move, board);

    Ply ply = Ply::start(board.sideToMove() == Color::WHITE, alpha, beta);
    for (int tried = 0;; ++tried) {
        const std::optional<Move> picked = picker.next();
        if (!picked) {
            break;
        }
        const Move move = *picked;
        make_move(board, move);
        board.makeMove(move);
        const int eval = with_mate_distance(search(board, depth - 1, ply.alpha, ply.beta));
        board.unmakeMove(move);
        unmake_move(move);
        if (out_of_time_) {
            return 0;
        }
        ply.apply_eval(eval, move);
        const Ply::Result result = ply.result();
        if (result == Ply::Result::Cutoff) {
            if (tried == 0) {
                ++counters_.first_cutoffs;
            }
            move_ordering_.record_cutoff(board, picker, depth);
            break;
        }
        if (result == Ply::Result::Mate) {
            break;
        }
    }

    store_tt(hash, depth, ply.best_eval, alpha, beta, ply.best_move);
    return ply.best_eval;
}

int Helios::quiescence(Board& board, int alpha, int beta) {
    ++counters_.nodes;
    if (check_time_expired()) return 0;
    if (is_insufficient_material(board)) return 0;

    const bool white_to_move = board.sideToMove() == Color::WHITE;
    const bool in_check = board.inCheck();

    Movelist moves;
    if (in_check) {
        movegen::legalmoves(moves, board);
        if (moves.empty()) return mate_or_stalemate(board);
    }
    if (is_path_draw(board)) return 0;

    Ply ply = Ply::start(white_to_move, alpha, beta);
    if (!in_check) {
        ply.apply_eval(evaluate(board), Move::NO_MOVE);
        if (ply.result() == Ply::Result::Cutoff) {
            return ply.best_eval;
        }
        movegen::legalmoves<movegen::MoveGenType::CAPTURE>(moves, board);
    }

    MoveOrdering::Picker picker = move_ordering_.pick(moves, Move::NO_MOVE, board);
    while (const std::optional<Move> picked = picker.next()) {
        const Move move = *picked;

        make_move(board, move);
        board.makeMove(move);
        const int eval = with_mate_distance(quiescence(board, ply.alpha, ply.beta));
        board.unmakeMove(move);
        unmake_move(move);
        if (out_of_time_) {
            return 0;
        }

        ply.apply_eval(eval, move);
        const Ply::Result result = ply.result();
        if (result == Ply::Result::Cutoff || result == Ply::Result::Mate) {
            break;
        }
    }
    return ply.best_eval;
}

bool Helios::check_time_expired() {
    if (out_of_time_) return true;
    if (counters_.nodes % 2048 != 0) return false;

    const auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now() - start_).count();
    if (elapsed >= budget_ms_) {
        out_of_time_ = true;
    }
    return out_of_time_;
}

Helios::TtHit Helios::probe_tt(std::uint64_t hash, int depth, int& alpha, int& beta) {
    TtHit hit;
    ++counters_.tt_probes;
    if (const std::optional<Entry> entry = transposition_table_.get_position(hash)) {
        ++counters_.tt_hits;
        hit.hash_move = entry->best;
        if (entry->depth >= depth) {
            if (entry->flag == Bound::Exact) {
                ++counters_.tt_cutoffs;
                hit.cutoff = entry->score;
                return hit;
            }
            if (entry->flag == Bound::Lower) alpha = std::max(entry->score, alpha);
            else if (entry->flag == Bound::Upper) beta = std::min(entry->score, beta);
            if (alpha >= beta) {
                ++counters_.tt_cutoffs;
                hit.cutoff = entry->score;
                return hit;
            }
        }
    }
    return hit;
}

void Helios::store_tt(std::uint64_t hash, int depth, int score, int alpha, int beta, chess::Move best) {
    transposition_table_.store_position(Entry{hash, depth, score, bound_of(score, alpha, beta), best});
}

std::string_view Helios::name() const {
    return "Helios";
}
