"""UCI engine that plays a fixed move list. Used by tests and clock checks.

``python crossplay/scripted_uci.py [--sleep SECONDS] e2e4 e7e5``
"""

import sys
import time


def send(line):
    print(line, flush=True)


def main():
    args = sys.argv[1:]
    sleep_s = 0.0
    if args and args[0] == "--sleep":
        sleep_s = float(args[1])
        args = args[2:]
    moves = list(args)
    index = 0

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        parts = line.strip().split()
        if not parts:
            continue
        command = parts[0]
        if command == "uci":
            send("id name scripted")
            send("id author crossplay")
            send("uciok")
        elif command == "isready":
            send("readyok")
        elif command == "ucinewgame":
            index = 0
        elif command == "go":
            if sleep_s:
                time.sleep(sleep_s)
            if index >= len(moves):
                send("bestmove 0000")
            else:
                send("bestmove " + moves[index])
                index += 1
        elif command == "quit":
            break


if __name__ == "__main__":
    main()
