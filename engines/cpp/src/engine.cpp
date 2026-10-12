#include "engine.hpp"

#include <random>

using namespace chess;

RandomEngine::RandomEngine() : rng_(std::random_device{}()) {}

Move RandomEngine::select_move(const Board& board) {
    Movelist moves;
    movegen::legalmoves(moves, board);
    if (moves.empty()) {
        return Move::NO_MOVE;
    }
    std::uniform_int_distribution<int> pick(0, moves.size() - 1);
    return moves[pick(rng_)];
}

std::string_view RandomEngine::name() const {
    return "Random";
}
