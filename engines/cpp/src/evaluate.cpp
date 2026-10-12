#include "evaluate.hpp"

int evaluate(const chess::Board& board) {
    const auto result = board.isGameOver().second;
    if (result == chess::GameResult::LOSE) {
        return board.sideToMove() == chess::Color::WHITE ? -1'000'000 : 1'000'000;
    }
    if (result == chess::GameResult::DRAW) {
        return 0;
    }

    const int white_pawns = board.pieces(chess::PieceType::PAWN, chess::Color::WHITE).count();
    const int black_pawns = board.pieces(chess::PieceType::PAWN, chess::Color::BLACK).count();

    const int white_knights = board.pieces(chess::PieceType::KNIGHT, chess::Color::WHITE).count();
    const int black_knights = board.pieces(chess::PieceType::KNIGHT, chess::Color::BLACK).count();

    const int white_bishops = board.pieces(chess::PieceType::BISHOP, chess::Color::WHITE).count();
    const int black_bishops = board.pieces(chess::PieceType::BISHOP, chess::Color::BLACK).count();

    const int white_rooks = board.pieces(chess::PieceType::ROOK, chess::Color::WHITE).count();
    const int black_rooks = board.pieces(chess::PieceType::ROOK, chess::Color::BLACK).count();

    const int white_queens = board.pieces(chess::PieceType::QUEEN, chess::Color::WHITE).count();
    const int black_queens = board.pieces(chess::PieceType::QUEEN, chess::Color::BLACK).count();

    return piece_values.pawn * (white_pawns - black_pawns)
        + piece_values.knight * (white_knights - black_knights)
        + piece_values.bishop * (white_bishops - black_bishops)
        + piece_values.rook * (white_rooks - black_rooks)
        + piece_values.queen * (white_queens - black_queens);
}
