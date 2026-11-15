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

MoveOrdering::Picker::Picker(chess::Movelist& moves, chess::Move previous_best, const chess::Board& board, const MoveOrdering& ordering)
    : moves_(moves), board_(board), ordering_(ordering) {
    if (previous_best == chess::Move::NO_MOVE) {
        return;
    }
    for (int i = 0; i < moves.size(); ++i) {
        if (moves[i] == previous_best) {
            previous_best_ = moves[i];
            yield_previous_best_ = true;
            return;
        }
    }
}

void MoveOrdering::Picker::score_loud() {
    const bool has_best = previous_best_ != chess::Move::NO_MOVE;
    for (int i = 0; i < moves_.size(); ++i) {
        chess::Move move = moves_[i];
        if (has_best && move == previous_best_) {
            continue;
        }
        if (is_quiet(board_, move)) {
            continue;
        }
        move.setScore(static_cast<std::int16_t>(loud_score(board_, move)));
        loud_.add(move);
    }
}

void MoveOrdering::Picker::score_quiet() {
    const int side = side_index(board_.sideToMove());
    const bool has_best = previous_best_ != chess::Move::NO_MOVE;
    for (int i = 0; i < moves_.size(); ++i) {
        chess::Move move = moves_[i];
        if (has_best && move == previous_best_) {
            continue;
        }
        if (!is_quiet(board_, move)) {
            continue;
        }
        move.setScore(static_cast<std::int16_t>(ordering_.history_[side][move.from().index()][move.to().index()]));
        quiet_.add(move);
    }
}

std::optional<chess::Move> MoveOrdering::Picker::next() {
    std::optional<chess::Move> move;
    if (yield_previous_best_) {
        yield_previous_best_ = false;
        move = previous_best_;
    } else {
        if (!is_loud_sorted_) {
            score_loud();
            sort(loud_);
            is_loud_sorted_ = true;
        }
        if (loud_index_ < loud_.size()) {
            move = loud_[loud_index_++];
        } else {
            if (!is_quiet_sorted_) {
                score_quiet();
                sort(quiet_);
                is_quiet_sorted_ = true;
            }
            if (quiet_index_ < quiet_.size()) {
                move = quiet_[quiet_index_++];
            }
        }
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
