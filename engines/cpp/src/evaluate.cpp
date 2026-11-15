#include "evaluate.hpp"

#include <vector>

namespace {

struct PieceValues {
    int pawn = 100;
    int knight = 300;
    int bishop = 300;
    int rook = 500;
    int queen = 900;
};

const PieceValues piece_values;

// Weights taken from PeSTO evaluation
struct PieceSquareWeights {
    int pawn_midgame[64] = {
          0,   0,   0,   0,   0,   0,   0,   0,
        -35,  -1, -20, -23, -15,  24,  38, -22,
        -26,  -4,  -4, -10,   3,   3,  33, -12,
        -27,  -2,  -5,  12,  17,   6,  10, -25,
        -14,  13,   6,  21,  23,  12,  17, -23,
         -6,   7,  26,  31,  65,  56,  25, -20,
         98, 134,  61,  95,  68, 126,  34, -11,
          0,   0,   0,   0,   0,   0,   0,   0
    };
    int pawn_endgame[64] = {
          0,   0,   0,   0,   0,   0,   0,   0,
         13,   8,   8,  10,  13,   0,   2,  -7,
          4,   7,  -6,   1,   0,  -5,  -1,  -8,
         13,   9,  -3,  -7,  -7,  -8,   3,  -1,
         32,  24,  13,   5,  -2,   4,  17,  17,
         94, 100,  85,  67,  56,  53,  82,  84,
        178, 173, 158, 134, 147, 132, 165, 187,
          0,   0,   0,   0,   0,   0,   0,   0
    };
    int knight_midgame[64] = {
        -105,  -21,  -58,  -33,  -17,  -28,  -19,  -23,
         -29,  -53,  -12,   -3,   -1,   18,  -14,  -19,
         -23,   -9,   12,   10,   19,   17,   25,  -16,
         -13,    4,   16,   13,   28,   19,   21,   -8,
          -9,   17,   19,   53,   37,   69,   18,   22,
         -47,   60,   37,   65,   84,  129,   73,   44,
         -73,  -41,   72,   36,   23,   62,    7,  -17,
        -167,  -89,  -34,  -49,   61,  -97,  -15, -107
    };
    int knight_endgame[64] = {
        -29, -51, -23, -15, -22, -18, -50, -64,
        -42, -20, -10,  -5,  -2, -20, -23, -44,
        -23,  -3,  -1,  15,  10,  -3, -20, -22,
        -18,  -6,  16,  25,  16,  17,   4, -18,
        -17,   3,  22,  22,  22,  11,   8, -18,
        -24, -20,  10,   9,  -1,  -9, -19, -41,
        -25,  -8, -25,  -2,  -9, -25, -24, -52,
        -58, -38, -13, -28, -31, -27, -63, -99
    };
    int bishop_midgame[64] = {
        -33,  -3, -14, -21, -13, -12, -39, -21,
          4,  15,  16,   0,   7,  21,  33,   1,
          0,  15,  15,  15,  14,  27,  18,  10,
         -6,  13,  13,  26,  34,  12,  10,   4,
         -4,   5,  19,  50,  37,  37,   7,  -2,
        -16,  37,  43,  40,  35,  50,  37,  -2,
        -26,  16, -18, -13,  30,  59,  18, -47,
        -29,   4, -82, -37, -25, -42,   7,  -8
    };
    int bishop_endgame[64] = {
        -23,  -9, -23,  -5,  -9, -16,  -5, -17,
        -14, -18,  -7,  -1,   4,  -9, -15, -27,
        -12,  -3,   8,  10,  13,   3,  -7, -15,
         -6,   3,  13,  19,   7,  10,  -3,  -9,
         -3,   9,  12,   9,  14,  10,   3,   2,
          2,  -8,   0,  -1,  -2,   6,   0,   4,
         -8,  -4,   7, -12,  -3, -13,  -4, -14,
        -14, -21, -11,  -8,  -7,  -9, -17, -24
    };
    int rook_midgame[64] = {
        -19, -13,   1,  17,  16,   7, -37, -26,
        -44, -16, -20,  -9,  -1,  11,  -6, -71,
        -45, -25, -16, -17,   3,   0,  -5, -33,
        -36, -26, -12,  -1,   9,  -7,   6, -23,
        -24, -11,   7,  26,  24,  35,  -8, -20,
         -5,  19,  26,  36,  17,  45,  61,  16,
         27,  32,  58,  62,  80,  67,  26,  44,
         32,  42,  32,  51,  63,   9,  31,  43
    };
    int rook_endgame[64] = {
         -9,   2,   3,  -1,  -5, -13,   4, -20,
         -6,  -6,   0,   2,  -9,  -9, -11,  -3,
         -4,   0,  -5,  -1,  -7, -12,  -8, -16,
          3,   5,   8,   4,  -5,  -6,  -8, -11,
          4,   3,  13,   1,   2,   1,  -1,   2,
          7,   7,   7,   5,   4,  -3,  -5,  -3,
         11,  13,  13,  11,  -3,   3,   8,   3,
         13,  10,  18,  15,  12,  12,   8,   5
    };
    int queen_midgame[64] = {
         -1, -18,  -9,  10, -15, -25, -31, -50,
        -35,  -8,  11,   2,   8,  15,  -3,   1,
        -14,   2, -11,  -2,  -5,   2,  14,   5,
         -9, -26,  -9, -10,  -2,  -4,   3,  -3,
        -27, -27, -16, -16,  -1,  17,  -2,   1,
        -13, -17,   7,   8,  29,  56,  47,  57,
        -24, -39,  -5,   1, -16,  57,  28,  54,
        -28,   0,  29,  12,  59,  44,  43,  45
    };
    int queen_endgame[64] = {
        -33, -28, -22, -43,  -5, -32, -20, -41,
        -22, -23, -30, -16, -16, -23, -36, -32,
        -16, -27,  15,   6,   9,  17,  10,   5,
        -18,  28,  19,  47,  31,  34,  39,  23,
          3,  22,  24,  45,  57,  40,  57,  36,
        -20,   6,   9,  49,  47,  35,  19,   9,
        -17,  20,  32,  41,  58,  25,  30,   0,
         -9,  22,  22,  27,  27,  19,  10,  20
    };
    int king_midgame[64] = {
        -15,  36,  12, -54,   8, -28,  24,  14,
          1,   7,  -8, -64, -43, -16,   9,   8,
        -14, -14, -22, -46, -44, -30, -15, -27,
        -49,  -1, -27, -39, -46, -44, -33, -51,
        -17, -20, -12, -27, -30, -25, -14, -36,
         -9,  24,   2, -16, -20,   6,  22, -22,
         29,  -1, -20,  -7,  -8,  -4, -38, -29,
        -65,  23,  16, -15, -56, -34,   2,  13
    };
    int king_endgame[64] = {
        -53, -34, -21, -11, -28, -14, -24, -43,
        -27, -11,   4,  13,  14,   4,  -5, -17,
        -19,  -3,  11,  21,  23,  16,   7,  -9,
        -18,  -4,  21,  24,  27,  23,   9, -11,
         -8,  22,  24,  27,  26,  33,  26,   3,
         10,  17,  23,  15,  20,  45,  44,  13,
        -12,  17,  14,  17,  17,  38,  23,  11,
        -74, -35, -18, -18, -11,  15,   4, -17
    };
};

const PieceSquareWeights piece_square_weights;

struct EvaluationState {
    int midgame = 0;
    int endgame = 0;
    int material = 0;
};

EvaluationState evaluation_state;
std::vector<EvaluationState> evaluation_stack;

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

int index(int sq, chess::Color color) {
    return color == chess::Color::WHITE ? sq : sq ^ 56;
}

int sign(chess::Color color) {
    return color == chess::Color::WHITE ? 1 : -1;
}

const int* midgame_table(chess::PieceType type) {
    switch (type.internal()) {
        case chess::PieceType::PAWN:   return piece_square_weights.pawn_midgame;
        case chess::PieceType::KNIGHT: return piece_square_weights.knight_midgame;
        case chess::PieceType::BISHOP: return piece_square_weights.bishop_midgame;
        case chess::PieceType::ROOK:   return piece_square_weights.rook_midgame;
        case chess::PieceType::QUEEN:  return piece_square_weights.queen_midgame;
        case chess::PieceType::KING:   return piece_square_weights.king_midgame;
        default:                       return nullptr;
    }
}

const int* endgame_table(chess::PieceType type) {
    switch (type.internal()) {
        case chess::PieceType::PAWN:   return piece_square_weights.pawn_endgame;
        case chess::PieceType::KNIGHT: return piece_square_weights.knight_endgame;
        case chess::PieceType::BISHOP: return piece_square_weights.bishop_endgame;
        case chess::PieceType::ROOK:   return piece_square_weights.rook_endgame;
        case chess::PieceType::QUEEN:  return piece_square_weights.queen_endgame;
        case chess::PieceType::KING:   return piece_square_weights.king_endgame;
        default:                       return nullptr;
    }
}

void apply(EvaluationState& total, const EvaluationState& delta) {
    total.midgame += delta.midgame;
    total.endgame += delta.endgame;
    total.material += delta.material;
}

EvaluationState add_piece(chess::PieceType type, chess::Color color, chess::Square sq) {
    const int placed = index(sq.index(), color);
    const int s = sign(color);
    return {
        s * midgame_table(type)[placed],
        s * endgame_table(type)[placed],
        s * piece_value(type),
    };
}

EvaluationState remove_piece(chess::PieceType type, chess::Color color, chess::Square sq) {
    EvaluationState delta = add_piece(type, color, sq);
    delta.midgame = -delta.midgame;
    delta.endgame = -delta.endgame;
    delta.material = -delta.material;
    return delta;
}

EvaluationState relocate_piece(chess::PieceType type, chess::Color color, chess::Square from, chess::Square to) {
    EvaluationState delta = remove_piece(type, color, from);
    apply(delta, add_piece(type, color, to));
    return delta;
}

}

int evaluate(const chess::Board& board) {
    const int phase = game_phase(board);
    return interpolate(evaluation_state.midgame, evaluation_state.endgame, phase) + evaluation_state.material;
}

void set_evaluation(const chess::Board& board) {
    evaluation_state = {};
    evaluation_stack.clear();

    chess::Bitboard occupied = board.occ();
    while (occupied) {
        const chess::Square sq(occupied.pop());
        const chess::Piece piece = board.at(sq);
        apply(evaluation_state, add_piece(piece.type(), piece.color(), sq));
    }
}

// The move is still unplayed. sideToMove, the piece on from, and a captured piece on to are read from this board.
void make_move(const chess::Board& board, const chess::Move& move) {
    const chess::Color mover = board.sideToMove();
    const chess::Color opponent = ~mover;
    EvaluationState delta;

    switch (move.typeOf()) {
        case chess::Move::CASTLING: {
            const bool king_side = move.to() > move.from();
            apply(delta, relocate_piece(chess::PieceType::KING, mover, move.from(),
                                        chess::Square::castling_king_square(king_side, mover)));
            apply(delta, relocate_piece(chess::PieceType::ROOK, mover, move.to(),
                                        chess::Square::castling_rook_square(king_side, mover)));
            break;
        }
        case chess::Move::PROMOTION: {
            apply(delta, remove_piece(chess::PieceType::PAWN, mover, move.from()));
            apply(delta, add_piece(move.promotionType(), mover, move.to()));
            if (board.isCapture(move)) {
                apply(delta, remove_piece(board.at<chess::PieceType>(move.to()), opponent, move.to()));
            }
            break;
        }
        case chess::Move::ENPASSANT: {
            apply(delta, relocate_piece(chess::PieceType::PAWN, mover, move.from(), move.to()));
            apply(delta, remove_piece(chess::PieceType::PAWN, opponent, move.to().ep_square()));
            break;
        }
        default: {
            apply(delta, relocate_piece(board.at<chess::PieceType>(move.from()), mover, move.from(), move.to()));
            if (board.isCapture(move)) {
                apply(delta, remove_piece(board.at<chess::PieceType>(move.to()), opponent, move.to()));
            }
            break;
        }
    }

    evaluation_stack.push_back(evaluation_state);
    apply(evaluation_state, delta);
}

void unmake_move(const chess::Move&) {
    evaluation_state = evaluation_stack.back();
    evaluation_stack.pop_back();
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

