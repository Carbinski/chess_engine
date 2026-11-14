#include "move_ordering.hpp"

#include <algorithm>
#include <cstdlib>

namespace {

void sort(chess::Movelist& moves) {
    std::stable_sort(moves.begin(), moves.end(), [](const chess::Move& a, const chess::Move& b) {
        return a.score() > b.score();
    });
}

}

MoveOrdering::Picker MoveOrdering::pick(chess::Movelist& moves, chess::Move previous_best,
                                        const chess::Board& board) const {
    return Picker(moves, previous_best, board, *this);
}

MoveOrdering::Picker::Picker(chess::Movelist& moves, chess::Move previous_best, const chess::Board& board, const MoveOrdering& ordering) {
    const int side = side_index(board.sideToMove());
    for (int i = 0; i < moves.size(); ++i) {
        chess::Move move = moves[i];
        if (previous_best != chess::Move::NO_MOVE && move == previous_best) {
            previous_best_ = move;
            yield_previous_best_ = true;
            previous_best_index_ = i;
        }
        else if (is_quiet(board, move)) {
            move.setScore(static_cast<std::int16_t>(ordering.history_[side][move.from().index()][move.to().index()]));
            quiet_.add(move);
        } else {
            move.setScore(static_cast<std::int16_t>(loud_score(board, move)));
            loud_.add(move);
        }
    }
}

std::optional<chess::Move> MoveOrdering::Picker::next() {
    std::optional<chess::Move> move;
    if (yield_previous_best_) {
        yield_previous_best_ = false;
        move = previous_best_;
    } else if (loud_index_ < loud_.size()) {
        if (!is_loud_sorted_) {
            sort(loud_);
            is_loud_sorted_ = true;
        }
        move = loud_[loud_index_++];
    } else if (quiet_index_ < quiet_.size()) {
        if (!is_quiet_sorted_) {
            sort(quiet_);
            is_quiet_sorted_ = true;
        }
        move = quiet_[quiet_index_++];
    }

    if (move) {
        tried_.add(*move);
    }
    return move;
}

int MoveOrdering::loud_score(const chess::Board& board, chess::Move move) {
    chess::PieceType victim = board.at(move.to()).type();
    if (move.typeOf() == chess::Move::ENPASSANT) {
        victim = chess::PieceType::PAWN;
    }

    const bool promotion = move.typeOf() == chess::Move::PROMOTION;
    const chess::PieceType attacker = board.at(move.from()).type();
    const int promoted = promotion ? piece_value(move.promotionType()) - 1 : 0;
    return 10 * (piece_value(victim) + promoted) - piece_value(attacker);
}

void MoveOrdering::update(chess::Color side, chess::Move move, int bonus) {
    bonus = std::clamp(bonus, -history_max, history_max);
    int& entry = history_[side_index(side)][move.from().index()][move.to().index()];
    entry += bonus - entry * std::abs(bonus) / history_max;
    entry = std::clamp(entry, -history_max, history_max);
}

void MoveOrdering::record_cutoff(const chess::Board& board, const Picker& picker, int depth) {
    const int cutoff_index = picker.tried_.size() - 1;
    const chess::Move cutoff = picker.tried_[cutoff_index];
    if (!is_quiet(board, cutoff)) {
        return;
    }

    const int bonus = depth * depth;
    update(board.sideToMove(), cutoff, bonus);
    for (int i = 0; i < cutoff_index; ++i) {
        if (is_quiet(board, picker.tried_[i])) {
            update(board.sideToMove(), picker.tried_[i], -bonus);
        }
    }
}
