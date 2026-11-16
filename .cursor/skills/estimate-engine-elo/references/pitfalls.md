# Pitfalls from the first measurement

These are the failures from the 2026-11-16 run. The scripts already avoid the ones they can.

## Engine process

- `CHESS_LOG` defaults to `trace` and writes `logs/` relative to the process working directory (`engines/cpp/src/logging.hpp`). `run_bracket.py` wraps the engine so the process fastchess execs sets `CHESS_LOG=off`. An assignment on the left of a shell pipe does not apply to that process.
- Configure with `-DCMAKE_CXX_COMPILER=g++`. On this image, `/usr/bin/c++` is Clang and the link fails with `cannot find -lstdc++`.
- `uci.cpp` reads `wtime` / `btime` for the side to move, or `movetime` if that is present, and ignores `winc`, `binc`, and `movestogo`. `search.cpp` sets the budget to that value divided by 75. At `8+0.08` the engine thinks for about 0.10 seconds per move. The rating includes this. Sending `quit` immediately after `go` in a hand test aborts the search at depth 1; wait for `bestmove`.
- The engine does not send `info score` lines, so fastchess score-resign and score-draw adjudication never trigger for it. Games run to a normal result, or to a time forfeit.

## Stockfish's dial

- `UCI_Elo` does nothing unless `UCI_LimitStrength=true`.
- Stockfish 17 and 19 share the formula in `search.h`, fit on 22 January 2023 (commit `a08b8d4e`) against then-current master and CCRL-rated Stash. The comment maps skill 0–19 to CCRL Blitz about 1320–3190. The same number on a newer binary plays stronger chess, because the limiter still uses that binary's evaluation.
- At a limited setting Stockfish searches a shallow multipv and then plays a different root move. Fastchess warns `Bestmove does not match beginning of last PV` on those moves. That is the limiter, not a desync. Redirect stdout or the log swamps the terminal.
- Stockfish 11's formula is in its `search.cpp` and was fit at 60+0.6. Do not put it on one scale with 17 and 19.
- Threads=1 and Hash=16 on Stockfish. Old engines default to more threads. Leave one core per engine process: concurrency `nproc/2`, not two matches at once.

## The fit

- The 95% interval is where log likelihood drops by 1.920729 from the maximum. Walking the search in the wrong direction returns the ends of the search range (for example 800–3200) and looks like a failed fit. Use `scripts/fit_elo.py`.
- A 0-for-n score against a full-strength engine means the engine is at least about `400 * log10((1 - p) / p)` Elo behind, with `p` the Clopper-Pearson 95% upper tail `1 - 0.05^(1/n)` (about 275 Elo for 0/16). That gap is at this time control. A CCRL 40/15 list number is a different scale.
- White and Black can differ by a couple of hundred Elo in a sample of this size. Report both. The headline is the combined sample.
- Official Stockfish 17 and 19 binaries are the anchors. A local `-O3` build of an old engine, especially one compiled with `-fno-aggressive-loop-optimizations`, is a few tens of Elo off the profiled binary a rating list measured. That does not move a 0-for-16 result.
