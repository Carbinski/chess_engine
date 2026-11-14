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

## freya-v5

Fixes stalemate bug with freya-v2.


## freya-v7

About 15% faster than freya-v5. Move ordering tries the previous best move first, then sorts captures, and sorts quiet moves only if search reaches them.

Profiled for 20 seconds from `startpos moves e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6`. The engine played d2d3 after 171,663,360 nodes, 8.6 million per second:

| Share | Where the time goes |
|---:|---|
| 33.7% | Search. Mostly the move picker scoring every legal move before the first try. |
| 17.7% | Movegen. |
| 16.7% | Make and unmake. Piece and hash updates. |
| 15.9% | Evaluate. About 12 points are the static evaluation. The rest is `piece_value` while scoring captures. |
| 8.0% | Move ordering sort. Quiet moves are sorted only when search reaches them. |
| 6.7% | Transposition. |
