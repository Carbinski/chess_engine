#pragma once

#include "chess.hpp"
#include "evaluate.hpp"

#include <cstdint>
#include <cstring>

class MoveOrdering {
public:
    void clear() {
        std::memset(history_, 0, sizeof(history_));
    }

    void order_moves(chess::Movelist& moves, chess::Move best, const chess::Board& board);
    void record_cutoff(const chess::Board& board, const chess::Movelist& moves, int cutoff_index, int depth);

private:
    struct ScoreBands {
        static constexpr int history_max = 12'000;
        static constexpr std::int16_t capture_base = 14'000;
        static constexpr std::int16_t prev_best = 0x7FFF;
    };

    int history_[2][64][64]{};

    static bool is_quiet(const chess::Board& board, chess::Move move) {
        if (move.typeOf() == chess::Move::PROMOTION || move.typeOf() == chess::Move::ENPASSANT) {
            return false;
        }
        return board.at(move.to()).type() == chess::PieceType::NONE;
    }

    static int side_index(chess::Color color) {
        return color == chess::Color::WHITE ? 0 : 1;
    }

    void update(chess::Color side, chess::Move move, int bonus);
};
