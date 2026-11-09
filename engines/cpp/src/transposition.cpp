#include "transposition.hpp"

Transposition::Transposition() : transposition_table(table_size) {}

void Transposition::store_position(const Entry& entry) {
    Entry& slot = transposition_table[index_of(entry.key)];
    if (entry.depth < slot.depth) {
        return;
    }
    slot = entry;
}

std::optional<Entry> Transposition::get_position(std::uint64_t hash) const {
    const Entry& slot = transposition_table[index_of(hash)];
    if (slot.key != hash) {
        return std::nullopt;
    }
    return slot;
}
