"""Think-time split shared with the C++ engine.

The C++ UCI front budgets ``time_remaining / 75`` milliseconds and ignores
increment. Python uses the same split. The referee still awards increment
and flags on the real clock.
"""

DIVISOR = 75


def budget_ms(time_remaining_ms):
    """Search budget for a side that has ``time_remaining_ms`` left, or None."""
    if time_remaining_ms is None:
        return None
    if time_remaining_ms <= 0:
        return 0
    return int(time_remaining_ms) // DIVISOR


def depth_cap(nominal_depth, budget_ms_value):
    """Cap a fixed-depth search so it can finish inside ``budget_ms_value``.

    Measured on these bots: depth 4 is a fraction of a second, depth 5 is
    about two seconds, depth 6 is about fifteen. The cap never raises a
    bot's own depth.
    """
    if budget_ms_value >= 15000:
        limit = 6
    elif budget_ms_value >= 2000:
        limit = 5
    elif budget_ms_value >= 200:
        limit = 4
    elif budget_ms_value >= 40:
        limit = 3
    elif budget_ms_value >= 8:
        limit = 2
    else:
        limit = 1
    nominal = int(nominal_depth) if nominal_depth else 1
    if nominal < 1:
        nominal = 1
    return min(nominal, limit)
