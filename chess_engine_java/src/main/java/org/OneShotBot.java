package org;

import com.github.bhlangonijr.chesslib.Board;
import com.github.bhlangonijr.chesslib.move.Move;

public class OneShotBot {
    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java org.OneShotBot \"<FEN>\"");
            System.exit(1);
        }

        String fen = args[0];
        try {
            Board board = new Board();
            board.loadFromFen(fen);

            // Using Bot_V2 with depth 5, stats=false, random=false (or similar defaults)
            // Constructor signature based on Runner.java: new Bot_V2(int depth, boolean active, boolean random)
            // Assuming "active" means stat tracking or something, setting false for speed/silence if possible, 
            // but Runner used 'true' for 'active'. Let's stick to what Runner did: (5, true, false)
            // Actually, for a one-shot, we might not want stats printed to stdout.
            // Let's assume the bot prints stats to stdout if active=true.
            // I'll check Bot_V2 source if needed, but safe bet is to try to minimize noise.
            // Let's use depth 5 for now.
            
            Runner.ChessBot bot = new Runner.JavaBotWrapper(new Bot_V2(5, false, false), "OneShot");
            
            Move move = bot.select_move(board);
            System.out.println(move.toString());
            
        } catch (Exception e) {
            System.err.println("Error processing FEN: " + fen);
            e.printStackTrace();
            System.exit(1);
        }
    }
}
