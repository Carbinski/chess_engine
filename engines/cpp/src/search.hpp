#pragma once

#include "chess.hpp"
#include "transposition.hpp"

#include <cstdint>
#include <optional>
#include <string_view>
#include <chrono>

class Search {
public:
    virtual ~Search() = default;

    virtual chess::Move select_move(const chess::Board& board, std::optional<int> time_remaining_ms) = 0;
    virtual std::string_view name() const = 0;
};

class Dumbledore : public Search {
public:
    Dumbledore();
    chess::Move select_move(const chess::Board& board, std::optional<int> time_remaining_ms) override;
    std::string_view name() const override;

private:
    int search(chess::Board& board, int depth, int alpha, int beta);
    bool check_time_expired();

    std::chrono::steady_clock::time_point start_{};
    int budget_ms_ = 0;
    bool out_of_time_ = false;
    std::uint64_t nodes_ = 0;
    std::uint64_t tt_probes_ = 0;
    std::uint64_t tt_hits_ = 0;
    std::uint64_t tt_cutoffs_ = 0;
    std::uint64_t first_cutoffs_ = 0;
    Transposition transposition_table_;
};
