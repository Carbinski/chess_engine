# Version notes

## eldritch-v1

Added LVV-MVA move ordering.

## freya-v1

About 1.3× faster than eldritch-v2. Search makes and unmakes moves on one board instead of copying it for every move.

## freya-v2

About 1.2× faster than freya-v1. Game over is checked only when a position has no legal moves. Search returns the static evaluation at depth 0 before that check, so a stalemate on that node is scored as a normal position.

## freya-v3

About 7% faster than freya-v2. The clock is checked every 2048 nodes. A stalemate at depth 0 is still scored as a normal position.

## freya-v4

About 3% faster than freya-v3. Release builds use `-march=native` and link-time optimization. A stalemate at depth 0 is still scored as a normal position.
