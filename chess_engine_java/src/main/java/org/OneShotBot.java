package org;

import com.github.bhlangonijr.chesslib.Board;
import com.github.bhlangonijr.chesslib.move.Move;

public class OneShotBot {
    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java org.OneShotBot \"<FEN>\" [BotName]");
            System.exit(1);
        }

        String fen = args[0];
        String botName = (args.length > 1) ? args[1] : "Bot_V2";

        try {
            Board board = new Board();
            board.loadFromFen(fen);

            Runner.ChessBot bot;

            switch (botName) {
                case "BasicBot_V3":
                    bot = new Runner.JavaBotWrapper(new BasicBot_V3(5, false, false), "BasicBot_V3");
                    break;
                case "FastBot_V2":
                    bot = new Runner.JavaBotWrapper(new FastBot_V2(5, false, false), "FastBot_V2");
                    break;
                case "Bot_V2":
                default:
                    // Default to Bot_V2 with depth 5, stats=false, random=false
                    bot = new Runner.JavaBotWrapper(new Bot_V2(5, false, false), "Bot_V2");
                    break;
            }
            
            Move move = bot.select_move(board);
            System.out.println(move.toString());
            
        } catch (Exception e) {
            System.err.println("Error processing FEN: " + fen);
            e.printStackTrace();
            System.exit(1);
        }
    }
}
