"""Long-lived UCI process."""

import queue
import subprocess
import threading
import time
from collections import deque


class EngineError(Exception):
    pass


class EngineTimeout(EngineError):
    pass


class EngineCrashed(EngineError):
    pass


class UciSession:
    def __init__(self, command, name, cwd=None):
        self.command = list(command)
        self.name = name
        self._closed = False
        self._write_lock = threading.Lock()
        self._lines = queue.Queue()
        self._stderr = deque(maxlen=40)
        self.proc = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            cwd=cwd,
        )
        threading.Thread(target=self._pump_stdout, daemon=True).start()
        threading.Thread(target=self._pump_stderr, daemon=True).start()
        self._send("uci")
        self._read_until(lambda line: line == "uciok", 10)
        self.ready()

    def _pump_stdout(self):
        stream = self.proc.stdout
        if stream is None:
            self._lines.put(None)
            return
        for line in stream:
            self._lines.put(line.strip())
        self._lines.put(None)

    def _pump_stderr(self):
        stream = self.proc.stderr
        if stream is None:
            return
        for line in stream:
            self._stderr.append(line.rstrip())

    def stderr_tail(self):
        return "\n".join(self._stderr)

    def _send(self, line):
        with self._write_lock:
            if self._closed or self.proc.stdin is None or self.proc.poll() is not None:
                raise EngineCrashed(self.name + " is not running\n" + self.stderr_tail())
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()

    def _read_until(self, predicate, timeout):
        deadline = time.monotonic() + timeout
        seen = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineTimeout(self.name + " timed out\n" + self.stderr_tail())
            try:
                line = self._lines.get(timeout=remaining)
            except queue.Empty:
                raise EngineTimeout(self.name + " timed out\n" + self.stderr_tail())
            if line is None:
                raise EngineCrashed(self.name + " exited\n" + self.stderr_tail())
            if predicate(line):
                return line, seen
            seen.append(line)

    def ready(self):
        self._send("isready")
        self._read_until(lambda line: line == "readyok", 10)

    def new_game(self):
        self._send("ucinewgame")
        self.ready()

    def send(self, line):
        self._send(line)

    def go(self, fen, wtime, btime, winc, binc, timeout):
        self._send("position fen " + fen)
        return self.go_line(
            f"go wtime {int(wtime)} btime {int(btime)} winc {int(winc)} binc {int(binc)}",
            timeout,
        )

    def go_line(self, line, timeout):
        self._send(line)
        reply, extras = self._read_until(lambda item: item.startswith("bestmove"), timeout)
        parts = reply.split()
        move = parts[1] if len(parts) > 1 else "0000"
        return move, extras

    def close(self):
        if self._closed:
            return
        self._closed = True
        proc = self.proc
        try:
            if proc.poll() is None and proc.stdin is not None:
                proc.stdin.write("quit\n")
                proc.stdin.flush()
        except Exception:
            pass
        try:
            if proc.poll() is None:
                proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=2)
        except Exception:
            pass
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            try:
                if stream is not None:
                    stream.close()
            except Exception:
                pass
