#include "search.hpp"
#include "evaluate.hpp"

using namespace chess;

bool score_is_better(bool white_to_move, int score, int best_score) {
    if (white_to_move) {
        return score > best_score;
    }
    return score < best_score;
}

BasicSearch::BasicSearch() {}

bool BasicSearch::check_time_expired() {
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

chess::Move BasicSearch::select_move(const chess::Board& board, std::optional<int> time_remaining_ms) {
    start_ = std::chrono::steady_clock::now();
    budget_ms_ = time_remaining_ms.value_or(0) / 75;
    out_of_time_ = false;

    Movelist moves;
    movegen::legalmoves(moves, board);
    if (moves.empty()) {
        return chess::Move::NO_MOVE;
    }

    Move best_move = moves[0];
    const bool white_to_move = board.sideToMove() == Color::WHITE;
    for (int depth = 1; ; ++depth) {
        int best_score = white_to_move ? -1'000'000 : 1'000'000;
        Move iteration_best = best_move;

        for (const auto& move : moves) {
            if (check_time_expired()) {
                break;
            }

            Board position = board;
            position.makeMove(move);
            const int score = search(position, depth - 1);
            if (out_of_time_) {
                break;
            }
            if (score_is_better(white_to_move, score, best_score)) {
                best_score = score;
                iteration_best = move;
            }
        }

        if (out_of_time_) {
            break;
        }
        best_move = iteration_best;

        if (check_time_expired()) {
            break;
        }
    }

    return best_move;
}

int BasicSearch::search(chess::Board& board, int depth) {
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
    int best_score = white_to_move ? -1'000'000 : 1'000'000;

    for (const auto& move : moves) {
        position.makeMove(move);
        int score = search(position, depth - 1);
        position.unmakeMove(move);
        if (out_of_time_) {
            return 0;
        }

        if (score_is_better(white_to_move, score, best_score)) {
            best_score = score;
        }
    }

    return best_score;
}

std::string_view BasicSearch::name() const {
    return "BasicSearch";
}
