#pragma once

#include "chess.hpp"

struct PieceValues {
    int pawn = 100;
    int knight = 300;
    int bishop = 300;
    int rook = 500;
    int queen = 900;
};

inline PieceValues piece_values;

int evaluate(const chess::Board& board);

