import sys
import chess

# --- IMPORT YOUR BOTS HERE ---
from bots.random_algo import RandomBot
from bots.fast_search_v4 import FastBotV4
from bots.midgame_v4 import MidGameBotV4
# Add other imports as needed

def get_bot_instance(bot_name):
    # Mapping string names to Bot Classes
    if bot_name == "RandomBot": return RandomBot()
    if bot_name == "FastBotV4": return FastBotV4()
    if bot_name == "MidGameBotV4": return MidGameBotV4()
    # Add others...
    return RandomBot() # Default

def main():
    # 1. Read the specific bot class name from command line args
    bot_name = "RandomBot"
    if len(sys.argv) > 1:
        bot_name = sys.argv[1]
    
    bot = get_bot_instance(bot_name)
    
    # 2. Loop forever: Read FEN -> Think -> Print Move
    while True:
        try:
            # Read FEN from stdin (sent by Java)
            fen = sys.stdin.readline()
            if not fen: break # End of stream
            fen = fen.strip()
            
            board = chess.Board(fen)
            
            # Select move
            move = bot.select_move(board)
            
            # Print move to stdout (Java reads this)
            print(move.uci())
            sys.stdout.flush()
            
        except Exception as e:
            # Write error to stderr so Java can see it if needed
            sys.stderr.write(str(e))
            break

if __name__ == "__main__":
    main()