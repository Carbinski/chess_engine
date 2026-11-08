#pragma once

#include <cstdint>
#include <optional>
#include <string>

// One row per move, outside the node loop. Files land in CHESS_LOG_DIR (default: logs/):
//   search-<pid>.tsv
//   summary-<pid>.txt
// CHESS_LOG=trace|summary|off   default trace; "0" is off
// CHESS_LOG_EVERY=n             every nth search row; the summary counts every search
// CHESS_LOG_MIN_MS=n            search rows that took at least n milliseconds
// CHESS_LOG_VERBOSE=1           include the FEN

namespace logging {

struct SearchStats {
    std::string engine;
    int game = 0;
    int move_number = 0;
    std::string side;
    int depth = 0;
    std::uint64_t nodes = 0;
    std::int64_t elapsed_ms = 0;
    int budget_ms = 0;
    bool full_budget = false;
    std::optional<int> score;
    std::string move;
    std::string fen;
};

void begin_game();
void log_search(SearchStats stats);
void flush();
bool should_include_fen();

}
