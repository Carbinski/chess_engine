import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engines" / "python"))

from support.time_budget import budget_ms, depth_cap
from crossplay.catalog import engines, get
from crossplay.conform import conform
from crossplay.live import LiveGame, wait_until_done
from crossplay.uci_session import UciSession


def scripted(*args):
    return [sys.executable, str(ROOT / "crossplay" / "scripted_uci.py"), *args]


def _wait_for(game, predicate, timeout):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = game.snapshot()
        if predicate(last):
            return last
        time.sleep(0.02)
    raise AssertionError(last)


class BudgetTests(unittest.TestCase):
    def test_divisor_matches_cpp(self):
        self.assertIsNone(budget_ms(None))
        self.assertEqual(budget_ms(0), 0)
        self.assertEqual(budget_ms(10000), 133)
        self.assertEqual(budget_ms(74), 0)

    def test_depth_cap_never_raises_depth(self):
        self.assertEqual(depth_cap(6, 15000), 6)
        self.assertEqual(depth_cap(6, 2000), 5)
        self.assertEqual(depth_cap(6, 200), 4)
        self.assertEqual(depth_cap(3, 15000), 3)
        self.assertEqual(depth_cap(4, 0), 1)


class RefereeTests(unittest.TestCase):
    def test_scholars_mate(self):
        white = UciSession(scripted("e2e4", "f1c4", "d1h5", "h5f7"), "white")
        black = UciSession(scripted("e7e5", "a7a6", "a6a5"), "black")
        game = LiveGame(
            "python_random",
            "python_random",
            60000,
            100,
            {"w": white, "b": black},
        )
        game.start()
        try:
            snap = wait_until_done(game, 10)
        finally:
            game.close()
        self.assertEqual(snap["result"], "1-0")
        self.assertEqual(snap["reason"], "checkmate")
        self.assertEqual(snap["moves"], ["e4", "e5", "Bc4", "a6", "Qh5", "a5", "Qxf7#"])
        self.assertIn("1-0", snap["pgn"])
        self.assertIn('[TimeControl "60+0.1"]', snap["pgn"])

    def test_time_forfeit(self):
        white = UciSession(scripted("--sleep", "0.4", "e2e4"), "slow")
        black = UciSession(scripted("e7e5"), "black")
        game = LiveGame(
            "python_random",
            "python_random",
            200,
            0,
            {"w": white, "b": black},
        )
        game.start()
        try:
            snap = wait_until_done(game, 5)
        finally:
            game.close()
        self.assertEqual(snap["result"], "0-1")
        self.assertEqual(snap["reason"], "time")
        self.assertEqual(snap["moves"], [])
        self.assertEqual(snap["whiteMs"], 0)

    def test_illegal_engine_move_loses(self):
        white = UciSession(scripted("e2e5"), "illegal")
        black = UciSession(scripted("e7e5"), "black")
        game = LiveGame(
            "python_random",
            "python_random",
            60000,
            0,
            {"w": white, "b": black},
        )
        game.start()
        try:
            snap = wait_until_done(game, 5)
        finally:
            game.close()
        self.assertEqual(snap["result"], "0-1")
        self.assertEqual(snap["reason"], "illegal move")

    def test_human_move_then_engine(self):
        black = UciSession(scripted("e7e5"), "black")
        game = LiveGame("human", "python_random", 60000, 0, {"w": None, "b": black})
        try:
            game.start()
            game.human_move("e2e4")
            snap = _wait_for(game, lambda item: len(item["moves"]) >= 2, 5)
            with self.assertRaises(ValueError):
                game.human_move("e2e4")
        finally:
            game.close()
        self.assertEqual(snap["moves"][:2], ["e4", "e5"])
        self.assertEqual(snap["result"], "*")


class TimedBotTests(unittest.TestCase):
    def test_midgame_v5_uses_the_clock(self):
        sys.path.insert(0, str(ROOT / "engines" / "python"))
        import chess
        from bots.midgame_v5 import MidGameBotV5

        bot = MidGameBotV5()
        bot.stat_tracking = False
        board = chess.Board()
        started = time.perf_counter()
        move = bot.select_move(board, time_remaining_ms=0)
        self.assertLess(time.perf_counter() - started, 0.5)
        self.assertIn(move, board.legal_moves)

        started = time.perf_counter()
        move = bot.select_move(board, time_remaining_ms=3000)
        self.assertLess(time.perf_counter() - started, 2.0)
        self.assertIn(move, board.legal_moves)


class ConformTests(unittest.TestCase):
    def test_python_random_and_fast(self):
        for engine_id in ("python_random", "python_fast_v4", "python_midgame_v5"):
            spec = get(engine_id)
            session = UciSession(spec["command"], spec["name"])
            try:
                conform(session)
            finally:
                session.close()

    def test_java_bot_v5_when_built(self):
        ready = {row["id"] for row in engines()}
        if "java_bot_v5" not in ready:
            self.skipTest("Java classes are not built")
        spec = get("java_bot_v5")
        session = UciSession(spec["command"], spec["name"])
        try:
            conform(session)
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
