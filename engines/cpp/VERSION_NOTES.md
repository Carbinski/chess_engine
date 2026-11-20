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

## ganymede-v1

About 30 Elo stronger than freya-v7 (+30 ± 18 over 1,001 games). Every piece has separate midgame and endgame square weights, taken from the PeSTO evaluation. The score blends the two by game phase.

## ganymede-v2

Search keeps a running midgame, endgame, and material total and updates it when a move is made or unmade. A leaf score blends that total by game phase, the same blend as ganymede-v1.

## helios-v1

Added quiescence sort. About 300 Elo stronger than ganymede-v3 (+301 ± 59 over 180 games).

## helios-v3

Castling is ordered with the other quiet moves. When the side to move is not in check, quiescence sorts captures by victim value and searches them in that order. Even with helios-v2 (0 ± 42 over 100 games at 10+0.1). The cheaper capture sort was removed in helios-v5. Castling stays a quiet move.

## helios-v4

Quiescence uses the full move picker again. Delta pruning skips a capture whose material gain cannot raise the score, unless the move gives check. Against helios-v2, 43.5/100 (−45 ± 48 over 100 games at 10+0.1; the interval covers 0). About 4–8% slower than helios-v2 on three 2-second searches. Removed in helios-v5.
