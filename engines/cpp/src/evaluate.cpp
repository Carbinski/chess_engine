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

int piece_value(chess::PieceType type) {
    switch (type.internal()) {
        case chess::PieceType::PAWN:   return piece_values.pawn;
        case chess::PieceType::KNIGHT: return piece_values.knight;
        case chess::PieceType::BISHOP: return piece_values.bishop;
        case chess::PieceType::ROOK:   return piece_values.rook;
        case chess::PieceType::QUEEN:  return piece_values.queen;
        default:                       return 0;
    }
}

int score_piece(const chess::Board& board, chess::PieceType type, const int table[64]) {
    const int value = piece_value(type);
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
    const int phase = game_phase(board);
    
    const int pawn_midgame = score_piece(board, chess::PieceType::PAWN, piece_square_weights.pawn_midgame);
    const int pawn_endgame = score_piece(board, chess::PieceType::PAWN, piece_square_weights.pawn_endgame);
    const int knight_midgame = score_piece(board, chess::PieceType::KNIGHT, piece_square_weights.knight_midgame);
    const int knight_endgame = score_piece(board, chess::PieceType::KNIGHT, piece_square_weights.knight_endgame);
    const int bishop_midgame = score_piece(board, chess::PieceType::BISHOP, piece_square_weights.bishop_midgame);
    const int bishop_endgame = score_piece(board, chess::PieceType::BISHOP, piece_square_weights.bishop_endgame);
    const int rook_midgame = score_piece(board, chess::PieceType::ROOK, piece_square_weights.rook_midgame);
    const int rook_endgame = score_piece(board, chess::PieceType::ROOK, piece_square_weights.rook_endgame);
    const int queen_midgame = score_piece(board, chess::PieceType::QUEEN, piece_square_weights.queen_midgame);
    const int queen_endgame = score_piece(board, chess::PieceType::QUEEN, piece_square_weights.queen_endgame);
    const int king_midgame = score_piece(board, chess::PieceType::KING, piece_square_weights.king_midgame);
    const int king_endgame = score_piece(board, chess::PieceType::KING, piece_square_weights.king_endgame);

    return interpolate(pawn_midgame, pawn_endgame, phase)
        + interpolate(knight_midgame, knight_endgame, phase)
        + interpolate(bishop_midgame, bishop_endgame, phase)
        + interpolate(rook_midgame, rook_endgame, phase)
        + interpolate(queen_midgame, queen_endgame, phase)
        + interpolate(king_midgame, king_endgame, phase);
}

bool is_insufficient_material(const chess::Board& board) {
    return board.isInsufficientMaterial();
}

bool is_path_draw(const chess::Board& board) {
    return board.isHalfMoveDraw() || board.isRepetition();
}

int mate_or_stalemate(const chess::Board& board) {
    if (board.inCheck()) {
        return board.sideToMove() == chess::Color::WHITE ? -checkmate_score : checkmate_score;
    }
    return 0;
}