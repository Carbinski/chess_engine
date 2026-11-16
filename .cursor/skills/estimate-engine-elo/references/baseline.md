# Baseline

Measured 16 November 2026, about 12:33 AM–1:31 AM Eastern, on a 4-core Intel Xeon. Engine commit `5597a64` (`feat: add quiescence search`), UCI name `Search`, search class Helios. Time control `8+0.08`, one thread, 16 MB hash, no tablebases, no books. Helios used about 0.10 seconds per move. Openings were the 32 positions in `assets/balanced.epd`. Concurrency 2.

Stockfish 19 and 17 were the official release binaries (`stockfish-linux-x86-64-universal`, `stockfish-ubuntu-x86-64-bmi2`). The historical engines were local g++ builds; see [full-strength.md](full-strength.md).

## Rating

| Dial | Games | Estimate | 95% profile interval |
| --- | ---: | ---: | --- |
| Stockfish 19 `UCI_Elo` | 136 | 2005 | 1936–2075 |
| Stockfish 17 `UCI_Elo` | 64 | 2236 | 2135–2336 |
| Stockfish 11 `UCI_Elo` (different formula, one opponent) | 16 | 2011 | 1824–2183 |

On the Stockfish 19 games Helios was about 2120 as White (42.5/68) and about 1890 as Black (27.0/68).

Stockfish 19 at `UCI_Elo` 2200 scored 24.5/32 (76.6%) against Stockfish 17 at 2200. Fastchess reported Stockfish 17 at −206 Elo, margin ±133. Shifting Stockfish 17's labels down by 206 and pooling gives about 2013, in line with the Stockfish 19 figure.

All 216 limited games ended normally. Average length was about 97 plies.

## Stockfish 19 scores (Helios)

| UCI_Elo | Score | Percent |
| ---: | ---: | ---: |
| 1320 | 8/8 | 100 |
| 1700 | 5/8 | 62.5 |
| 1800 | 12.5/20 | 62.5 |
| 1900 | 13/20 | 65.0 |
| 2000 | 18/32 | 56.2 |
| 2100 | 11/24 | 45.8 |
| 2300 | 1.5/8 | 18.8 |
| 2600 | 0.5/8 | 6.2 |
| 2900 | 0/8 | 0 |

## Full-strength ceiling

Helios lost all 128 games, 16 against each of Glaurung 2.1, Stockfish 1.0, 1.2, 1.6.3, 2.3.1, 5, 8, and 11. One loss was a time forfeit. That places Helios at least about 275 Elo behind each of those binaries at `8+0.08`. Glaurung 2.1's published 2772 is a CCRL 40/15 rating and is not this scale.

## Later runs

Append a row when a measurement should stay on record. Keep the time control, commit, and both dials.

| Date (Eastern) | Commit | TC | sf19 | sf19 interval | sf17 | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-16 | `5597a64` | 8+0.08 | 2005 | 1936–2075 | 2236 | First measurement. 0/128 vs full-strength ladder. |
