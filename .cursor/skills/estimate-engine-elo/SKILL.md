---
name: estimate-engine-elo
description: >
  Measure the C++ chess engine's Elo at 8+0.08 by playing official Stockfish
  17 and Stockfish 19 with UCI_LimitStrength, then fitting a logistic rating.
  Use when the user asks how strong the engine is, for its Elo or rating, or
  to rerun the Stockfish bracket.
---

# Estimate engine Elo

Measure the current C++ engine. Do not change its search or its clock to move the number. The rating includes the clock in `engines/cpp/src/uci.cpp` and `search.cpp`: `go` time is the side's remaining time (or `movetime`), divided by 75, and the increment is ignored.

Read [references/pitfalls.md](references/pitfalls.md) before the first run on a machine. The historical full-strength ladder is in [references/full-strength.md](references/full-strength.md). The 2026-11-16 result is in [references/baseline.md](references/baseline.md).

## Setup

From the repo root. Release is required. Clang fails to link `libstdc++` here; use g++.

```bash
git submodule update --init tools/fastchess engines/cpp/chess-library
cmake -S engines/cpp -B engines/cpp/build -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++
cmake --build engines/cpp/build -j
make -C tools/fastchess -j
```

## Run

```bash
python3 .cursor/skills/estimate-engine-elo/scripts/run_bracket.py \
  --engine engines/cpp/build/chess_engine \
  --name Helios \
  --out /tmp/elo-run
```

`--name` is the player label in the PGN. The baseline used `Helios`, which is the search class. The UCI `id name` is `Search` until `SearchEngine::name()` in `engines/cpp/src/engine.cpp` changes. Use the same `--name` for the fitter. The script downloads Stockfish 19 (`stockfish-linux-x86-64-universal`) and Stockfish 17 (`stockfish-ubuntu-x86-64-bmi2`) into `--out` on first use. A full bracket is about 15–25 minutes at concurrency 2. Leave it running. Fastchess's "Bestmove does not match beginning of last PV" lines are the strength limiter, and they are redirected to `--out/logs`.

What it plays, at `8+0.08`, one thread, 16 MB hash, `UCI_LimitStrength=true`, book `assets/balanced.epd`, both colors, concurrency `cpu_count // 2`:

1. Stockfish 19 at 1320, 1700, 2000, 2300, 2600, and 2900, 4 rounds (8 games) each.
2. 12 rounds (24 games) at the two levels that straddle 50%, plus up to two interior 100-Elo steps when that gap is wider than 100. Above 50% at every level, it adds 2900 and 3100. At or under 25% against 1320, it stops.
3. Stockfish 17 at the Stockfish 19 estimate rounded to 100, and 200 higher, 8 rounds (16 games) each.

`--skip-cross` skips step 3. `--calibrate` adds a 16-round Stockfish 17 vs Stockfish 19 match at `UCI_Elo` 2200, which remeasures the dial gap. `--fit-only` refits `--out/pgn` without playing. `--only sf19:2000 --rounds 4` plays one cell.

After editing the scripts, run `python3 .cursor/skills/estimate-engine-elo/scripts/test_fit.py`. It does not play games.

To refit PGNs from a finished run:

```bash
python3 .cursor/skills/estimate-engine-elo/scripts/fit_elo.py --engine-name Helios /tmp/elo-run/pgn
```

## How to report

Lead with the Stockfish 19 rating and its 95% profile interval. Then the Stockfish 17 rating and its interval. Then White and Black on the Stockfish 19 set. State the commit, `8+0.08`, one thread, no tablebases, and that the engine spends remaining time divided by 75.

Keep the two dials separate. On 2026-11-16, Stockfish 19 at `UCI_Elo` 2200 was about 206 Elo stronger than Stockfish 17 at the same setting. The fitter's shifted line is a check that the two samples agree after that gap. It is not a third rating to quote.

Stockfish 11's `UCI_Elo` formula was fit at 60+0.6 and is a different scale. Do not pool it with 17 or 19.

Compare the Stockfish 19 number to [references/baseline.md](references/baseline.md). Append a row there when the user wants the new run kept.

## When this bracket is the wrong tool

- Under 25% at 1320: the engine is below the dial. Say that and stop.
- Still above about 60% at 3100: the dial is topped out. Use [references/full-strength.md](references/full-strength.md) before quoting anything above 3190.
- A different time control, thread count, or clock produces a different rating. Label it, and do not compare it to the baseline.
