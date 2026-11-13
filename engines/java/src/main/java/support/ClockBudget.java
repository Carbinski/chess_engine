package support;

/**
 * Think-time split shared with the C++ engine.
 *
 * The C++ UCI front budgets {@code timeRemaining / 75} milliseconds and
 * ignores increment. Java uses the same split. The referee still awards
 * increment and flags on the real clock.
 */
public final class ClockBudget {
    public static final int DIVISOR = 75;

    private ClockBudget() {}

    public static long budgetMs(long timeRemainingMs) {
        if (timeRemainingMs <= 0) {
            return 0;
        }
        return timeRemainingMs / DIVISOR;
    }

    /**
     * Cap a fixed-depth search so it can finish inside {@code budgetMs}.
     * Never raises a bot's own depth.
     */
    public static int depthCap(int nominalDepth, long budgetMs) {
        int limit;
        if (budgetMs >= 15000) {
            limit = 6;
        } else if (budgetMs >= 2000) {
            limit = 5;
        } else if (budgetMs >= 200) {
            limit = 4;
        } else if (budgetMs >= 40) {
            limit = 3;
        } else if (budgetMs >= 8) {
            limit = 2;
        } else {
            limit = 1;
        }
        if (nominalDepth < 1) {
            return 1;
        }
        return Math.min(nominalDepth, limit);
    }
}
