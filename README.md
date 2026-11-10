# Chess Engine

Chess engines, with a small web UI for playing them.

Python and Java engines are already here. The C++ engine will live in `engines/cpp`.

## Layout

- `engines/python` — Python engines
- `engines/java` — Java engines (Maven)
- `engines/cpp` — C++ engine
- `web` — browser UI and local API
- `experiments` — early sketches

The Python code uses the [chess](https://python-chess.readthedocs.io/) library. The Java project uses [chesslib](https://github.com/bhlangonijr/chesslib).

## Cross-play

Python, Java, and the C++ binary all speak UCI. `python -m crossplay` is the referee: it owns the clock and the result, and either color can be any engine in `engines/catalog.json`. Think time uses the same split as the C++ engine, `remaining / 75` milliseconds. Increment is ignored by the engines and awarded by the referee.

```bash
python -m pip install -r requirements.txt
mvn -f engines/java/pom.xml -q compile
python -m crossplay list
python -m crossplay conform
python -m crossplay match python_random java_bot_v2 --time 10000 --inc 100
```

`--time` and `--inc` are milliseconds. `roundrobin` alternates colors for each pair. `fastchess` prints a command for `tools/fastchess` when that runner is built; it does not ship in this tree.

The C++ engine is optional. Build `engines/cpp` when its headers are present. The catalog uses `engines/cpp/build/chess_engine` as-is.

The web UI uses the same catalog. From the repo root:

```bash
python -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8000
```

In `web/frontend`, run `npm run dev` and open the page. Each color can be Human or any available engine.
