#pragma once

#include "chess.hpp"
#include "evaluate.hpp"

#include <cstdint>

class MoveOrdering {
public:
    void order_moves(chess::Movelist& moves, chess::Move best, const chess::Board& board);

private:
    struct ScoreBands {
        static constexpr std::int16_t prev_best = 0x7FFF;
    };
};
