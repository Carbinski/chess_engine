#pragma once

#include "chess.hpp"
#include "evaluate.hpp"

#include <cstdint>
#include <cstring>
#include <optional>

class MoveOrdering {
public:
    class Picker {
    public:
        std::optional<chess::Move> next();

    private:
        friend class MoveOrdering;

        Picker(chess::Movelist& moves, chess::Move previous_best, const chess::Board& board,
               const MoveOrdering& ordering);

        void score_loud();
        void score_quiet();

        chess::Movelist& moves_;
        const chess::Board& board_;
        const MoveOrdering& ordering_;

        chess::Move previous_best_ = chess::Move::NO_MOVE;
        bool yield_previous_best_ = false;

        bool is_loud_sorted_ = false;
        chess::Movelist loud_;
        int loud_index_ = 0;

        bool is_quiet_sorted_ = false;
        chess::Movelist quiet_;
        int quiet_index_ = 0;

        chess::Movelist tried_;
    };

    void clear() {
        std::memset(history_, 0, sizeof(history_));
    }

    Picker pick(chess::Movelist& moves, chess::Move previous_best, const chess::Board& board) const;
    void record_cutoff(const chess::Board& board, const Picker& picker, int depth);

private:
    static constexpr int history_max = 12'000;

    int history_[2][64][64]{};

    static int loud_score(const chess::Board& board, chess::Move move);

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
