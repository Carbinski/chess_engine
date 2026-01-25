import sys
import os
import subprocess
import time
import chess
import random

# Add root directory to path so we can import bots
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from bots.random_algo import RandomBot
from bots.aggressive_algo import AggressiveBot
from bots.dumb_eval_algo import DumbEvalBot
from bots.basic_search_algo import BasicSearchBot
from bots.fast_search_v2 import FastBotV2
from bots.fast_search_v4 import FastBotV4
from bots.midgame_v1 import MidGameBotV1

def get_python_move(fen: str, bot_id: str):
    board = chess.Board(fen)
    if board.is_game_over():
        return None, 0, 0
    
    start_time = time.perf_counter()
    
    bot = None
    depth = 0
    
    if bot_id == "python_random":
        bot = RandomBot()
    elif bot_id == "python_aggressive":
        bot = AggressiveBot()
    elif bot_id == "python_dumb_eval":
        bot = DumbEvalBot()
    elif bot_id == "python_basic_search":
        bot = BasicSearchBot()
        depth = 3 # Default depth for BasicSearchBot
    elif bot_id == "python_fast_v2":
        bot = FastBotV2()
        depth = 5 # Default depth for FastBotV2
    elif bot_id == "python_midgame_v1":
        bot = MidGameBotV1()
        depth = 5 # Default depth for MidGameBotV1
    else: 
        # Default fallback
        bot = FastBotV4()
        depth = 4

    move = bot.select_move(board)
    end_time = time.perf_counter()
    
    # Some bots might return a string or object, ensure we get UCI
    if hasattr(move, 'uci'):
        uci = move.uci()
    else:
        uci = str(move)
        
    return uci, end_time - start_time, depth

def get_java_move(fen: str, bot_id: str, time_limit: int = 5000):
    # Path to chess_engine_java
    java_project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../chess_engine_java"))
    classpath = f"{java_project_path}/libs/chesslib-1.3.3.jar:{java_project_path}/target/classes"
    
    # Map frontend bot_id to Java OneShotBot names
    java_bot_name = "Bot_V2" # Default
    if bot_id == "java_basic_v3":
        java_bot_name = "BasicBot_V3"
    elif bot_id == "java_fast_v2":
        java_bot_name = "FastBot_V2"
    elif bot_id == "java_bot_v2":
        java_bot_name = "Bot_V2"
    elif bot_id == "java_time_bot":
        java_bot_name = "TimeBot_V1"

    start_time = time.perf_counter()
    cmd = [
        "java",
        "-cp", classpath,
        "org.OneShotBot",
        fen,
        java_bot_name,
        str(time_limit)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.perf_counter()
    
    if result.returncode != 0:
        raise Exception(f"Java Bot Failed: {result.stderr}")
    
    lines = result.stdout.strip().splitlines()
    if not lines:
         raise Exception("Java Bot produced no output")
    
    move_uci = None
    max_depth = 0
    
    import re
    depth_pattern = re.compile(r"Depth (\d+) completed")
    
    for line in lines:
        line = line.strip()
        
        # Check for depth info
        match = depth_pattern.search(line)
        if match:
             d = int(match.group(1))
             if d > max_depth: 
                 max_depth = d
                 
    # Reverse loop to find the move (last valid UCI string)
    for line in reversed(lines):
        line = line.strip()
        # Simple check for UCI-like string (e.g. e2e4, a7a8q)
        if 4 <= len(line) <= 5 and not "Depth" in line:
             move_uci = line
             break
             
    if not move_uci:
        move_uci = lines[-1] # Fallback
        
    if max_depth == 0:
        max_depth = 5 # Fallback if parsing fails

    return move_uci, end_time - start_time, max_depth
