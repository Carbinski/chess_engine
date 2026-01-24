package org;

import com.github.bhlangonijr.chesslib.Board;
import com.github.bhlangonijr.chesslib.move.Move;
import com.github.bhlangonijr.chesslib.Side;

import java.io.*;
import java.util.Scanner;

public class Runner {

    // Interface for all bots (Java or Python)
    public interface ChessBot {
        Move select_move(Board board);
        String getName();
        String getStats();
    }

    // Wrapper for your Java Bot
    public static class JavaBotWrapper implements ChessBot {
        private final JavaChessBot bot;
        private final String name;

        public JavaBotWrapper(JavaChessBot bot, String name) {
            this.bot = bot;
            this.name = name;
        }

        @Override
        public Move select_move(Board board) {
            return bot.select_move(board);
        }

        @Override
        public String getName() { return name; }

        @Override
        public String getStats() {
            return "Total time: " + bot.get_total_time() + "ms | Average time per move: " + bot.get_total_time() / bot.get_total_moves() + "ms";
        }
    }

    // ---------------------------------------------------------
    // 1. HUMAN VS COMPUTER
    // ---------------------------------------------------------
    public static void playHumanVsBot(boolean humanIsWhite, ChessBot bot, String outputFilename) {
        Board board = new Board();
        Scanner scanner = new Scanner(System.in);
        int moveCount = 1;

        // Initialize HTML
        StringBuilder htmlHistory = new StringBuilder();
        updateHtmlFile(outputFilename, htmlHistory.toString(), board.getFen(), "Game Start");
        System.out.println("Game started! Open " + outputFilename + " to view.");

        while (!board.isMated() && !board.isDraw()) {
            boolean isHumanTurn = (board.getSideToMove() == Side.WHITE && humanIsWhite) ||
                    (board.getSideToMove() == Side.BLACK && !humanIsWhite);

            Move move = null;
            String moveStr = "";

            if (isHumanTurn) {
                while (move == null) {
                    System.out.print("\nYour Move (e.g., e2e4): ");
                    String input = scanner.nextLine().trim();
                    try {
                        move = new Move(input, board.getSideToMove());
                        if (!board.isMoveLegal(move, true)) {
                            System.out.println("Illegal move.");
                            move = null;
                        }
                    } catch (Exception e) {
                        System.out.println("Invalid format. Use UCI (e2e4).");
                    }
                }
                moveStr = move.toString();
            } else {
                System.out.println("\nBot is thinking...");
                move = bot.select_move(board);
                moveStr = move.toString();
                System.out.println("Bot played: " + moveStr);
            }

            board.doMove(move);

            // Add to HTML
            String color = board.getSideToMove().flip() == Side.WHITE ? "White" : "Black";
            String cardHtml = String.format(
                    "<div class='move-card'><div class='move-number'>Ply %d</div>" +
                            "<div class='move-action'>%s: %s</div><div id='board-%d' class='board' style='width: 300px'></div></div>" +
                            "<script>Chessboard('board-%d', {position: '%s', showNotation: false, pieceTheme: 'pieces/{piece}.png', draggable: false});</script>",
                    (moveCount), color, moveStr, moveCount, moveCount, board.getFen()
            );
            htmlHistory.append(cardHtml);
            updateHtmlFile(outputFilename, htmlHistory.toString(), board.getFen(), "InProgress");

            moveCount++;
        }

        System.out.println("Game Over! Result: " + (board.isMated() ? "Checkmate" : "Draw"));
    }

    // ---------------------------------------------------------
    // 2. BOT VS BOT (Rendered)
    // ---------------------------------------------------------
    public static void playAndRenderGame(ChessBot white, ChessBot black, String outputFilename) {
        Board board = new Board();
        StringBuilder htmlHistory = new StringBuilder();
        int moveCount = 0;

        System.out.println("Starting match: " + white.getName() + " vs " + black.getName());

        // Initial Position
        String startFen = board.getFen();
        htmlHistory.append(String.format(
                "<div class='move-card'><div class='move-number'>Start</div>" +
                        "<div class='move-action'>Start</div><div id='board-start' class='board' style='width: 300px'></div></div>" +
                        "<script>Chessboard('board-start', {position: '%s', showNotation: false, pieceTheme: 'pieces/{piece}.png'});</script>", startFen
        ));

        while (!board.isMated() && !board.isDraw()) {
            ChessBot currentBot = (board.getSideToMove() == Side.WHITE) ? white : black;
            Move move = currentBot.select_move(board);
            board.doMove(move);
            moveCount++;

            String color = board.getSideToMove().flip() == Side.WHITE ? "White" : "Black";
            System.out.println("Ply " + moveCount + ": " + move.toString());

            String cardHtml = String.format(
                    "<div class='move-card'><div class='move-number'>Ply %d</div>" +
                            "<div class='move-action'>%s: %s</div><div id='board-%d' class='board' style='width: 300px'></div></div>" +
                            "<script>Chessboard('board-%d', {position: '%s', showNotation: false, pieceTheme: 'pieces/{piece}.png'});</script>",
                    moveCount, color, move.toString(), moveCount, moveCount, board.getFen()
            );

            htmlHistory.append(cardHtml);
        }

        updateHtmlFile(outputFilename, htmlHistory.toString(), board.getFen(), "Game Over");
        System.out.println("Match finished. See " + outputFilename);
    }

    // ---------------------------------------------------------
    // 3. BOT VS BOT (Tournament)
    // ---------------------------------------------------------
    public static void playTournament(ChessBot bot1, ChessBot bot2, int numberOfGames) {
        System.out.println("=============================================");
        System.out.println("Starting Tournament: " + bot1.getName() + " vs " + bot2.getName());
        System.out.println("Total Games: " + numberOfGames);
        System.out.println("=============================================\n");

        int bot1Wins = 0;
        int bot2Wins = 0;
        int draws = 0;

        for (int i = 1; i <= numberOfGames; i++) {
            // Determine colors: Bot 1 is White for odd games, Black for even
            ChessBot whiteBot = (i % 2 != 0) ? bot1 : bot2;
            ChessBot blackBot = (i % 2 != 0) ? bot2 : bot1;

            System.out.printf("Game %d/%d: %s (White) vs %s (Black)... ", i, numberOfGames, whiteBot.getName(), blackBot.getName());

            // Run a single simulation (Silent mode, no HTML)
            String result = playSingleSilentGame(whiteBot, blackBot);

            System.out.println("Result: " + result);

            // Tally score
            if (result.equals("Draw")) {
                draws++;
            } else if (result.equals("White")) {
                if (whiteBot == bot1) bot1Wins++; else bot2Wins++;
            } else if (result.equals("Black")) {
                if (blackBot == bot1) bot1Wins++; else bot2Wins++;
            }
        }

        System.out.println("\n=============================================");
        System.out.println("TOURNAMENT RESULTS");
        System.out.println("=============================================");
        System.out.printf("%s Wins: %d%n", bot1.getName(), bot1Wins);
        System.out.printf("%s Wins: %d%n", bot2.getName(), bot2Wins);
        System.out.printf("Draws:       %d%n", draws);
        System.out.println("=============================================");
    }


    private static String playSingleSilentGame(ChessBot white, ChessBot black) {
        Board board = new Board();
        int moves = 0;

        while (!board.isMated() && !board.isDraw() && moves < 200) {
            ChessBot currentBot = (board.getSideToMove() == Side.WHITE) ? white : black;
            Move move = currentBot.select_move(board);
            board.doMove(move);
            moves++;
        }

        if (board.isMated()) {
            return (board.getSideToMove() == Side.BLACK) ? "White" : "Black";
        } else {
            return "Draw";
        }
    }

    // ---------------------------------------------------------
    // HTML GENERATOR HELPER
    // ---------------------------------------------------------
    private static void updateHtmlFile(String filename, String historyHtml, String currentFen, String status) {
        String css = "body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 20px; }" +
                ".game-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; }" +
                ".move-card { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; }" +
                ".move-action { font-weight: 800; font-size: 1.2em; color: #2c3e50; margin-bottom: 10px; }";

        String template = "<html><head><style>" + css + "</style>" +
                "<link rel='stylesheet' href='https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.css'>" +
                "<script src='https://code.jquery.com/jquery-3.5.1.min.js'></script>" +
                "<script src='https://unpkg.com/@chrisoakman/chessboardjs@1.0.0/dist/chessboard-1.0.0.min.js'></script>" +
                "</head><body>" +
                "<h1 style='text-align:center'>Match Viewer</h1>" +
                "<div class='game-container'>" + historyHtml + "</div>" +
                "</body></html>";

        try (PrintWriter out = new PrintWriter(filename)) {
            out.println(template);
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
    }

    // ---------------------------------------------------------
    // MAIN METHOD TO RUN EVERYTHING
    // ---------------------------------------------------------
    public static void main(String[] args) throws Exception {

        ChessBot javaBotV1 = new JavaBotWrapper(new BasicBot_V1(4, true, true), "JavaV1");
        ChessBot javaBotV1_0 = new JavaBotWrapper(new BasicBot_V1(5, true, true), "JavaV1");
        ChessBot javaBotV2 = new JavaBotWrapper(new BasicBot_V2(5, true, true), "JavaV2");
        ChessBot javaBotV3 = new JavaBotWrapper(new BasicBot_V3(5, true, true), "JavaV3");
        ChessBot javaBotV4 = new JavaBotWrapper(new FastBot_V1(5, true, true), "JavaV4");
        ChessBot javaBotV5 = new JavaBotWrapper(new FastBot_V2(5, true, true), "JavaV5");
        ChessBot javaBotV6 = new JavaBotWrapper(new Bot_V1(5, true, true), "JavaV6");
        ChessBot javaBotV7 = new JavaBotWrapper(new Bot_V2(5, true, true), "JavaV7");


        // Mode A: Java vs Java
//        playAndRenderGame(javaBotV7, javaBotV6, "java_vs_java.html");
//        playAndRenderGame(javaBotV6, javaBotV7, "java_vs_java.html");
//        System.out.println(javaBotV7.getStats());
//        System.out.println(javaBotV6.getStats());
        // Plugged In : Minimal Background Tasks
        // BasicBot_V1 (Depth 6) vs BasicBot_V1 (Depth 4) : 3220 ms per move (111)
        // BasicBot_V2 (Depth 6) vs BasicBot_V1 (Depth 4) : 3995 ms per move (54)
        // BasicBot_V3 (Depth 6) vs BasicBot_V1 (Depth 4) : 600 ms per move (25)
        // BasicBot_V3 (Depth 6) vs BasicBot_V2 (Depth 6) : 374 ms per move vs 1806 ms per move (145)

        // BasicBot_V3 (Depth 6) : 786 ms
        // FastBot_V1 (Depth 6)  : 493 ms
        // FastBot_V2 (Depth 6) over 10 games is about 20 ms faster

        // FastBot_V2 (Depth 8) - 4185 ms
//
        playTournament(javaBotV6, javaBotV7, 10);
        System.out.println(javaBotV6.getStats());
        System.out.println(javaBotV7.getStats());

        // Mode B: Human vs Java
//        playHumanVsBot(false, javaBotV5, "human_vs_java.html");

    }
}