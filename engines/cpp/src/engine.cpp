#include "engine.hpp"

using namespace chess;

SearchEngine::SearchEngine() = default;

Move SearchEngine::select_move(const Board& board, std::optional<int> time_remaining_ms) {
    return search_.select_move(board, time_remaining_ms);
}

std::string_view SearchEngine::name() const {
    return "Search";
}
