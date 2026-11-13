# MVV-LVA move ordering

Local match on 12 Nov 2026, 10:03–10:35 AM ET. The engine sources were left unchanged. The four binaries existed only for this run.

## Question

Dumbledore searches the transposition-table move first and otherwise leaves move order alone. This match asked whether most-valuable-victim, least-valuable-attacker (MVV-LVA) capture ordering is worth its cost, and whether extra checks for en passant and promotion change that.

## Builds

All four were Release builds of the same tree, differing only in `order_moves`.

| Build | Ordering |
| --- | --- |
| `dumbledore` | Transposition-table move first. This is the current engine. |
| `dumbledore-v1` | MVV-LVA. En passant counts as a pawn capture. |
| `dumbledore-v2` | MVV-LVA. Promotions score 900, and a queen promotion scores 1000. |
| `dumbledore-v3` | MVV-LVA with both of those checks. |

Capture score was `10 * victim - attacker`, using the engine’s piece values (pawn 100, knight 300, bishop 300, rook 500, queen 900). A normal capture is a non-castling move whose target square is occupied. En passant only scored when that check was compiled in, because the captured pawn is not on the target square. After scoring, the hash move was moved to the front. On the ordered builds it was rotated there so the best capture stayed next. The original kept its existing swap.

## Setup

fastchess round robin, both colors.

- 1,200 games, 200 per pairing
- time control `5+0.05`
- concurrency 4, which is this machine’s core count; fastchess rejects a higher value
- 100 openings from the fastchess ECO set, seed `20261112`
- each engine logged every search (`CHESS_LOG=trace`)

The engine spends `time_remaining / 75` on each search. Mean search time was 62 ms, and every search used the full budget.

## Result

Score is points across all 600 games that build played. “Vs original” is the 200-game head-to-head. Pool Elo is fastchess’s zero-sum rating of the four builds, with a 95% interval near ±24. A 200-game gap at these scores is about ±30 Elo.

| Build | Score | Vs original | Pool Elo |
| --- | --- | --- | --- |
| En passant | 60.3% | 130–53–17 (78.3%, about +222) | +73 |
| Promotion | 59.4% | 133–45–22 (77.8%, about +217) | +66 |
| Both checks | 57.6% | 123–58–19 (76.0%, about +200) | +53 |
| Original | 22.7% | — | −213 |

The ordered builds did not separate from each other.

| Matchup | Wins | Draws | Losses | Score |
| --- | --- | --- | --- | --- |
| En passant vs promotion | 71 | 69 | 60 | 52.8% |
| En passant vs both checks | 63 | 74 | 63 | 50.0% |
| Promotion vs both checks | 67 | 79 | 54 | 53.3% |

Games ended by mate (822), threefold repetition (362), insufficient material (15), or the fifty-move rule (1).

## Logs

Totals from the per-move search logs. Nodes per second is total nodes divided by total search time.

| Build | Searches | Nodes/sec | Median depth | Mean depth | Mean nodes | TT hits | Cutoffs on slot 0 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Original | 28,282 | 10.31M | 5 | 5.42 | 645k | 6.2% | 3.4% of nodes |
| En passant | 30,316 | 6.64M | 6 | 6.22 | 414k | 3.5% | 14.7% |
| Promotion | 31,376 | 6.61M | 6 | 6.23 | 411k | 3.0% | 14.8% |
| Both checks | 30,893 | 6.50M | 6 | 6.25 | 405k | 3.4% | 14.9% |

Mean depth leaves out 373–401 searches per build that ran past depth 40. Those are forced mates: iterative deepening keeps going until the clock expires, so the raw mean is not a depth.

A separate bench, one engine at a time, 800 ms per search, six positions, three reps each, showed the same split. The original ran at 10.7 million nodes per second. The ordered builds ran at 6.8–7.4 million and were usually one ply deeper on the tactical positions.

## Slot-0 cutoffs

`first_cutoffs` counts a beta cutoff only when the move in slot 0 caused it. Slot 0 is the previous-iteration move whenever the transposition table has one, and the capture sort only when it does not. A cutoff on slot 0 therefore credits iterative deepening on any node that already has a hash move. A cutoff on move 2, after that hash move fails, is missing from the column. That is the case where MVV-LVA matters most.

In these logs the hash move was rare. The table hit on 3–6% of interior nodes, and most of those hits returned a score before a move was tried. At most about 10% of the original’s slot-0 cutoffs, and about 2% of the ordered builds’, can be the hash move. The rest are nodes with no hash move, so slot 0 is the capture sort on the ordered builds and raw generation order on the original.

## Reading

MVV-LVA cost about 36% of the node rate. Median depth went from 5 to 6, and the ordered builds scored about 78% against the original. The en passant check, the promotion check, and both together changed node speed by about 2% and did not change the match between those three builds. The sort is the cost, and the games paid it back. The extra checks did not show a further tradeoff.
