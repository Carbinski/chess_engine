#!/usr/bin/env python3
"""Fit an Elo estimate from fastchess PGNs produced by run_bracket.py.

Each game contributes its score (0, 1/2, or 1) to the logistic Elo
likelihood. The 95% interval is the profile likelihood: ratings whose log
likelihood is within 1.920729 of the maximum (half of the 3.84 chi-square
threshold on one parameter). An end that never crosses that threshold is
left open instead of being reported as the edge of the search. Stockfish 17
and Stockfish 19 are fit separately. Their UCI_Elo labels are not the same
strength.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

SCORE = {"1-0": 1.0, "0-1": 0.0, "1/2-1/2": 0.5}
# Abandoned games are crashes, not results. Time forfeits are real losses.
SCORED = {"normal", "time forfeit"}
LIMITED = re.compile(r"^(sf\d+)-(\d+)$")
PROFILE_DROP = 1.920729  # 0.5 * 3.841, the 95% chi-square threshold


def load_games(paths: list[Path]) -> list[dict]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.pgn")))
        elif path.is_file():
            files.append(path)
        else:
            raise SystemExit(f"no such PGN path: {path}")
    games = []
    for path in files:
        text = path.read_text(errors="replace")
        for chunk in text.split("[Event ")[1:]:
            headers = dict(re.findall(r'\[(\w+) "([^"]*)"\]', chunk))
            if headers.get("Result") not in SCORE:
                continue
            headers["_file"] = path.name
            games.append(headers)
    return games


def infer_engine_name(games: list[dict]) -> str | None:
    counts: dict[str, int] = defaultdict(int)
    for game in games:
        for side in ("White", "Black"):
            name = game.get(side, "")
            if name and not LIMITED.fullmatch(name):
                counts[name] += 1
    if not counts:
        return None
    most = max(counts.values())
    names = [name for name, count in counts.items() if count == most]
    # A two-engine match increments both names equally. Don't guess which one
    # is the engine under test.
    if len(names) != 1:
        return None
    return names[0]


def stockfish_major(family: str) -> int:
    return int(family.removeprefix("sf"))


def player_score(game: dict, name: str) -> float | None:
    result = SCORE[game["Result"]]
    if game.get("White") == name:
        return result
    if game.get("Black") == name:
        return 1.0 - result
    return None


def expected(rating: float, opponent: float, scale: float = 1.0) -> float:
    return 1.0 / (1.0 + 10 ** ((opponent - rating) / (400.0 * scale)))


def log_likelihood(pairs: list[tuple[float, float]], rating: float, scale: float = 1.0) -> float:
    total = 0.0
    for score, opponent in pairs:
        prob = expected(rating, opponent, scale)
        prob = min(max(prob, 1e-15), 1.0 - 1e-15)
        total += score * math.log(prob) + (1.0 - score) * math.log(1.0 - prob)
    return total


def maximum_likelihood(pairs: list[tuple[float, float]], scale: float = 1.0) -> tuple[float, float]:
    best_rating, best_ll = 2000.0, -1e300
    rating = 800.0
    while rating <= 3600.0:
        value = log_likelihood(pairs, rating, scale)
        if value > best_ll:
            best_rating, best_ll = rating, value
        rating += 5.0
    rating = best_rating - 5.0
    end = best_rating + 5.0
    while rating <= end:
        value = log_likelihood(pairs, rating, scale)
        if value > best_ll:
            best_rating, best_ll = rating, value
        rating += 0.25
    return best_rating, best_ll


def profile_interval(
    pairs: list[tuple[float, float]], mle: float, peak: float
) -> tuple[float | None, float | None]:
    """Return (low, high). An end is None when the likelihood never drops enough."""
    target = peak - PROFILE_DROP

    def walk(step: float) -> float | None:
        rating = mle
        for _ in range(400):
            rating += step
            if log_likelihood(pairs, rating) < target:
                return rating
        return None

    def bisect(inside: float, outside: float | None) -> float | None:
        if outside is None or log_likelihood(pairs, outside) >= target:
            return None
        for _ in range(60):
            mid = (inside + outside) / 2.0
            if log_likelihood(pairs, mid) >= target:
                inside = mid
            else:
                outside = mid
        return inside

    return bisect(mle, walk(-10.0)), bisect(mle, walk(10.0))


def format_interval(low: float | None, high: float | None) -> str:
    left = f"{low:.0f}" if low is not None else "-inf"
    right = f"{high:.0f}" if high is not None else "+inf"
    return f"[{left}, {right}]"


def standard_error(pairs: list[tuple[float, float]], mle: float) -> float:
    eps = 1.0
    curve = (
        log_likelihood(pairs, mle + eps) + log_likelihood(pairs, mle - eps) - 2.0 * log_likelihood(pairs, mle)
    )
    if curve >= 0:
        return float("nan")
    return 1.0 / math.sqrt(-curve)


def slope_interval(pairs: list[tuple[float, float]]) -> tuple[float, float, float, float] | None:
    """If a free Elo slope fits better, return (low, high, best_scale, likelihood_gain)."""
    scales = (0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.5)
    peak = -1e300
    best_scale = 1.0
    fixed = None
    for scale in scales:
        _rating, value = maximum_likelihood(pairs, scale)
        if scale == 1.0:
            fixed = value
        if value > peak:
            peak, best_scale = value, scale
    assert fixed is not None
    gain = peak - fixed
    if 2.0 * gain < 3.84:
        return None
    ok = []
    for rating in range(1200, 3601, 10):
        best = max(log_likelihood(pairs, rating, scale) for scale in scales)
        if best >= peak - PROFILE_DROP:
            ok.append(rating)
    if not ok:
        return None
    return float(ok[0]), float(ok[-1]), best_scale, gain


def cell_lines(rows: list[tuple[float, int, str]]) -> list[str]:
    cells: dict[tuple[str, int], list[float]] = defaultdict(lambda: [0.0, 0, 0, 0, 0])
    for score, label, family in rows:
        cell = cells[(family, label)]
        cell[0] += score
        cell[1] += 1
        cell[2] += score == 1.0
        cell[3] += score == 0.5
        cell[4] += score == 0.0
    lines = []
    for (family, label), (points, n, wins, draws, losses) in sorted(cells.items()):
        lines.append(
            f"  {family} {label:4d}  {points:5.1f}/{n:<3d} {100.0 * points / n:5.1f}%"
            f"   {int(wins)}W {int(draws)}D {int(losses)}L"
        )
    return lines


def format_report(games: list[dict], engine_name: str, sf17_shift: float) -> str:
    limited: list[dict] = []
    other: dict[str, list[float]] = defaultdict(lambda: [0.0, 0])
    calibration: list[tuple[float, str, str]] = []
    skipped = 0
    for game in games:
        termination = game.get("Termination")
        if termination and termination not in SCORED:
            skipped += 1
            continue
        score = player_score(game, engine_name)
        if score is None:
            white, black = game.get("White", ""), game.get("Black", "")
            left, right = LIMITED.fullmatch(white), LIMITED.fullmatch(black)
            if left and right and left.group(2) == right.group(2):
                # Score from the higher Stockfish version's point of view.
                if stockfish_major(left.group(1)) >= stockfish_major(right.group(1)):
                    calibration.append((SCORE[game["Result"]], white, black))
                else:
                    calibration.append((1.0 - SCORE[game["Result"]], black, white))
            continue
        opponent = game["Black"] if game.get("White") == engine_name else game["White"]
        match = LIMITED.fullmatch(opponent)
        if match:
            limited.append(
                {
                    "score": score,
                    "family": match.group(1),
                    "label": int(match.group(2)),
                    "color": "W" if game.get("White") == engine_name else "B",
                    "term": game.get("Termination", "?"),
                    "ply": int(game.get("PlyCount") or 0),
                }
            )
        else:
            other[opponent][0] += score
            other[opponent][1] += 1

    lines = [f"Engine: {engine_name}", f"PGN games read: {len(games)}"]
    if skipped:
        lines.append(f"Excluded {skipped} games whose termination was not normal or a time forfeit.")
    if other:
        lines.append("")
        lines.append("Full-strength or unlabeled opponents (engine score):")
        for name, (points, n) in sorted(other.items()):
            lines.append(f"  {name:16} {points:5.1f}/{n:<3.0f} {100.0 * points / n:5.1f}%")
        lines.append("  A zero score is an upper bound at this time control, not a CCRL rating.")

    if not limited and not calibration:
        lines.append("")
        lines.append("No UCI_Elo games found. Name opponents sf19-2000, sf17-2200, and so on.")
        return "\n".join(lines) + "\n"

    if limited:
        terms = defaultdict(int)
        for game in limited:
            terms[game["term"]] += 1
        plies = [game["ply"] for game in limited if game["ply"]]
        lines.append("")
        lines.append(f"Limited-strength games: {len(limited)}  terminations: {dict(terms)}")
        if plies:
            lines.append(
                f"Ply mean {sum(plies) / len(plies):.0f}, median {sorted(plies)[len(plies) // 2]}, max {max(plies)}"
            )
        lines.append("")
        lines.append("Scores:")
        lines.extend(cell_lines([(g["score"], g["label"], g["family"]) for g in limited]))

        fits = {}
        lines.append("")
        lines.append("Logistic Elo by Stockfish version (do not average these labels):")
        for family in sorted({g["family"] for g in limited}):
            pairs = [(g["score"], float(g["label"])) for g in limited if g["family"] == family]
            mle, peak = maximum_likelihood(pairs)
            low, high = profile_interval(pairs, mle, peak)
            se = standard_error(pairs, mle)
            fits[family] = (pairs, mle, peak)
            edge = ""
            if mle <= 800.25 or mle >= 3599.75:
                edge = "  (at the 800–3600 search edge)"
            lines.append(
                f"  {family}  n={len(pairs):3d}  {mle:.0f}  95% profile {format_interval(low, high)}"
                f"  se {se:.0f}{edge}"
            )
            for color in ("W", "B"):
                colored = [(g["score"], float(g["label"])) for g in limited if g["family"] == family and g["color"] == color]
                if len(colored) < 8:
                    continue
                color_mle, _ = maximum_likelihood(colored)
                points = sum(score for score, _ in colored)
                lines.append(f"    as {color}: {color_mle:.0f}  ({points:.1f}/{len(colored)})")
            wider = slope_interval(pairs)
            if wider:
                wlow, whigh, scale, gain = wider
                lines.append(
                    f"    slope is flatter than 400 Elo/logit (scale {scale:.1f}, "
                    f"likelihood gain {gain:.2f}); interval with a free slope is about {wlow:.0f}–{whigh:.0f}"
                )

        measured = dial_gaps(calibration)
        sf17_gap = measured.get(("sf19", "sf17"))
        shift = sf17_gap if sf17_gap is not None else sf17_shift
        shift_note = (
            "the dial gap measured in this PGN set"
            if sf17_gap is not None
            else "the stored 2026-11-16 dial gap"
        )
        if "sf19" in fits and "sf17" in fits and shift:
            shifted = list(fits["sf19"][0]) + [
                (score, label - shift) for score, label in fits["sf17"][0]
            ]
            mle, peak = maximum_likelihood(shifted)
            low, high = profile_interval(shifted, mle, peak)
            lines.append("")
            lines.append(
                f"On the sf19 dial, with sf17 labels shifted down by {shift:.0f} ({shift_note}): "
                f"{mle:.0f}  95% profile {format_interval(low, high)}  n={len(shifted)}"
            )
            lines.append(
                "  Quote the separate sf19 and sf17 ratings. The shifted figure is a check that they agree."
            )

    if calibration:
        lines.append("")
        lines.extend(dial_lines(calibration))
    return "\n".join(lines) + "\n"


def dial_gaps(calibration: list[tuple[float, str, str]]) -> dict[tuple[str, str], float]:
    """Elo by which the newer Stockfish outrates the older one, for a single shared label."""
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for score, newer, older in calibration:
        newer_match, older_match = LIMITED.fullmatch(newer), LIMITED.fullmatch(older)
        if not newer_match or not older_match:
            continue
        grouped[(newer_match.group(1), older_match.group(1), newer_match.group(2))].append(score)
    gaps: dict[tuple[str, str], float] = {}
    labels: dict[tuple[str, str], set[str]] = defaultdict(set)
    by_pair: dict[tuple[str, str], list[float]] = defaultdict(list)
    for (newer, older, label), scores in grouped.items():
        labels[(newer, older)].add(label)
        points = sum(scores)
        n = len(scores)
        p = points / n
        if 0 < p < 1:
            by_pair[(newer, older)].append(400.0 * math.log10(p / (1.0 - p)))
    for pair, values in by_pair.items():
        # Matches at two labels are not one binomial sample.
        if len(labels[pair]) == 1 and len(values) == 1:
            gaps[pair] = values[0]
    return gaps


def dial_lines(calibration: list[tuple[float, str, str]]) -> list[str]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for score, newer, older in calibration:
        grouped[(newer, older)].append(score)
    lines = []
    for (newer, older), scores in sorted(grouped.items()):
        points = sum(scores)
        n = len(scores)
        p = points / n
        lines.append(f"Dial check {newer} vs {older}: {newer} scored {points:.1f}/{n} ({100 * p:.1f}%)")
        if 0 < p < 1:
            diff = 400.0 * math.log10(p / (1.0 - p))
            se_p = math.sqrt(p * (1.0 - p) / n)
            se = 400.0 / (math.log(10) * p * (1.0 - p)) * se_p
            lines.append(f"  {newer} is {diff:.0f} Elo stronger at the same UCI_Elo (se {se:.0f})")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fit Elo from fastchess PGNs of a UCI_Elo bracket.")
    parser.add_argument("paths", nargs="+", type=Path, help="PGN files or directories")
    parser.add_argument("--engine-name", help="Player name in the PGN. Inferred when omitted.")
    parser.add_argument(
        "--sf17-shift",
        type=float,
        default=206.0,
        help="How many Elo to subtract from Stockfish 17 labels when restating them on the Stockfish 19 dial.",
    )
    args = parser.parse_args(argv)
    games = load_games(args.paths)
    if not games:
        print("No games found.", file=sys.stderr)
        return 1
    name = args.engine_name or infer_engine_name(games)
    if not name:
        print("Could not infer the engine name. Pass --engine-name.", file=sys.stderr)
        return 1
    print(format_report(games, name, args.sf17_shift), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
