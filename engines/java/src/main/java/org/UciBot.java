package org;

import com.github.bhlangonijr.chesslib.Board;
import com.github.bhlangonijr.chesslib.Side;
import com.github.bhlangonijr.chesslib.move.Move;

import java.io.PrintStream;
import java.util.List;
import java.util.Scanner;

import support.ClockBudget;

public class UciBot {
    public static void main(String[] args) {
        String botName = args.length > 0 ? args[0] : "Bot_V2";
        JavaChessBot bot = createBot(botName);
        if (bot == null) {
            System.err.println("Unknown bot: " + botName);
            System.exit(1);
        }

        Board board = new Board();
        Scanner in = new Scanner(System.in);
        while (in.hasNextLine()) {
            String line = in.nextLine().trim();
            if (line.isEmpty()) {
                continue;
            }
            String[] tokens = line.split("\\s+");
            switch (tokens[0]) {
                case "uci":
                    send("id name " + botName);
                    send("id author chess_engine");
                    send("uciok");
                    break;
                case "isready":
                    send("readyok");
                    break;
                case "ucinewgame":
                    bot = createBot(botName);
                    board = new Board();
                    break;
                case "position":
                    board = applyPosition(tokens);
                    break;
                case "go":
                    long timeLeft = timeForSide(board, tokens);
                    if (ClockBudget.budgetMs(timeLeft) <= 0) {
                        send(firstLegal(board));
                        break;
                    }
                    int nominalDepth = nominalDepth(bot);
                    if (nominalDepth > 0) {
                        setDepth(bot, ClockBudget.depthCap(nominalDepth, ClockBudget.budgetMs(timeLeft)));
                    }
                    PrintStream out = System.out;
                    System.setOut(System.err);
                    Move move = null;
                    try {
                        move = bot.select_move(board, timeLeft);
                    } catch (RuntimeException ex) {
                        System.err.println("Search failed: " + ex.getMessage());
                    } finally {
                        System.setOut(out);
                        if (nominalDepth > 0) {
                            setDepth(bot, nominalDepth);
                        }
                    }
                    if (move == null) {
                        send("bestmove 0000");
                    } else {
                        send("bestmove " + move);
                    }
                    break;
                case "quit":
                    return;
                default:
                    break;
            }
        }
    }

    private static JavaChessBot createBot(String name) {
        switch (name) {
            case "BasicBot_V1":
                return new BasicBot_V1(5, false, false);
            case "BasicBot_V2":
                return new BasicBot_V2(5, false, false);
            case "BasicBot_V3":
                return new BasicBot_V3(5, false, false);
            case "FastBot_V1":
                return new FastBot_V1(5, false, false);
            case "FastBot_V2":
                return new FastBot_V2(5, false, false);
            case "Bot_V1":
                return new Bot_V1(5, false, false);
            case "Bot_V2":
                return new Bot_V2(5, false, false);
            case "Bot_V3":
                return new Bot_V3(6, false, false);
            case "Bot_V4":
                return new Bot_V4(6, false, false);
            case "TimeBot_V1":
                return new TimeBot_V1(64, false, false);
            default:
                return null;
        }
    }

    /** Fixed-depth bots that do not watch the clock. Time-aware bots return -1. */
    private static int nominalDepth(JavaChessBot bot) {
        if (bot instanceof BasicBot_V1 basic) {
            return basic.depth;
        }
        if (bot instanceof BasicBot_V2 basic) {
            return basic.depth;
        }
        return -1;
    }

    private static void setDepth(JavaChessBot bot, int depth) {
        if (bot instanceof BasicBot_V1 basic) {
            basic.depth = depth;
        } else if (bot instanceof BasicBot_V2 basic) {
            basic.depth = depth;
        }
    }

    private static String firstLegal(Board board) {
        List<Move> moves = board.legalMoves();
        if (moves.isEmpty()) {
            return "bestmove 0000";
        }
        return "bestmove " + moves.get(0);
    }

    private static Board applyPosition(String[] tokens) {
        Board board = new Board();
        if (tokens.length < 2) {
            return board;
        }
        int index = 1;
        if (tokens[index].equals("startpos")) {
            index++;
        } else if (tokens[index].equals("fen")) {
            index++;
            StringBuilder fen = new StringBuilder();
            while (index < tokens.length && !tokens[index].equals("moves")) {
                if (fen.length() > 0) {
                    fen.append(' ');
                }
                fen.append(tokens[index++]);
            }
            try {
                board.loadFromFen(fen.toString());
            } catch (RuntimeException ex) {
                System.err.println("Bad FEN: " + fen);
                return new Board();
            }
        }

        if (index < tokens.length && tokens[index].equals("moves")) {
            index++;
            while (index < tokens.length) {
                try {
                    Move move = new Move(tokens[index], board.getSideToMove());
                    if (!board.doMove(move)) {
                        System.err.println("Illegal move: " + tokens[index]);
                        break;
                    }
                } catch (RuntimeException ex) {
                    System.err.println("Bad move: " + tokens[index]);
                    break;
                }
                index++;
            }
        }
        return board;
    }

    private static long timeForSide(Board board, String[] tokens) {
        long wtime = -1;
        long btime = -1;
        long movetime = -1;
        try {
            for (int i = 1; i < tokens.length - 1; i++) {
                if (tokens[i].equals("wtime")) {
                    wtime = Long.parseLong(tokens[++i]);
                } else if (tokens[i].equals("btime")) {
                    btime = Long.parseLong(tokens[++i]);
                } else if (tokens[i].equals("movetime")) {
                    movetime = Long.parseLong(tokens[++i]);
                } else if (tokens[i].equals("winc") || tokens[i].equals("binc")
                        || tokens[i].equals("movestogo") || tokens[i].equals("depth")
                        || tokens[i].equals("nodes") || tokens[i].equals("mate")) {
                    i++;
                }
            }
        } catch (NumberFormatException ex) {
            return 0;
        }
        if (movetime >= 0) {
            return movetime;
        }
        long remaining = board.getSideToMove() == Side.WHITE ? wtime : btime;
        // A bare `go` has no clock. Budget 0 matches the C++ engine, which then
        // plays its first legal move.
        return remaining >= 0 ? remaining : 0;
    }

    private static void send(String line) {
        System.out.println(line);
        System.out.flush();
    }
}
