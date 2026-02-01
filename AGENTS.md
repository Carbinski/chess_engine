# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a chess engine project with implementations in both Python and Java. The project includes multiple bot implementations with varying levels of sophistication, from basic material evaluation to advanced search algorithms with transposition tables, iterative deepening, and piece-square tables.

The project also includes a web application (Next.js frontend + FastAPI backend) that allows users to play against different bot implementations in the browser.

## Code Architecture

### Core Components

**Python Bots** (`bots/`)
- Bot progression: `random_algo.py` → `aggressive_algo.py` → `dumb_eval_algo.py` → `basic_search_algo.py` → `fast_search_v2/v3/v4.py` → `midgame_v1/v2/v3/v4.py`
- All bots implement a `select_move(board: chess.Board) -> chess.Move` interface
- Advanced bots use:
  - **Negamax with alpha-beta pruning** for search
  - **MVV-LVA (Most Valuable Victim - Least Valuable Attacker)** for move ordering
  - **Piece-square tables** for positional evaluation
  - **Iterative deepening** for time management (see `help` file for reference implementation)
  - **Transposition tables** (MidGame bots via `support/TranspositionTable.py`)
  - **Quiescence search** to avoid horizon effect (MidGame bots)
  - **Tapered evaluation** (midgame vs endgame phase) in advanced bots

**Java Bots** (`chess_engine_java/src/main/java/org/`)
- Similar progression: `BasicBot_V1/V2/V3.java` → `FastBot_V1/V2.java` → `Bot_V1/V2/V3.java`
- All Java bots implement the `JavaChessBot` interface with `select_move()`, `get_total_time()`, and `get_total_moves()`
- Uses `chesslib` (v1.3.3) from GitHub's bhlangonijr
- Advanced bots use similar optimizations as Python bots (transposition tables, tapered eval, etc.)
- `OneShotBot.java` is the entry point for web app integration - takes FEN string and bot name as args

**Support Modules**
- `support/TranspositionTable.py`: Hash table for caching position evaluations to avoid redundant calculations
- `support/Support.java`: Utility functions for the Java engine

**Runner Scripts**
- `runner.py`: Main Python orchestration script with three modes:
  - `play_game_with_computer()`: Human vs bot with HTML board visualization
  - `play_and_render_game()`: Bot vs bot with move-by-move HTML rendering
  - `run()`: Tournament mode for statistical analysis
- `chess_engine_java/src/main/java/org/Runner.java`: Java equivalent with similar modes

**Web Application** (`web_app/`)
- `frontend/`: Next.js 16 app with TypeScript, React 19, Tailwind CSS
  - Uses `react-chessboard` and `chess.js` libraries
  - Source files in `app/` directory (Next.js app router)
- `backend/`: FastAPI server
  - `main.py`: API endpoints (`/move` and `/bots`)
  - `bot_manager.py`: Manages Python and Java bot instantiation and move generation
  - Python bots run directly in-process
  - Java bots executed via subprocess calling `OneShotBot` with classpath

### Key Design Patterns

**Negamax Search**: All advanced bots use negamax formulation (negating opponent's score) rather than separate min/max functions. This simplifies the code and evaluation is always from current player's perspective.

**Delta Evaluation**: FastBot_V4 and Java Bot_V2 use incremental evaluation - instead of recalculating entire position after each move, they compute the delta (change in evaluation). Significantly faster than full re-evaluation.

**Move Ordering**: Critical for alpha-beta pruning efficiency. Bots prioritize:
1. Captures (sorted by MVV-LVA)
2. Checks
3. Castling
4. Promotions
5. Quiet moves

**Iterative Deepening**: Best move from depth N-1 is searched first at depth N, improving pruning. Allows time-bound search with best move from completed depth.

## Common Development Commands

### Python Bots

Run bot vs bot game with visualization:
```bash
python3 runner.py
```
Edit the `__main__` block in `runner.py` to select which bots to play and which mode to use.

Run single game and view HTML output:
```bash
python3 runner.py  # generates game_report.html by default
open game_report.html
```

Run with PyPy for performance (if available):
```bash
pypy3 runner.py
```

Test a bot interactively (human vs bot):
```python
from runner import play_game_with_computer
from bots.fast_search_v4 import FastBotV4
play_game_with_computer(True, FastBotV4())  # Play as white
```

### Java Bots

Build the Java project:
```bash
cd chess_engine_java
mvn clean compile
```

Run bot vs bot game:
```bash
cd chess_engine_java
mvn exec:java -Dexec.mainClass="org.Runner"
```
Edit `Runner.java` main method to select bots and modes.

Test single position with OneShotBot:
```bash
cd chess_engine_java
java -cp "libs/chesslib-1.3.3.jar:target/classes" org.OneShotBot "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" Bot_V2
```

### Web Application

Start backend (from web_app/backend):
```bash
cd web_app/backend
python3 -m uvicorn main:app --reload
```

Start frontend (from web_app/frontend):
```bash
cd web_app/frontend
npm install  # first time only
npm run dev
```

Build frontend for production:
```bash
cd web_app/frontend
npm run build
npm start
```

Lint frontend:
```bash
cd web_app/frontend
npm run lint
```

### Testing & Benchmarking

To benchmark bot performance, enable `stat_tracking` in bot constructors and check the timing comments at the bottom of `runner.py` which document performance metrics for various bot versions at different depths.

Run tournament between two bots:
```python
from runner import run
from bots.fast_search_v4 import FastBotV4
from bots.midgame_v4 import MidGameBotV4

bot1 = FastBotV4()
bot2 = MidGameBotV4()
results = run(bot1, bot2, total_games=100)
print(f"Bot1: {results[0]}, Draws: {results[1]}, Bot2: {results[2]}")
```

## Important Implementation Details

### Python Bot Development

When creating new bots:
1. Implement `select_move(self, board: chess.Board) -> chess.Move`
2. For negamax evaluation, return score from current player's perspective (multiply by `who2move`)
3. Use local variable caching for performance (e.g., `board = self.board, PIECE_WT = self.pieceWt`)
4. For move ordering, prioritize captures using MVV-LVA: `score = (10 * victim_value) - attacker_value`
5. Check for en passant captures separately (see `orderMoves()` in existing bots)
6. Add new bots to imports in `runner.py` and `web_app/backend/bot_manager.py`

### Java Bot Development

When creating new Java bots:
1. Implement `JavaChessBot` interface
2. Use bitboard operations for performance: `Long.bitCount()`, `Long.numberOfTrailingZeros()`
3. Use buffers to reduce garbage collection (see `Bot_V2.java` sort_buffers and delta_buffer)
4. Add bot to `OneShotBot.java` switch statement for web app integration
5. Add bot wrapper to `Runner.java` main method

### Position Evaluation

Piece values used across bots:
- Pawn: 100
- Knight: 300
- Bishop: 300
- Rook: 500
- Queen: 900
- King: 20000

Advanced bots use separate midgame and endgame piece-square tables. Game phase is calculated based on remaining material (max 6200 = 4 Rooks + 4 Knights + 4 Bishops + 2 Queens).

### Web App Integration

To add a new bot to the web app:
1. **Python bot**: Add to `bot_manager.py` in `get_python_move()` and add to `/bots` endpoint in `main.py`
2. **Java bot**: Add to `OneShotBot.java` switch statement, add to `get_java_move()` in `bot_manager.py`, and add to `/bots` endpoint in `main.py`
3. Bot IDs use format: `python_{name}` or `java_{name}`

### Performance Notes

Performance benchmarks (seconds per move) are documented in comments at the bottom of `runner.py`:
- FastBotV4 at depth 4: ~0.12s/move
- MidGameBotV1 at depth 4: ~0.13s/move
- MidGameBotV2 at depth 5: ~2.17s/move
- MidGameBotV3 at depth 6: ~12.2s/move
- PyPy3 provides minimal speedup for this workload (~1% improvement)

Java bots are typically 2-3x faster than equivalent Python bots due to JIT compilation and lower-level optimizations.

## Dependencies

### Python
- `chess` (python-chess): Core chess library
- `fastapi`: Web backend
- `pydantic`: Request validation
- `uvicorn`: ASGI server

Install with:
```bash
pip3 install python-chess fastapi pydantic uvicorn
```

Or use existing virtual environment:
```bash
source .venv/bin/activate
```

### Java
- Maven project with Java 23
- `chesslib` v1.3.3 from jitpack.io
- JAR included in `chess_engine_java/libs/`

### Frontend
- See `web_app/frontend/package.json` for complete dependency list
- Key: Next.js 16, React 19, chess.js, react-chessboard, Tailwind CSS

## File Organization

- Root: Runner scripts, rendered game HTML files
- `bots/`: Python bot implementations
- `chess_engine_java/`: Complete Java Maven project
  - `src/main/java/org/`: All Java bot implementations
  - `libs/`: chesslib JAR
  - `target/`: Compiled classes
- `web_app/`: Full-stack web application
  - `frontend/`: Next.js app
  - `backend/`: FastAPI server
- `support/`: Shared utilities (TranspositionTable)
- `pieces-basic-png/`, `pieces-basic-svg/`: Chess piece assets
- `.venv/`: Python virtual environment
- `pypy-env/`: PyPy virtual environment (for performance testing)

## Current Branch

Working on `engine-hosting` branch which contains the web application implementation for hosting chess bots online.
