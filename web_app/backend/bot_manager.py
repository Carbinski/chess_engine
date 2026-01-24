import sys
import os
import subprocess
import time
import chess

# Add root directory to path so we can import bots
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from bots.fast_search_v4 import FastBotV4

def get_python_move(fen: str):
    board = chess.Board(fen)
    if board.is_game_over():
        return None, 0, 0
    
    start_time = time.perf_counter()
    bot = FastBotV4() 
    # FastBotV4 likely has same interface as others: select_move(board)
    # FastBotV4 has a search depth of 4 by default in __init__
    move = bot.select_move(board)
    end_time = time.perf_counter()
    
    return move.uci(), end_time - start_time, bot.depth

def get_java_move(fen: str):
    # Path to chess_engine_java
    java_project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../chess_engine_java"))
    classpath = f"{java_project_path}/libs/chesslib-1.3.3.jar:{java_project_path}/target/classes"
    
    start_time = time.perf_counter()
    cmd = [
        "java",
        "-cp", classpath,
        "org.OneShotBot",
        fen
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.perf_counter()
    
    if result.returncode != 0:
        raise Exception(f"Java Bot Failed: {result.stderr}")
    
    lines = result.stdout.strip().splitlines()
    if not lines:
         raise Exception("Java Bot produced no output")
    
    move_uci = None
    for line in reversed(lines):
        line = line.strip()
        # Simple check for UCI-like string (e.g. e2e4, a7a8q)
        if 4 <= len(line) <= 5:
             move_uci = line
             break
             
    if not move_uci:
        move_uci = lines[-1] # Fallback

    # Java Bot depth is hardcoded or unknown from this wrapper, let's assume 4 for now or 0 if unknown
    # Based on previous context, BotV2 might be depth 4 as well.
    return move_uci, end_time - start_time, 4
