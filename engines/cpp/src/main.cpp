#include "chess.hpp"

#include <iostream>
#include <random>

using namespace chess;

using Engine = Move (*)(const Board&);

namespace {

std::mt19937 rng{std::random_device{}()};

Move random_move(const Board& board) {
    Movelist moves;
    movegen::legalmoves(moves, board);
    std::uniform_int_distribution<int> pick(0, moves.size() - 1);
    return moves[pick(rng)];
}

const char* reason_name(GameResultReason reason) {
    switch (reason) {
        case GameResultReason::CHECKMATE:
            return "checkmate";
        case GameResultReason::STALEMATE:
            return "stalemate";
        case GameResultReason::INSUFFICIENT_MATERIAL:
            return "insufficient material";
        case GameResultReason::FIFTY_MOVE_RULE:
            return "fifty-move rule";
        case GameResultReason::THREEFOLD_REPETITION:
            return "threefold repetition";
        default:
            return "unknown";
    }
}

}  // namespace

void play(Engine white, Engine black) {
    Board board;
    int ply = 0;

    while (true) {
        const auto [reason, result] = board.isGameOver();
        if (result != GameResult::NONE) {
            const char* score = "1/2-1/2";
            if (reason == GameResultReason::CHECKMATE) {
                score = board.sideToMove() == Color::WHITE ? "0-1" : "1-0";
            }
            if (ply % 2 == 1) {
                std::cout << "\n";
            }
            std::cout << score << " " << reason_name(reason) << "\n";
            break;
        }

        const bool white_to_move = board.sideToMove() == Color::WHITE;
        const Move move = white_to_move ? white(board) : black(board);
        if (white_to_move) {
            std::cout << (ply / 2 + 1) << ". " << uci::moveToUci(move);
        } else {
            std::cout << " " << uci::moveToUci(move) << "\n";
        }

        board.makeMove(move);
        ++ply;
    }
}

int main() {
    play(random_move, random_move);
}
