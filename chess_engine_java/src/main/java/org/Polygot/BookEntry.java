package org.Polygot;

import com.github.bhlangonijr.chesslib.PieceType;
import com.github.bhlangonijr.chesslib.Side;
import com.github.bhlangonijr.chesslib.Square;
import com.github.bhlangonijr.chesslib.move.Move;

/**
 * Represents a single entry in a Polygot opening book.
 * Each entry contains:
 *  - 8 bytes: Zobrist Key (stored as long)
 *  - 2 bytes: Move (encoded)
 *  - 2 bytes: Weight
 *  - 4 bytes: Learn (unsued)
 */
public class BookEntry implements Comparable<BookEntry> {

    private final long key;
    private final int move;
    private final int weight;

    public BookEntry(long key, int move, int weight) {
        this.key = key;
        this.move = move;
        this.weight = weight;
    }

    /**
     * @param data 16-byte array representing one entry
     */
    public BookEntry(byte[] data) {
        // Polygot is Big Endian
        this.key = makeLong(data, 0);
        this.move = makeShort(data, 8);
        this.weight = makeShort(data, 10);
        //  Ignore the 'learn' field (bytes 12-15)
    }

    private static long makeLong(byte[] b, int offset) {
        return ((((long) b[offset]) & 0xFF) << 56) |
               ((((long) b[offset + 1]) & 0xFF) << 48) |
               ((((long) b[offset + 2]) & 0xFF) << 40) |
               ((((long) b[offset + 3]) & 0xFF) << 32) |
               ((((long) b[offset + 4]) & 0xFF) << 24) |
               ((((long) b[offset + 5]) & 0xFF) << 16) |
               ((((long) b[offset + 6]) & 0xFF) << 8) |
               (((long) b[offset + 7]) & 0xFF);
    }

    private static int makeShort(byte[] b, int offset) {
        return ((((int) b[offset]) & 0xFF) << 8) |
               (((int) b[offset + 1]) & 0xFF);
    }

    public long getKey() {
        return key;
    }

    public int getWeight() {
        return weight;
    }

    /**
     * Decodes the polygot move into a ChessLib Move.
     * Polygot Move:
     * bits 0-5: dest square
     * bits 6-11: source square
     * bits 12-14: promotion (0: none, 1: knight, 2: bishop, 3: rook, 4: queen)
     */
    public Move getMove(Side side) {
        int toSqIdx = move & 0x3F;
        int fromSqIdx = (move >> 6) & 0x3F;
        int promoIdx = (move >> 12) & 0x7;

        Square from = Square.values()[fromSqIdx];
        Square to = Square.values()[toSqIdx];

        if (promoIdx == 0) {
            return new Move(from, to);
        }

        PieceType promotionType = PieceType.NONE;
        promotionType = switch (promoIdx) {
            case 1 -> PieceType.KNIGHT;
            case 2 -> PieceType.BISHOP;
            case 3 -> PieceType.ROOK;
            case 4 -> PieceType.QUEEN;
            default -> promotionType;
        };
        
        // Polygot promotion is just the piece type. We need the specific Piece (Side specific).
        return new Move(from, to, com.github.bhlangonijr.chesslib.Piece.make(side, promotionType));
    }

    /**
     * Compare keys as unsigned 64-bit integers.
     */
    @Override
    public int compareTo(BookEntry o) {
        return Long.compareUnsigned(this.key, o.key);
    }
}
