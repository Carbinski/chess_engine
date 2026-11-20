#pragma once

#include "chess.hpp"
#include "move_ordering.hpp"
#include "transposition.hpp"

#include <cstdint>
#include <optional>
#include <string_view>
#include <chrono>

struct SearchCounters {
    std::uint64_t nodes = 0;
    std::uint64_t tt_probes = 0;
    std::uint64_t tt_hits = 0;
    std::uint64_t tt_cutoffs = 0;
    std::uint64_t null_cutoffs = 0;
    std::uint64_t first_cutoffs = 0;
};

class Search {
public:
    virtual ~Search() = default;

    virtual chess::Move select_move(const chess::Board& board, std::optional<int> time_remaining_ms) = 0;
    virtual std::string_view name() const = 0;
};

class Icarus : public Search {
public:
    Icarus();
    chess::Move select_move(const chess::Board& board, std::optional<int> time_remaining_ms) override;
    std::string_view name() const override;

private:
    struct TtHit {
        chess::Move hash_move = chess::Move::NO_MOVE;
        std::optional<int> cutoff;
    };

    int search(chess::Board& board, int depth, int alpha, int beta, bool is_principal_variation, bool allow_null);
    std::optional<int> null_cutoff(chess::Board& board, int depth, int alpha, int beta);
    int quiescence(chess::Board& board, int alpha, int beta);
    bool check_time_expired();
    TtHit probe_tt(std::uint64_t hash, int depth, int& alpha, int& beta);
    void store_tt(std::uint64_t hash, int depth, int score, int alpha, int beta, chess::Move best);

    std::chrono::steady_clock::time_point start_{};
    int budget_ms_ = 0;
    bool out_of_time_ = false;
    SearchCounters counters_;
    Transposition transposition_table_;
    MoveOrdering move_ordering_;
};
