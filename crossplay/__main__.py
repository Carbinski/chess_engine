"""Play engines against each other from the command line.

Examples:

    python -m crossplay list
    python -m crossplay conform
    python -m crossplay match python_random java_bot_v2 --time 10000 --inc 100
    python -m crossplay roundrobin python_random java_bot_v2 --games 2 --time 5000
    python -m crossplay fastchess python_random java_bot_v2 cpp_search
"""

import argparse
import shlex
import sys

from crossplay.catalog import engines, get
from crossplay.conform import conform
from crossplay.live import start_match, wait_until_done
from crossplay.uci_session import UciSession


def _cmd_list(_args):
    rows = engines(available_only=False)
    ready = {row["id"] for row in engines(available_only=True)}
    for row in rows:
        mark = "ready" if row["id"] in ready else "unavailable"
        print(f"{row['id']}\t{row['language']}\t{mark}\t{row['name']}")


def _cmd_conform(_args):
    failed = 0
    for row in engines(available_only=True):
        print(f"conform {row['id']} ...", flush=True)
        session = UciSession(row["command"], row["name"])
        try:
            conform(session)
        except Exception as exc:
            failed += 1
            print(f"FAIL {row['id']}: {exc}", file=sys.stderr)
        else:
            print(f"ok {row['id']}")
        finally:
            session.close()
    if failed:
        raise SystemExit(1)


def _play(white, black, initial_ms, increment_ms, fen=None):
    # Two clocks plus a small margin so a stalled engine is forfeited first.
    timeout = (initial_ms / 1000) * 4 + 30
    game = start_match(white, black, initial_ms, increment_ms, fen=fen)
    try:
        return wait_until_done(game, timeout)
    finally:
        game.close()


def _cmd_match(args):
    snap = _play(args.white, args.black, args.time, args.inc, fen=args.fen)
    print(f"{snap['result']}  {snap['reason']}")
    print(snap["pgn"])
    if args.out:
        with open(args.out, "w") as handle:
            handle.write(snap["pgn"])
            if not snap["pgn"].endswith("\n"):
                handle.write("\n")


def _points(result, white_is_first):
    if result == "1/2-1/2":
        return 0.5
    if result == "1-0":
        return 1.0 if white_is_first else 0.0
    if result == "0-1":
        return 0.0 if white_is_first else 1.0
    return 0.0


def _cmd_roundrobin(args):
    ids = args.engines
    if len(ids) < 2:
        raise SystemExit("roundrobin needs two engines")
    scores = {engine_id: 0.0 for engine_id in ids}
    for index, first in enumerate(ids):
        for second in ids[index + 1 :]:
            for game_index in range(args.games):
                if game_index % 2 == 0:
                    white, black = first, second
                    first_is_white = True
                else:
                    white, black = second, first
                    first_is_white = False
                snap = _play(white, black, args.time, args.inc)
                scores[first] += _points(snap["result"], first_is_white)
                scores[second] += _points(snap["result"], not first_is_white)
                print(
                    f"{snap['white']['name']} vs {snap['black']['name']}: "
                    f"{snap['result']} ({snap['reason']})"
                )
    print()
    for engine_id, score in scores.items():
        print(f"{get(engine_id)['name']}: {score}")


def _cmd_fastchess(args):
    parts = ["tools/fastchess/fastchess"]
    for engine_id in args.engines:
        spec = get(engine_id)
        executable = shlex.quote(spec["command"][0])
        part = f"-engine cmd={executable} name={engine_id}"
        for arg in spec["command"][1:]:
            part += " arg=" + shlex.quote(arg)
        parts.append(part)
    parts.append("-each tc=10+0.1 -rounds 20 -repeat -concurrency 1")
    print(" \\\n  ".join(parts))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m crossplay")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="show the engine catalog")
    sub.add_parser("conform", help="check every available engine speaks UCI")

    match = sub.add_parser("match", help="play one game")
    match.add_argument("white")
    match.add_argument("black")
    match.add_argument("--time", type=int, default=60000, help="milliseconds per side")
    match.add_argument("--inc", type=int, default=0, help="increment in milliseconds")
    match.add_argument("--fen", default=None)
    match.add_argument("--out", help="also write the PGN to this path")

    robin = sub.add_parser("roundrobin", help="play each pair, alternating colors")
    robin.add_argument("engines", nargs="+")
    robin.add_argument("--games", type=int, default=2)
    robin.add_argument("--time", type=int, default=60000)
    robin.add_argument("--inc", type=int, default=0)

    chess = sub.add_parser("fastchess", help="print a fastchess command for these engines")
    chess.add_argument("engines", nargs="+")

    args = parser.parse_args(argv)
    {
        "list": _cmd_list,
        "conform": _cmd_conform,
        "match": _cmd_match,
        "roundrobin": _cmd_roundrobin,
        "fastchess": _cmd_fastchess,
    }[args.command](args)


if __name__ == "__main__":
    main()
