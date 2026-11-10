import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bots.aggressive_algo import AggressiveBot
from bots.basic_search_algo import BasicSearchBot
from bots.dumb_eval_algo import DumbEvalBot
from bots.fast_search_algo import FastBot
from bots.fast_search_v2 import FastBotV2
from bots.fast_search_v3 import FastBotV3
from bots.fast_search_v4 import FastBotV4
from bots.midgame_v1 import MidGameBotV1
from bots.midgame_v2 import MidGameBotV2
from bots.midgame_v3 import MidGameBotV3
from bots.midgame_v4 import MidGameBotV4
from bots.minimal_v1 import MiniBotV1
from bots.random_algo import RandomBot
from support.time_budget import budget_ms, depth_cap

BOTS = {
    "AggressiveBot": AggressiveBot,
    "BasicSearchBot": BasicSearchBot,
    "DumbEvalBot": DumbEvalBot,
    "FastBot": FastBot,
    "FastBotV2": FastBotV2,
    "FastBotV3": FastBotV3,
    "FastBotV4": FastBotV4,
    "MidGameBotV1": MidGameBotV1,
    "MidGameBotV2": MidGameBotV2,
    "MidGameBotV3": MidGameBotV3,
    "MidGameBotV4": MidGameBotV4,
    "MiniBotV1": MiniBotV1,
    "RandomBot": RandomBot,
}

_GO_VALUES = {
    "wtime",
    "btime",
    "winc",
    "binc",
    "movetime",
    "depth",
    "nodes",
    "mate",
    "movestogo",
}


def send(line):
    print(line, flush=True)


def apply_position(board, tokens):
    index = 1
    if index >= len(tokens):
        return
    if tokens[index] == "startpos":
        board.reset()
        index += 1
    elif tokens[index] == "fen":
        index += 1
        fen_parts = []
        while index < len(tokens) and tokens[index] != "moves":
            fen_parts.append(tokens[index])
            index += 1
        board.set_fen(" ".join(fen_parts))

    if index < len(tokens) and tokens[index] == "moves":
        for move in tokens[index + 1 :]:
            board.push_uci(move)


def time_remaining_ms(board, tokens):
    """Full clock for the side to move, in milliseconds. None if ``go`` has no clock."""
    values = {}
    index = 1
    while index < len(tokens):
        key = tokens[index]
        if key in _GO_VALUES and index + 1 < len(tokens):
            try:
                values[key] = int(tokens[index + 1])
            except ValueError:
                return None
            index += 2
            continue
        index += 1

    if "movetime" in values:
        return values["movetime"]
    if board.turn == chess.WHITE and "wtime" in values:
        return values["wtime"]
    if board.turn == chess.BLACK and "btime" in values:
        return values["btime"]
    return None


def first_legal(board):
    for move in board.legal_moves:
        return move
    return None


def choose_move(bot, board, remaining):
    """Return a move, or None when the position has no legal move."""
    if not any(board.legal_moves):
        return None

    budget = budget_ms(remaining)
    if budget is not None and budget <= 0:
        return first_legal(board)

    saved_depth = getattr(bot, "depth", None)
    bot._clock_budget_ms = budget
    if isinstance(saved_depth, int) and budget is not None:
        bot.depth = depth_cap(saved_depth, budget)
    try:
        move = bot.select_move(board)
    finally:
        bot._clock_budget_ms = None
        if isinstance(saved_depth, int):
            bot.depth = saved_depth

    if isinstance(move, chess.Move):
        return move
    return first_legal(board)


def main():
    bot_name = sys.argv[1] if len(sys.argv) > 1 else "RandomBot"
    if bot_name not in BOTS:
        print(f"Unknown bot: {bot_name}", file=sys.stderr)
        sys.exit(1)

    bot = BOTS[bot_name]()
    board = chess.Board()

    for line in sys.stdin:
        tokens = line.strip().split()
        if not tokens:
            continue
        command = tokens[0]

        if command == "uci":
            send(f"id name {bot_name}")
            send("id author chess_engine")
            send("uciok")
        elif command == "isready":
            send("readyok")
        elif command == "ucinewgame":
            bot = BOTS[bot_name]()
            board.reset()
        elif command == "position":
            try:
                apply_position(board, tokens)
            except ValueError as exc:
                print(f"Bad position: {exc}", file=sys.stderr)
        elif command == "go":
            remaining = time_remaining_ms(board, tokens)
            saved = sys.stdout
            sys.stdout = sys.stderr
            try:
                move = choose_move(bot, board, remaining)
            except Exception as exc:
                print(f"Search failed: {exc}", file=sys.stderr)
                move = None
            finally:
                sys.stdout = saved
            if isinstance(move, chess.Move):
                send(f"bestmove {move.uci()}")
            else:
                send("bestmove 0000")
        elif command == "quit":
            break


if __name__ == "__main__":
    main()
