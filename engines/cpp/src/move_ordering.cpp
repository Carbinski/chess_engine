#include "move_ordering.hpp"

#include <algorithm>
#include <cstdlib>

void MoveOrdering::update(chess::Color side, chess::Move move, int bonus) {
    bonus = std::clamp(bonus, -ScoreBands::history_max, ScoreBands::history_max);
    int& entry = history_[side_index(side)][move.from().index()][move.to().index()];
    entry += bonus - entry * std::abs(bonus) / ScoreBands::history_max;
    entry = std::clamp(entry, -ScoreBands::history_max, ScoreBands::history_max);
}

void MoveOrdering::record_cutoff(const chess::Board& board, const chess::Movelist& moves, int cutoff_index, int depth) {
    const chess::Move cutoff = moves[cutoff_index];
    if (!is_quiet(board, cutoff)) {
        return;
    }

    const int bonus = depth * depth;
    update(board.sideToMove(), cutoff, bonus);
    for (int i = 0; i < cutoff_index; ++i) {
        if (is_quiet(board, moves[i])) {
            update(board.sideToMove(), moves[i], -bonus);
        }
    }
}

void MoveOrdering::order_moves(chess::Movelist& moves, chess::Move best, const chess::Board& board) {
    const int side = side_index(board.sideToMove());
    for (int i = 0; i < moves.size(); ++i) {
        chess::Move& move = moves[i];
        if (best != chess::Move::NO_MOVE && move == best) {
            move.setScore(ScoreBands::prev_best);
            continue;
        }

        chess::PieceType victim = board.at(move.to()).type();
        if (move.typeOf() == chess::Move::ENPASSANT) {
            victim = chess::PieceType::PAWN;
        }

        const bool promotion = move.typeOf() == chess::Move::PROMOTION;
        if (victim != chess::PieceType::NONE || promotion) {
            const chess::PieceType attacker = board.at(move.from()).type();
            const int promoted = promotion ? piece_value(move.promotionType()) - 1 : 0;
            const int score = 10 * (piece_value(victim) + promoted) - piece_value(attacker);
            move.setScore(static_cast<std::int16_t>(ScoreBands::capture_base + score));
            continue;
        }

        move.setScore(static_cast<std::int16_t>(history_[side][move.from().index()][move.to().index()]));
    }

    std::stable_sort(moves.begin(), moves.end(), [](const chess::Move& a, const chess::Move& b) {
        return a.score() > b.score();
    });
}
