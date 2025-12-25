import chess
import chess.svg
from typing import Callable, Tuple

from bots.random_algo import RandomBot
from bots.aggressive_algo import AggressiveBot
from bots.dumb_eval_algo import DumbEvalBot
from bots.basic_search_algo import BasicSearchBot
from bots.fast_search_v2 import FastBotV2
from bots.fast_search_v3 import FastBotV3
from bots.fast_search_v4 import FastBotV4
from bots.midgame_v1 import MidGameBotV1
from bots.midgame_v2 import MidGameBotV2
from bots.midgame_v3 import MidGameBotV3
from bots.midgame_v4 import MidGameBotV4
from bots.minimal_v1 import MiniBotV1

ChessAlgo = Callable[[chess.Board], chess.Move]

import chess
import chess.svg

def play_game_with_computer(player_is_white: bool, algo, output_filename="chess_game.html"):
    board = chess.Board()

    css = """
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #f0f2f5; padding: 20px; }
        h1 { text-align: center; color: #333; margin-bottom: 10px; }
        .status { text-align: center; margin-bottom: 20px; color: #555; }
        .game-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }
        .move-card { 
            background: white; 
            padding: 15px; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
            text-align: center;
            width: 320px;
            transition: transform 0.2s;
        }
        .move-card:last-child { border: 2px solid #4CAF50; transform: scale(1.02); } /* Highlight latest state */
        .move-number { font-weight: bold; color: #888; font-size: 0.85em; margin-bottom: 5px; text-transform: uppercase; }
        .move-action { font-weight: 800; font-size: 1.3em; color: #2c3e50; margin-bottom: 10px; }
        .footer { margin-top: 40px; text-align: center; color: #aaa; }
    </style>
    """

    def update_file(content_history):
        full_html = f"<html><head>{css}</head><body>"
        full_html += f"<h1>Human ({'White' if player_is_white else 'Black'}) vs Bot</h1>"
        
        status_text = "Game in Progress" if not board.is_game_over() else f"Game Over: {board.result()}"
        full_html += f"<div class='status'>{status_text}</div>"
        
        full_html += "<div class='game-container'>"
        full_html += content_history
        full_html += "</div>"
        
        full_html += "<script>window.scrollTo(0, document.body.scrollHeight);</script>"
        full_html += "</body></html>"

        with open(output_filename, "w") as file:
            file.write(full_html)

    orientation = not player_is_white 
    
    history_html = f"""
    <div class='move-card'>
        <div class='move-number'>Start</div>
        <div class='move-action'>Game Start</div>
        {chess.svg.board(board, size=300, flipped=orientation)}
    </div>
    """
    
    update_file(history_html)
    print(f"Game started! Open {output_filename} in your browser.")
    print(f"Playing as: {'White' if player_is_white else 'Black'}")

    move_count = 1

    while not board.is_game_over():
        is_human_turn = (board.turn == chess.WHITE and player_is_white) or \
                        (board.turn == chess.BLACK and not player_is_white)

        current_color_name = "White" if board.turn == chess.WHITE else "Black"

        if is_human_turn:
            move = None
            while move is None:
                try:
                    move_str = input(f"\n({current_color_name}) Enter move (e.g. e2e4): ").replace(" ", "")
                    if move_str.lower() == "undo":
                        print("Undo not supported in this simple loop yet!")
                        continue
                        
                    candidate = chess.Move.from_uci(move_str)
                    
                    if candidate in board.legal_moves:
                        move = candidate
                    else:
                        print(f"Illegal move: {move_str}. Legal moves: {[m.uci() for m in board.legal_moves][:5]}...")
                except ValueError:
                    print("Invalid format. Use UCI (e.g., e2e4, a7a8q)")
        else:
            print(f"\n({current_color_name}) Bot is thinking...")
            move = algo.select_move(board)
            print(f"Bot played: {move.uci()}")

        san_move = board.san(move)
        display_text = f"{move_count}. {san_move}" if board.turn == chess.WHITE else f"{move_count}... {san_move}"
        
        board.push(move)

        svg = chess.svg.board(
            board, 
            size=300, 
            lastmove=move, 
            check=board.king(board.turn) if board.is_check() else None,
            flipped=orientation
        )

        history_html += f"""
        <div class='move-card'>
            <div class='move-number'>Ply {board.fullmove_number * 2 - (1 if board.turn == chess.BLACK else 0)}</div>
            <div class='move-action'>{current_color_name}: {san_move}</div>
            {svg}
        </div>
        """

        update_file(history_html)
        print(f"Move recorded. Refresh {output_filename} to see.")
        
        if board.turn == chess.WHITE:
            move_count += 1

    print("\nGame Over!")
    print("Result:", board.result())

def play_and_render_game(white_algo, black_algo, output_filename="game_report.html"):
    board = chess.Board()
    
    css = """
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; padding: 20px; }
        h1 { text-align: center; color: #333; }
        .game-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }
        .move-card { 
            background: white; 
            padding: 15px; 
            border-radius: 8px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            text-align: center;
            width: 320px;
        }
        .move-number { font-weight: bold; color: #777; font-size: 0.9em; margin-bottom: 5px;}
        .move-action { font-weight: bold; font-size: 1.2em; color: #333; margin-bottom: 10px; }
        .final-result { margin-top: 30px; text-align: center; font-size: 1.5em; font-weight: bold; color: #2c3e50;}
    </style>
    """

    html_content = f"<html><head>{css}</head><body>"
    html_content += "<h1>Chess Bot Game Report</h1>"
    html_content += "<div class='game-container'>"

    html_content += f"""
    <div class='move-card'>
        <div class='move-number'>Start</div>
        <div class='move-action'>Game Start</div>
        {chess.svg.board(board, size=300)}
    </div>
    """

    move_count = 1
    
    while not board.is_game_over():
        is_white = board.turn
        
        if is_white:
            move = white_algo.select_move(board)
            player_color = "White"
        else:
            move = black_algo.select_move(board)
            player_color = "Black"
        
        san_move = board.san(move)
        display_text = f"{move_count}. {san_move}" if is_white else f"{move_count}... {san_move}"

        board.push(move)

        svg = chess.svg.board(
            board, 
            size=300, 
            lastmove=move, 
            check=board.king(board.turn) if board.is_check() else None
        )

        html_content += f"""
        <div class='move-card'>
            <div class='move-number'>Ply {board.fullmove_number * 2 - (1 if is_white else 0)}</div>
            <div class='move-action'>{player_color}: {san_move}</div>
            {svg}
        </div>
        """
        
        if not is_white:
            move_count += 1

    html_content += "</div>" # End game-container
    
    html_content += f"<div class='final-result'>Result: {board.result()} <br> <span style='font-size:0.7em'>{board.outcome().termination.name}</span></div>"
    html_content += "</body></html>"

    with open(output_filename, "w") as file:
        file.write(html_content)
    print(f"HTML file {output_filename} successfully created.")

    return board.result()

def play_game(white_algo: ChessAlgo, black_algo: ChessAlgo) -> str:
    board = chess.Board()

    while (not board.is_game_over()):
        if board.turn: # If white move
            move = white_algo.select_move(board)
        else:
            move = black_algo.select_move(board)

        board.push(move)
    
    return board.result()

def run(algo1: ChessAlgo, algo2: ChessAlgo, total_games=1000) -> Tuple[float, float]:
    algo1_score, algo2_score, draws = 0.0, 0.0, 0.0
    switch_sides = total_games // 2

    for i in range(total_games):
        if i < switch_sides:
            result = play_game(white_algo=algo1, black_algo=algo2).split("-")

            if result[0] == "1/2":
                draws += 1
            else:
                algo1_score += float(result[0]) # White score
                algo2_score += float(result[1]) # Black score
        else:
            result = play_game(white_algo=algo2, black_algo=algo1).split("-")

            if result[0] == "1/2":
                draws += 1
            else:
                algo1_score += float(result[1]) # Black score
                algo2_score += float(result[0]) # White score

        # if (i + 1) % 4 == 0:
        print(f"Games: {i + 1} | Algo 1: {algo1_score} | Draws: {draws} | Algo 2: {algo2_score}")

    return algo1_score, draws, algo2_score

if __name__ == "__main__":
    bot_1 = MiniBotV1()
    bot_2 = FastBotV4()

    play_and_render_game(white_algo=bot_1, black_algo=bot_2)
    print(f"Total time: {bot_1.total_time}")
    print(f"Time per move: {bot_1.total_time / bot_1.total_moves}")
    # ~0.27 seconds per move for FastBotV2
    # ~0.13 seconds per move for FastBotV3
    # ~0.11657 seconds per move for FastBotV4 against FastBotV2 (Depth = 4)
    # ~0.13201 seconds per move for MidGameBotV1 against FastBotV4 (Depth = 4)
    # ~0.21402 seconds per move for MidGameBotV2 against FastBotV4 (Depth = 4)

    # ~2.17278 seconds per move for MidGameBotV2 against FastBotV4 (Depth = 5)

    # ~12.20536736248889  seconds per move for MidGameBotV3 against FastBotV4 (Depth = 6)
    # ~12.245790603436978 seconds per move for MidGameBotV3 against FastBotV4 (Depth = 6) w/ Pypy3
    # ~18.024962981533328 seconds per move for MidGameBotV4 against FastBotV4 (Depth = 6)
    # ~17.949637472189757 seconds per move for MidGameBotV4 against FastBotV4 (Depth = 6) w/ Pypy3

    # play_game(white_algo=bot_1, black_algo=bot_2)

    # results = run(algo1=bot_1, algo2=bot_2, total_games=10)

    # print("\n" + "*" * 50)
    # print(f"Algorithm 1: {results[0]}")
    # print(f"Draws: {results[1]}")
    # print(f"Algorithm 2: {results[2]}")

    # play_game_with_computer(True, bot_1)
    # print(f"Total positions searched: {bot_1.total_positions_searched}")
    # print(f"Total time: {bot_1.total_time}")
    # print(f"Time per move: {bot_1.total_time / bot_1.total_moves}")