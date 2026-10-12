# C++ engine

One source tree lives in this directory. Previous versions are saved as git tags and built binaries, so old engines can play new ones without copying the source.

## Versions

Edit `src/` in place. Git history is the record of how the engine changed. When a version is worth keeping as an opponent, freeze it: tag the commit, build that commit, and copy the binary into `releases/`. Leave `src/` as the working copy and keep going.

`releases/` is gitignored. The tag is the source of truth. The binary is a cache you can rebuild from the tag.

Name the tag and the binary the same way: `cpp-v1`, `cpp-v2`, and so on.

### Freeze a version

From the repo root, with a clean tree:

```bash
git tag cpp-v1
cmake -S engines/cpp -B engines/cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build engines/cpp/build
mkdir -p engines/cpp/releases
cp engines/cpp/build/chess_engine engines/cpp/releases/cpp-v1
```

The CMake target name may differ once the project exists. Copy whatever binary the build produces, and name the copy after the tag.

To rebuild a binary you deleted:

```bash
git worktree add /tmp/cpp-v1 cpp-v1
cmake -S /tmp/cpp-v1/engines/cpp -B /tmp/cpp-v1/engines/cpp/build -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/cpp-v1/engines/cpp/build
cp /tmp/cpp-v1/engines/cpp/build/chess_engine engines/cpp/releases/cpp-v1
git worktree remove /tmp/cpp-v1
```

A worktree builds the old tag without switching your current checkout.

### Binary contract

Every frozen binary is a UCI engine. Fastchess starts the process and keeps it open. The engine reads commands on stdin and writes one response line at a time on stdout.

```text
uci
id name Random
id author chess_engine
uciok

isready
readyok

ucinewgame
position startpos moves e2e4
go wtime 10000 btime 10000
bestmove e7e5

quit
```

`bestmove` is the last line of a `go` response. Search, the board representation, and eval can change between tags. This exchange stays fixed.

### Playing versions

Build fastchess with `make -j` in `tools/fastchess`, then point it at the frozen binaries:

```bash
tools/fastchess/fastchess \
  -engine cmd=engines/cpp/releases/cpp-v1 name=cpp-v1 \
  -engine cmd=engines/cpp/releases/cpp-v2 name=cpp-v2 \
  -each tc=10+0.1 -rounds 200 -repeat
```

If two versions differ only by eval weights or search parameters, a data file next to the binary is enough. When search or the board changes, freeze a new binary.
