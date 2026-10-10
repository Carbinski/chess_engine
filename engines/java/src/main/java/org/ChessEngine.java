package org;

import com.github.bhlangonijr.chesslib.Board;
import com.github.bhlangonijr.chesslib.Piece;
import com.github.bhlangonijr.chesslib.PieceType;
import com.github.bhlangonijr.chesslib.Side;
import com.github.bhlangonijr.chesslib.move.Move;
import com.github.bhlangonijr.chesslib.move.MoveGenerator;
import java.util.List; // Don't forget this for the List type!
import support.Support;

public class ChessEngine {
    public static void main(String[] args) {
        // 1. Initialize a board at the starting position
        Board board = new Board();

        // 2. Generate legal moves
        try {
            List<Move> moves = MoveGenerator.generateLegalMoves(board);
            System.out.println("Legal moves available: " + moves.size());

            // 3. Print the board to console (visual check)
            System.out.println(board.toString());

            System.out.println(Support.bitboardToString(board.getBitboard()));

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}