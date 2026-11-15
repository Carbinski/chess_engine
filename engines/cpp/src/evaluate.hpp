#pragma once

#include "chess.hpp"

int evaluate(const chess::Board& board);
void set_evaluation(const chess::Board& board);

// The move is still unplayed. sideToMove, the piece on from, and a captured piece on to are read from this board.
void make_move(const chess::Board& board, const chess::Move& move);
void unmake_move(const chess::Move& move);

// Checkmate, before search counts the plies.
inline constexpr int checkmate_score = 1'000'000;

bool is_insufficient_material(const chess::Board& board);
bool is_path_draw(const chess::Board& board);
int mate_or_stalemate(const chess::Board& board);

int piece_value(chess::PieceType type);
