#include "move_ordering.hpp"

#include "evaluate.hpp"

#include <algorithm>
#include <cstdint>
#include <utility>

#ifndef MOVE_ORDER_MODE
#define MOVE_ORDER_MODE 0
#endif

#if MOVE_ORDER_MODE != 0
namespace {

int piece_value(chess::PieceType type) {
    switch (type.internal()) {
    case chess::PieceType::PAWN:
        return piece_values.pawn;
    case chess::PieceType::KNIGHT:
        return piece_values.knight;
    case chess::PieceType::BISHOP:
        return piece_values.bishop;
    case chess::PieceType::ROOK:
        return piece_values.rook;
    case chess::PieceType::QUEEN:
        return piece_values.queen;
    default:
        return 0;
    }
}

// Most valuable victim, least valuable attacker. Victim is weighted so a
// bigger capture always outranks the attacker that made it.
int capture_score(int victim, int attacker) {
    return 10 * victim - attacker;
}

void rank_by_mvv_lva(const chess::Board& board, chess::Movelist& moves) {
    for (int i = 0; i < moves.size(); ++i) {
        chess::Move move = moves[i];
        const int attacker = piece_value(board.at<chess::PieceType>(move.from()));
        int score = 0;

        const bool normal_capture =
            move.typeOf() != chess::Move::CASTLING && board.at(move.to()) != chess::Piece::NONE;
        if (normal_capture) {
            score += capture_score(piece_value(board.at<chess::PieceType>(move.to())), attacker);
        }

#if MOVE_ORDER_MODE == 1 || MOVE_ORDER_MODE == 3
        // The captured pawn is not on the target square, so a plain victim
        // lookup would treat en passant as a quiet move.
        if (move.typeOf() == chess::Move::ENPASSANT) {
            score += capture_score(piece_values.pawn, attacker);
        }
#endif

#if MOVE_ORDER_MODE == 2 || MOVE_ORDER_MODE == 3
        if (move.typeOf() == chess::Move::PROMOTION) {
            score += 900;
            if (move.promotionType() == chess::PieceType::QUEEN) {
                score += 100;
            }
        }
#endif

        move.setScore(static_cast<std::int16_t>(score));
        moves[i] = move;
    }

    std::stable_sort(moves.begin(), moves.end(), [](const chess::Move& a, const chess::Move& b) {
        return a.score() > b.score();
    });
}

}
#endif

void MoveOrdering::order_moves(const chess::Board& board, chess::Movelist& moves, chess::Move best) {
#if MOVE_ORDER_MODE != 0
    rank_by_mvv_lva(board, moves);
#else
    (void)board;
#endif
    transposition_table_move_first(moves, best);
}

void MoveOrdering::transposition_table_move_first(chess::Movelist& moves, chess::Move best) {
    if (best == chess::Move::NO_MOVE || moves.empty() || moves[0] == best) {
        return;
    }
    for (int i = 1; i < moves.size(); ++i) {
        if (moves[i] == best) {
#if MOVE_ORDER_MODE == 0
            // Unsorted lists only need the hash move in front.
            std::swap(moves[0], moves[i]);
#else
            // Keep the MVV-LVA order of every other move.
            std::rotate(moves.begin(), moves.begin() + i, moves.begin() + i + 1);
#endif
            return;
        }
    }
}
