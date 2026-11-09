#include "evaluate.hpp"

int game_phase(const chess::Board& board) {
    int phase = board.pieces(chess::PieceType::KNIGHT).count()
        + board.pieces(chess::PieceType::BISHOP).count()
        + board.pieces(chess::PieceType::ROOK).count() * 2
        + board.pieces(chess::PieceType::QUEEN).count() * 4;
    if (phase > 24) {
        phase = 24;
    }
    return phase;
}

int interpolate(const int midgame, const int endgame, int phase) {
    return (midgame * phase + endgame * (24 - phase)) / 24;
}

int score_piece(const chess::Board& board, chess::PieceType type, int value, const int table[64]) {
    int score = 0;

    chess::Bitboard white = board.pieces(type, chess::Color::WHITE);
    while (white) {
        const int sq = white.pop();
        score += value + table[sq];
    }

    chess::Bitboard black = board.pieces(type, chess::Color::BLACK);
    while (black) {
        const int sq = black.pop();
        score -= value + table[sq ^ 56];
    }

    return score;
}

int evaluate(const chess::Board& board) {
    const auto result = board.isGameOver().second;
    if (result == chess::GameResult::LOSE) {
        return board.sideToMove() == chess::Color::WHITE ? -checkmate_score : checkmate_score;
    }
    if (result == chess::GameResult::DRAW) {
        return 0;
    }

    const int phase = game_phase(board);
    const int king_midgame = score_piece(board, chess::PieceType::KING, 0, piece_square_weights.king_midgame);
    const int king_endgame = score_piece(board, chess::PieceType::KING, 0, piece_square_weights.king_endgame);

    return score_piece(board, chess::PieceType::PAWN, piece_values.pawn, piece_square_weights.pawn)
        + score_piece(board, chess::PieceType::KNIGHT, piece_values.knight, piece_square_weights.knight)
        + score_piece(board, chess::PieceType::BISHOP, piece_values.bishop, piece_square_weights.bishop)
        + score_piece(board, chess::PieceType::ROOK, piece_values.rook, piece_square_weights.rook)
        + score_piece(board, chess::PieceType::QUEEN, piece_values.queen, piece_square_weights.queen)
        + interpolate(king_midgame, king_endgame, phase);
}
