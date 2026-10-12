#pragma once

#include "chess.hpp"

#include <optional>
#include <random>
#include <string_view>

// Picks a move. The UCI session talks to this, not to a particular search.
class Engine {
public:
    virtual ~Engine() = default;

    // time_remaining_ms is the side-to-move clock from `go`, in milliseconds.
    // Empty when that command did not include a clock.
    virtual chess::Move select_move(const chess::Board& board, std::optional<int> time_remaining_ms) = 0;
    virtual std::string_view name() const = 0;
};

class RandomEngine : public Engine {
public:
    RandomEngine();

    chess::Move select_move(const chess::Board& board, std::optional<int> time_remaining_ms) override;
    std::string_view name() const override;

private:
    std::mt19937 rng_;
};
