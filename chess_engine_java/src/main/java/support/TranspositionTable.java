package support;

public class TranspositionTable {
    public static final int EXACT = 0;
    public static final int LOWER_BOUND = 1;
    public static final int UPPER_BOUND = 2;

    private final int size;
    private final long[] keys; // Store the hash keys
    private final long[] data;

    public TranspositionTable(int num_entries) {
        this.size = num_entries;
        this.keys = new long[size];
        this.data = new long[size];
    }

    public void store(long key, int depth, int score, int flag, int move) {
        int index = (int) (Long.remainderUnsigned(key, size));

        // Always Replace + Depth First Strategy
        if (keys[index] == 0 || depth >= get_depth(data[index])) {
            keys[index] = key;
            data[index] = pack(depth, score, flag, move);
        }
    }

    public TTEntry probe(long key) {
        int index = (int) (Long.remainderUnsigned(key, size));

        if (keys[index] == key) {
            return unpack(data[index]);
        }
        return null;
    }


    private long pack(int depth, int score, int flag, int move) {
        return ((long) depth << 48) |
                ((long) (score + 32768) << 32) |
                ((long) flag << 24) |
                (move & 0xFFFFFFL);
    }

    private int get_depth(long packed) {
        return (int) (packed >> 48);
    }

    public record TTEntry(int depth, int score, int flag, int move) {}

    private TTEntry unpack(long packed) {
        int depth = (int) (packed >> 48);
        int score = (int) ((packed >> 32) & 0xFFFF) - 32768;
        int flag = (int) ((packed >> 24) & 0xFF);
        int move = (int) (packed & 0xFFFFFF);
        return new TTEntry(depth, score, flag, move);
    }
}
