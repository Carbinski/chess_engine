#include "engine.hpp"

#include <iostream>
#include <sstream>
#include <string>
#include <string_view>

using namespace chess;

// Speaks UCI with the tournament runner. Move choice is delegated to Engine.
class UciSession {
public:
    explicit UciSession(Engine& engine) : engine_(engine) {}

    void run();

private:
    void send(std::string_view line) const;
    void set_position(const std::string& line);
    void go();

    Engine& engine_;
    Board board_;
};

void UciSession::send(std::string_view line) const {
    std::cout << line << std::endl;
}

void UciSession::set_position(const std::string& line) {
    std::istringstream in(line);
    std::string token;
    in >> token;

    if (!(in >> token)) {
        return;
    }

    if (token == "startpos") {
        board_.setFen(constants::STARTPOS);
        in >> token;
    } else if (token == "fen") {
        std::string fen;
        while (in >> token && token != "moves") {
            if (!fen.empty()) {
                fen.push_back(' ');
            }
            fen += token;
        }
        board_.setFen(fen);
    }

    if (token != "moves") {
        return;
    }

    while (in >> token) {
        const Move move = uci::uciToMove(board_, token);
        if (move == Move::NO_MOVE) {
            break;
        }
        board_.makeMove(move);
    }
}

void UciSession::go() {
    const Move move = engine_.select_move(board_);
    if (move == Move::NO_MOVE) {
        send("bestmove 0000");
        return;
    }
    send("bestmove " + uci::moveToUci(move));
}

void UciSession::run() {
    std::string line;

    while (std::getline(std::cin, line)) {
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }

        std::istringstream in(line);
        std::string command;
        if (!(in >> command)) {
            continue;
        }

        if (command == "uci") {
            send(std::string("id name ") + std::string(engine_.name()));
            send("id author chess_engine");
            send("uciok");
        } else if (command == "isready") {
            send("readyok");
        } else if (command == "ucinewgame") {
            board_.setFen(constants::STARTPOS);
        } else if (command == "position") {
            set_position(line);
        } else if (command == "go") {
            go();
        } else if (command == "quit") {
            break;
        }
    }
}

int main() {
    RandomEngine engine;
    UciSession session(engine);
    session.run();
}
