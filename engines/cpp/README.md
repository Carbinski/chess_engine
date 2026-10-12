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

Every frozen binary uses the same command line:

```text
cpp-v1 <fen> <time_ms>
```

It prints one UCI move on stdout (for example `e2e4` or `a7a8q`). Search, the board representation, and eval can change between tags. This command line stays fixed, so the web backend and match runner can launch any release the same way.

### Playing versions

The local site can shell out to a path under `releases/`, the same way it already launches a Java bot with a FEN and a time limit.

For tournaments, teach the engine UCI and run the binaries with [cutechess-cli](https://github.com/cutechess/cutechess) or [fastchess](https://github.com/Disservin/fastchess). Those tools play engine binaries against each other, so `cpp-v1` vs `cpp-v3` does not need a custom match harness.

If two versions differ only by eval weights or search parameters, a data file next to the binary is enough. When search or the board changes, freeze a new binary.
