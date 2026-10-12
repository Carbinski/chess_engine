package org;

import com.github.bhlangonijr.chesslib.Board;
import com.github.bhlangonijr.chesslib.Side;
import com.github.bhlangonijr.chesslib.move.Move;

import java.io.PrintStream;
import java.util.Scanner;

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
                    board = new Board();
                    break;
                case "position":
                    board = applyPosition(tokens);
                    break;
                case "go":
                    long timeLeft = timeForSide(board, tokens);
                    PrintStream out = System.out;
                    System.setOut(System.err);
                    Move move;
                    try {
                        move = bot.select_move(board, timeLeft);
                    } finally {
                        System.setOut(out);
                    }
                    send("bestmove " + move);
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

    private static Board applyPosition(String[] tokens) {
        Board board = new Board();
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
            board.loadFromFen(fen.toString());
        }

        if (index < tokens.length && tokens[index].equals("moves")) {
            index++;
            while (index < tokens.length) {
                board.doMove(new Move(tokens[index], board.getSideToMove()));
                index++;
            }
        }
        return board;
    }

    private static long timeForSide(Board board, String[] tokens) {
        long wtime = 1000;
        long btime = 1000;
        long movetime = -1;
        for (int i = 1; i < tokens.length - 1; i++) {
            if (tokens[i].equals("wtime")) {
                wtime = Long.parseLong(tokens[++i]);
            } else if (tokens[i].equals("btime")) {
                btime = Long.parseLong(tokens[++i]);
            } else if (tokens[i].equals("movetime")) {
                movetime = Long.parseLong(tokens[++i]);
            }
        }
        if (movetime >= 0) {
            return movetime;
        }
        return board.getSideToMove() == Side.WHITE ? wtime : btime;
    }

    private static void send(String line) {
        System.out.println(line);
        System.out.flush();
    }
}
