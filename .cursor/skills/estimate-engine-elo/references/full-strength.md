# Full-strength ladder

Use this when the engine is still scoring above about 60% against Stockfish 19 at `UCI_Elo` 3100, or when you want a ceiling against historical engines. A string of losses does not produce a point rating. On 2026-11-16 Helios lost all 128 games and the estimate came from the `UCI_Elo` bracket instead.

Play the same `8+0.08`, both colors, `assets/balanced.epd`, Threads=1, Hash=16. For engines older than Stockfish 17 also set `OwnBook=false` (the default book file is missing) and keep Threads at 1 (several default to 4). Name each opponent in fastchess (`Glaurung-2.1`, `sf-1.0`, …) so `fit_elo.py` can tabulate them. One loss on time counts as a loss.

## Binaries that bracketed Helios

Tags in `official-stockfish/Stockfish`. `sf_0` is Glaurung 2.1 and its binary is named `glaurung`. The others produce `stockfish`.

```bash
git clone --filter=blob:none https://github.com/official-stockfish/Stockfish.git /tmp/sfsrc
git -C /tmp/sfsrc fetch --tags
```

Check out each tag in its own worktree under `src/` and build there.

Glaurung 2.1 and Stockfish 1.0 through 1.2 segfault on current g++. `evaluate.cpp` reads one past `SafetyTable`, and `-faggressive-loop-optimizations` turns that into `SIGSEGV` inside `init_safety`. The 1.0 and 1.2 makefiles default `CXX` to `icpc`, and `include .depend` fails until that file exists. `cstring` is not pulled in transitively. This build ran:

```bash
touch .depend
make CXX=g++ \
  CXXFLAGS="-O3 -DNDEBUG -m64 -mpopcnt -msse3 -fno-exceptions -fomit-frame-pointer -fno-rtti -fno-strict-aliasing -fwrapv -fno-aggressive-loop-optimizations -w -std=gnu++14 -include cstring -include cstdlib -include cstdio -include cmath"
```

Stockfish 1.6.3 needed the same loop flag via its popcnt target:

```bash
make gcc-popcnt CXX=g++ \
  GCCFLAGS="-O3 -DNDEBUG -msse -mpopcnt -fno-strict-aliasing -fwrapv -fno-aggressive-loop-optimizations -fno-exceptions -fno-rtti"
```

Stockfish 2.3.1 built with `make build ARCH=x86-64-modern`. Stockfish 5, 8, and 11 built with `make build ARCH=x86-64-bmi2`. Those four did not need the loop flag. They are not profile-guided builds, so they can sit a few tens of Elo off a rating list's binary. Confirm each binary returns a legal `bestmove` for `position startpos` / `go movetime 1000` before a match. A `quit` sent before `bestmove` is an aborted search, not a broken build.

## Reading a shutout

`fit_elo.py` prints the score against each unlabeled opponent. For 0 wins in 16 games the 95% upper bound on the engine's score is about 17%, which is about 275 Elo behind that opponent at this time control. Do not subtract that from a CCRL 40/15 rating. Published anchors, for context only: Glaurung 2.1 64-bit is 2772 ± 15 on CCRL 40/15; computer-chess-index T1 at this same `8+0.08` lists full-strength Stockfish 8 around 2996 and Stockfish 19 around 3568.
