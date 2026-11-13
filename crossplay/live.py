"""One referee for human and engine seats.

The board, the clock, and the result live here. Engines only return a move.
python-chess decides mate, stalemate, insufficient material, the 50-move
rule, and threefold repetition.
"""

import threading
import time
import uuid

import chess
import chess.pgn

from crossplay.catalog import HUMAN, get
from crossplay.uci_session import EngineError, UciSession

MAX_PLIES = 400


def _seconds(ms):
    if ms % 1000 == 0:
        return str(ms // 1000)
    text = f"{ms / 1000:.3f}".rstrip("0").rstrip(".")
    return text


def _side_to_move(board):
    return "w" if board.turn == chess.WHITE else "b"


def _outcome_reason(outcome):
    return outcome.termination.name.replace("_", " ").lower()


class LiveGame:
    def __init__(self, white_id, black_id, initial_ms, increment_ms, sessions, fen=None):
        white = get(white_id)
        black = get(black_id)
        self.id = uuid.uuid4().hex[:12]
        self.ids = {"w": white_id, "b": black_id}
        self.names = {"w": white["name"], "b": black["name"]}
        self.initial_ms = int(initial_ms)
        self.increment_ms = int(increment_ms)
        self.sessions = sessions
        self.board = chess.Board(fen) if fen else chess.Board()
        self.white_ms = self.initial_ms
        self.black_ms = self.initial_ms
        self.turn_started = time.monotonic()
        self.result = "*"
        self.reason = ""
        self.thinking = False
        self.closed = False
        self.driving = False
        self.generation = 0
        self.state_id = 1
        self.sans = []
        self._retired = False
        self.lock = threading.Lock()
        if self.board.is_game_over(claim_draw=True):
            self._adjudicate()

    def start(self):
        self._kick()

    def close(self):
        with self.lock:
            self.closed = True
            self.generation += 1
            self.driving = False
            self.thinking = False
        self._retire_engines_now()

    def _retire_engines_now(self):
        with self.lock:
            if self._retired:
                return
            self._retired = True
            sessions = [session for session in self.sessions.values() if session is not None]
            self.sessions = {"w": None, "b": None}
        for session in sessions:
            session.close()

    def human_move(self, uci):
        with self.lock:
            if self.closed:
                raise ValueError("game is closed")
            self._flag_if_needed()
            if self.result != "*":
                raise ValueError("game is over")
            side = _side_to_move(self.board)
            if self.ids[side] != HUMAN:
                raise ValueError("it is not the human's turn")
            try:
                move = chess.Move.from_uci(uci.strip())
            except ValueError as exc:
                raise ValueError("illegal move") from exc
            if move not in self.board.legal_moves:
                raise ValueError("illegal move")
            self._push(move)
        self._kick()

    def snapshot(self):
        with self.lock:
            if self._flag_if_needed():
                self.state_id += 1
            white_ms, black_ms = self._display_pair()
            ticking = None
            if self.result == "*":
                ticking = _side_to_move(self.board)
            last = None
            if self.board.move_stack:
                move = self.board.move_stack[-1]
                last = {
                    "from": chess.square_name(move.from_square),
                    "to": chess.square_name(move.to_square),
                }
            finished = self.result != "*"
            payload = {
                "id": self.id,
                "fen": self.board.fen(),
                "white": {"id": self.ids["w"], "name": self.names["w"]},
                "black": {"id": self.ids["b"], "name": self.names["b"]},
                "whiteMs": white_ms,
                "blackMs": black_ms,
                "ticking": ticking,
                "initialMs": self.initial_ms,
                "incrementMs": self.increment_ms,
                "moves": list(self.sans),
                "lastMove": last,
                "result": self.result,
                "reason": self.reason,
                "thinking": self.thinking,
                "stateId": self.state_id,
                "turn": _side_to_move(self.board),
                "pgn": self._pgn(),
            }
        if finished:
            self._retire_engines()
        return payload

    def _retire_engines(self):
        with self.lock:
            if self._retired or self.result == "*":
                return
            self._retired = True
            sessions = [session for session in self.sessions.values() if session is not None]
            self.sessions = {"w": None, "b": None}
        for session in sessions:
            session.close()

    def _kick(self):
        with self.lock:
            if self.closed or self.result != "*" or self.driving:
                return
            if self.ids[_side_to_move(self.board)] == HUMAN:
                return
            self.driving = True
        threading.Thread(target=self._drive, daemon=True).start()

    def _drive(self):
        try:
            while True:
                with self.lock:
                    if self.closed or self.result != "*":
                        self.driving = False
                        self.thinking = False
                        return
                    if self._flag_if_needed():
                        self.state_id += 1
                    if self.result != "*":
                        self.driving = False
                        self.thinking = False
                        return
                    side = _side_to_move(self.board)
                    if self.ids[side] == HUMAN:
                        self.driving = False
                        self.thinking = False
                        return
                    session = self.sessions[side]
                    fen = self.board.fen()
                    white_ms, black_ms = self._display_pair()
                    increment = self.increment_ms
                    generation = self.generation
                    self.thinking = True
                    self.state_id += 1
                try:
                    move, _extras = session.go(
                        fen,
                        white_ms,
                        black_ms,
                        increment,
                        increment,
                        timeout=max(white_ms if side == "w" else black_ms, 1) / 1000 + 2,
                    )
                except EngineError:
                    with self.lock:
                        self.thinking = False
                        self.driving = False
                        if not self.closed and generation == self.generation and self.result == "*":
                            self._set_loss(side, "engine failure")
                            self.state_id += 1
                    return
                with self.lock:
                    self.thinking = False
                    if self.closed or generation != self.generation or self.result != "*":
                        self.driving = False
                        return
                    if self._flag_if_needed():
                        self.state_id += 1
                        self.driving = False
                        return
                    if not _parse_legal(self.board, move):
                        self._set_loss(side, "illegal move")
                        self.state_id += 1
                        self.driving = False
                        return
                    self._push(chess.Move.from_uci(move))
                    if self.result != "*":
                        self.driving = False
                        return
                    if self.ids[_side_to_move(self.board)] == HUMAN:
                        self.driving = False
                        return
        except Exception:
            with self.lock:
                self.thinking = False
                self.driving = False
                if not self.closed and self.result == "*":
                    side = _side_to_move(self.board)
                    self._set_loss(side, "engine failure")
                    self.state_id += 1

    def _bank(self, side):
        return self.white_ms if side == "w" else self.black_ms

    def _set_bank(self, side, value):
        if side == "w":
            self.white_ms = value
        else:
            self.black_ms = value

    def _elapsed_ms(self):
        return int((time.monotonic() - self.turn_started) * 1000)

    def _display_pair(self):
        white_ms = self.white_ms
        black_ms = self.black_ms
        if self.result != "*":
            return white_ms, black_ms
        spent = self._elapsed_ms()
        if self.board.turn == chess.WHITE:
            white_ms = max(0, white_ms - spent)
        else:
            black_ms = max(0, black_ms - spent)
        return white_ms, black_ms

    def _flag_if_needed(self):
        if self.result != "*":
            return False
        side = _side_to_move(self.board)
        if self._elapsed_ms() > self._bank(side):
            self._set_loss(side, "time")
            return True
        return False

    def _push(self, move):
        side = _side_to_move(self.board)
        elapsed = self._elapsed_ms()
        bank = self._bank(side)
        if elapsed > bank:
            self._set_loss(side, "time")
            self.state_id += 1
            return
        san = self.board.san(move)
        self.board.push(move)
        self.sans.append(san)
        self._set_bank(side, bank - elapsed + self.increment_ms)
        self.turn_started = time.monotonic()
        self.generation += 1
        self.state_id += 1
        self._adjudicate()

    def _adjudicate(self):
        if len(self.board.move_stack) >= MAX_PLIES:
            self._set_draw("move limit")
            return
        outcome = self.board.outcome(claim_draw=True)
        if outcome is not None:
            self.result = outcome.result()
            self.reason = _outcome_reason(outcome)

    def _set_loss(self, side, reason):
        self.result = "0-1" if side == "w" else "1-0"
        self.reason = reason
        self.thinking = False
        if reason == "time":
            self._set_bank(side, 0)

    def _set_draw(self, reason):
        self.result = "1/2-1/2"
        self.reason = reason
        self.thinking = False

    def _pgn(self):
        game = chess.pgn.Game.from_board(self.board)
        game.headers["White"] = self.names["w"]
        game.headers["Black"] = self.names["b"]
        game.headers["Result"] = self.result
        game.headers["Termination"] = self.reason or "unterminated"
        game.headers["TimeControl"] = f"{_seconds(self.initial_ms)}+{_seconds(self.increment_ms)}"
        return str(game)


def _parse_legal(board, uci):
    if not uci or uci == "0000" or uci == "null":
        return False
    try:
        move = chess.Move.from_uci(uci)
    except ValueError:
        return False
    return move in board.legal_moves


def open_sessions(white_id, black_id):
    sessions = {"w": None, "b": None}
    try:
        if white_id != HUMAN:
            spec = get(white_id)
            sessions["w"] = UciSession(spec["command"], spec["name"])
            sessions["w"].new_game()
        if black_id != HUMAN:
            spec = get(black_id)
            sessions["b"] = UciSession(spec["command"], spec["name"])
            sessions["b"].new_game()
    except Exception:
        for session in sessions.values():
            if session is not None:
                session.close()
        raise
    return sessions


def start_match(white_id, black_id, initial_ms, increment_ms, fen=None):
    sessions = open_sessions(white_id, black_id)
    game = LiveGame(white_id, black_id, initial_ms, increment_ms, sessions, fen=fen)
    game.start()
    return game


class GameManager:
    def __init__(self):
        self._games = {}
        self._lock = threading.Lock()

    def create(self, white_id, black_id, initial_ms, increment_ms):
        game = start_match(white_id, black_id, initial_ms, increment_ms)
        with self._lock:
            self._games[game.id] = game
        return game

    def get(self, game_id):
        with self._lock:
            game = self._games.get(game_id)
        if game is None:
            raise KeyError(game_id)
        return game

    def close(self, game_id):
        game = self.get(game_id)
        game.close()
        with self._lock:
            self._games.pop(game_id, None)

    def close_all(self):
        with self._lock:
            games = list(self._games.values())
            self._games.clear()
        for game in games:
            game.close()


def wait_until_done(game, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        snap = game.snapshot()
        if snap["result"] != "*":
            return snap
        time.sleep(0.02)
    raise TimeoutError("match did not finish")
