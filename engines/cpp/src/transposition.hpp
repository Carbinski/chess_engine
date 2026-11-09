#pragma once

#include "chess.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

enum class Bound : std::uint8_t {
    Exact,  // alpha < score < beta
    Lower,  // score >= beta; the real score is at least this
    Upper,  // score <= alpha; the real score is at most this
};

struct Entry {
    std::uint64_t key = 0;
    int depth = 0;
    int score = 0;
    Bound flag = Bound::Exact;
    chess::Move best = chess::Move::NO_MOVE;
};

class Transposition {
public:
    Transposition();

    void store_position(const Entry& entry);
    std::optional<Entry> get_position(std::uint64_t hash) const;

private:
    static constexpr std::size_t table_size = 1u << 20;

    std::size_t index_of(std::uint64_t key) const {
        return key & (table_size - 1);
    }

    std::vector<Entry> transposition_table;
};
