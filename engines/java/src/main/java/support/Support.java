package support;

public class Support {
    public static String bitboardToString(long bitboard) {
        StringBuilder sb = new StringBuilder();

        for (int rank = 7; rank >= 0; rank--) {
            for (int file = 0; file < 8; file++) {
                int square = rank * 8 + file;

                if (((bitboard >>> square) & 1L) == 1L) {
                    sb.append("1 ");
                } else {
                    sb.append("0 ");
                }
            }
            sb.append("\n");
        }
        return sb.toString();
    }
}
