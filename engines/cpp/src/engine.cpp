#include "engine.hpp"
#include "evaluate.hpp"

#include <random>
#include <vector>

using namespace chess;

EvalEngine::EvalEngine() : rng_(std::random_device{}()) {}

Move EvalEngine::select_move(const Board& board, std::optional<int>) {
    Movelist moves;
    movegen::legalmoves(moves, board);
    if (moves.empty()) {
        return Move::NO_MOVE;
    }

    int best_score = -1'000'000;
    std::vector<Move> best_moves;

    for (const auto& move : moves) {
        Board position = board;
        position.makeMove(move);
        const int score = position.sideToMove() == Color::BLACK ? evaluate(position) : -evaluate(position);

        if (score > best_score) {
            best_score = score;
            best_moves.clear();
            best_moves.push_back(move);
        } else if (score == best_score) {
            best_moves.push_back(move);
        }
    }

    if (best_moves.empty()) {
        return Move::NO_MOVE;
    }

    std::uniform_int_distribution<int> pick(0, static_cast<int>(best_moves.size()) - 1);
    return best_moves[pick(rng_)];
}

std::string_view EvalEngine::name() const {
    return "Eval";
}
