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


def send(line):
    print(line, flush=True)


def apply_position(board, tokens):
    index = 1
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
            board.reset()
        elif command == "position":
            apply_position(board, tokens)
        elif command == "go":
            saved = sys.stdout
            sys.stdout = sys.stderr
            try:
                move = bot.select_move(board)
            finally:
                sys.stdout = saved
            send(f"bestmove {move.uci()}")
        elif command == "quit":
            break


if __name__ == "__main__":
    main()
