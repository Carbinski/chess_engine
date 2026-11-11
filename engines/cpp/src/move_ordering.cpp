#include "move_ordering.hpp"

#include <algorithm>

void MoveOrdering::order_moves(chess::Movelist& moves, chess::Move best, const chess::Board& board) {
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
        int score = 0;
        if (victim != chess::PieceType::NONE || promotion) {
            const chess::PieceType attacker = board.at(move.from()).type();
            const int promoted = promotion ? piece_value(move.promotionType()) - 1 : 0;
            score = 10 * (piece_value(victim) + promoted) - piece_value(attacker);

        }
        move.setScore(static_cast<std::int16_t>(score));
        // TODO: Add From-to history heuristic
    }

    std::stable_sort(moves.begin(), moves.end(), [](const chess::Move& a, const chess::Move& b) {
        return a.score() > b.score();
    });
}
