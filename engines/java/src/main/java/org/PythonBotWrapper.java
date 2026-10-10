package org;

import com.github.bhlangonijr.chesslib.Board;
import com.github.bhlangonijr.chesslib.move.Move;

import java.io.*;

public class PythonBotWrapper implements Runner.ChessBot {
    private Process pythonProcess;
    private BufferedReader in;
    private BufferedWriter out;
    private String name;

    public PythonBotWrapper(String pythonCommand, String scriptPath, String botClassName, String name) throws IOException {
        this.name = name;
        ProcessBuilder pb = new ProcessBuilder(pythonCommand, scriptPath, botClassName);
        this.pythonProcess = pb.start();
        this.in = new BufferedReader(new InputStreamReader(pythonProcess.getInputStream()));
        this.out = new BufferedWriter(new OutputStreamWriter(pythonProcess.getOutputStream()));
    }

    @Override
    public Move select_move(Board board) {
        try {
            // 1. Send FEN to Python
            System.out.println("Selecting Python");
            String fen = board.getFen();
            out.write(fen + "\n");
            out.flush();

            // 2. Read Move from Python
            String moveStr = in.readLine();
            System.out.println(moveStr);

            if (moveStr == null || moveStr.trim().isEmpty()) {
                System.err.println("Python bot crashed or returned empty string.");
                return null;
            }

            // Clean up string just in case
            moveStr = moveStr.trim();

            return new Move(moveStr, board.getSideToMove());
        } catch (IOException e) {
            throw new RuntimeException("Error communicating with Python bot", e);
        }
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public String getStats() {
        return "";
    }

    // Call this when shutting down the app
    public void close() {
        pythonProcess.destroy();
    }
}