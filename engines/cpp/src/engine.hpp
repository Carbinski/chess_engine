#pragma once

#include "chess.hpp"
#include "search.hpp"

#include <optional>
#include <string_view>

// Picks a move. The UCI session talks to this, not to a particular search.
class Engine {
public:
    virtual ~Engine() = default;

    virtual chess::Move select_move(const chess::Board& board, std::optional<int> time_remaining_ms) = 0;
    virtual std::string_view name() const = 0;
};

class SearchEngine : public Engine {
public:
    SearchEngine();

    chess::Move select_move(const chess::Board& board, std::optional<int> time_remaining_ms) override;
    std::string_view name() const override;

private:
    BasicSearch search_;
};
