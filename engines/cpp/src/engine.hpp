#pragma once

#include "chess.hpp"

#include <random>
#include <string_view>

// Picks a move. The UCI session talks to this, not to a particular search.
class Engine {
public:
    virtual ~Engine() = default;

    virtual chess::Move select_move(const chess::Board& board) = 0;
    virtual std::string_view name() const = 0;
};

class RandomEngine : public Engine {
public:
    RandomEngine();

    chess::Move select_move(const chess::Board& board) override;
    std::string_view name() const override;

private:
    std::mt19937 rng_;
};
