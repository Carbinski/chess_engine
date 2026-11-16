#!/usr/bin/env python3
"""Play the 8+0.08 Stockfish UCI_Elo bracket and print an Elo estimate.

See the estimate-engine-elo skill for how to read the result. This script
does not change the engine. Stockfish 19 is the primary dial. Stockfish 17
is a second dial, measured separately.
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fit_elo  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parents[1]
BOOK = SKILL_ROOT / "assets" / "balanced.epd"
COARSE = (1320, 1700, 2000, 2300, 2600, 2900)
DIAL_MIN, DIAL_MAX = 1320, 3190

SF19_URL = (
    "https://github.com/official-stockfish/Stockfish/releases/download/"
    "sf_19/stockfish-linux-x86-64-universal.tar.gz"
)
SF17_URL = (
    "https://github.com/official-stockfish/Stockfish/releases/download/"
    "sf_17/stockfish-ubuntu-x86-64-bmi2.tar"
)
SF19_BIN = "stockfish-linux-x86-64-universal"
SF17_BIN = "stockfish-ubuntu-x86-64-bmi2"


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "tools" / "fastchess" / "Makefile").exists():
            return parent
    raise SystemExit("Could not find tools/fastchess. Run this from the chess_engine checkout.")


def book_lines() -> int:
    return sum(1 for line in BOOK.read_text().splitlines() if line.strip() and not line.startswith("#"))


def run(cmd: list[str], **kwargs) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, **kwargs)


def ensure_stockfish(out: Path, url: str, archive_name: str, binary_name: str) -> Path:
    root = out / "stockfish" / binary_name
    binary = root / "stockfish" / binary_name
    if binary.is_file():
        return binary
    root.mkdir(parents=True, exist_ok=True)
    archive = out / "stockfish" / archive_name
    if not archive.is_file() or archive.stat().st_size == 0:
        run(["curl", "-fL", "--retry", "3", "-o", str(archive), url])
    run(["tar", "-xf", str(archive), "-C", str(root)])
    if not binary.is_file():
        found = list(root.rglob(binary_name))
        if not found:
            raise SystemExit(f"{binary_name} not found after extracting {archive}")
        return found[0]
    return binary


def write_wrapper(out: Path, engine: Path) -> Path:
    wrapper = out / "engine.sh"
    # CHESS_LOG defaults to trace and writes beside the process cwd. The
    # assignment has to be in the process fastchess execs, not on a pipeline.
    wrapper.write_text(f"#!/bin/sh\nexport CHESS_LOG=off\nexec {shlex.quote(str(engine))}\n")
    wrapper.chmod(0o755)
    return wrapper


def fastchess_bin(root: Path) -> Path:
    binary = root / "tools" / "fastchess" / "fastchess"
    if not binary.is_file():
        raise SystemExit(
            "fastchess is not built. From the repo root:\n"
            "  git submodule update --init tools/fastchess engines/cpp/chess-library\n"
            "  make -C tools/fastchess -j"
        )
    return binary


def play_match(
    fastchess: Path,
    wrapper: Path,
    engine_name: str,
    opponent: Path,
    opponent_name: str,
    elo: int | None,
    rounds: int,
    concurrency: int,
    tc: str,
    pgn: Path,
    log: Path,
) -> None:
    if rounds > book_lines():
        raise SystemExit(f"{rounds} rounds exceeds the {book_lines()}-line book. Sequential order uses one opening per round.")
    pgn.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    opponent_cmd = [
        "-engine",
        f"cmd={opponent}",
        f"name={opponent_name}",
        f"dir={opponent.parent}",
        "option.Threads=1",
        "option.Hash=16",
    ]
    if elo is not None:
        opponent_cmd += ["option.UCI_LimitStrength=true", f"option.UCI_Elo={elo}"]
    cmd = [
        str(fastchess),
        "-engine",
        f"cmd={wrapper}",
        f"name={engine_name}",
        *opponent_cmd,
        "-each",
        f"tc={tc}",
        "proto=uci",
        "-openings",
        f"file={BOOK}",
        "format=epd",
        "order=sequential",
        "-rounds",
        str(rounds),
        "-repeat",
        "-concurrency",
        str(concurrency),
        "-pgnout",
        f"file={pgn}",
        "append=false",
        "-recover",
    ]
    print(f"\n== {engine_name} vs {opponent_name}  rounds={rounds} (x2 colors) ==", flush=True)
    with log.open("w") as handle:
        proc = subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        tail = log.read_text(errors="replace").splitlines()[-40:]
        print("\n".join(tail), file=sys.stderr)
        raise SystemExit(f"fastchess exited {proc.returncode}; log: {log}")
    games = fit_elo.load_games([pgn])
    expected = rounds * 2
    if len(games) != expected:
        raise SystemExit(f"{pgn} has {len(games)} games, expected {expected}. Log: {log}")
    bad = [game.get("Termination") for game in games if game.get("Termination") not in fit_elo.SCORED]
    if bad:
        raise SystemExit(f"{pgn} has unscored terminations {bad}. The opponent may have crashed. Log: {log}")
    points = 0.0
    for game in games:
        score = fit_elo.player_score(game, engine_name)
        if score is None:
            raise SystemExit(f"{engine_name} did not play in {pgn}")
        points += score
    print(f"   {points:.1f}/{len(games)} ({100.0 * points / len(games):.1f}%)", flush=True)


def play_calibration(fastchess: Path, sf17: Path, sf19: Path, rounds: int, concurrency: int, tc: str, pgn: Path, log: Path) -> None:
    pgn.parent.mkdir(parents=True, exist_ok=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(fastchess),
        "-engine", f"cmd={sf17}", "name=sf17-2200", f"dir={sf17.parent}",
        "option.Threads=1", "option.Hash=16", "option.UCI_LimitStrength=true", "option.UCI_Elo=2200",
        "-engine", f"cmd={sf19}", "name=sf19-2200", f"dir={sf19.parent}",
        "option.Threads=1", "option.Hash=16", "option.UCI_LimitStrength=true", "option.UCI_Elo=2200",
        "-each", f"tc={tc}", "proto=uci",
        "-openings", f"file={BOOK}", "format=epd", "order=sequential",
        "-rounds", str(rounds), "-repeat", "-concurrency", str(concurrency),
        "-pgnout", f"file={pgn}", "append=false", "-recover",
    ]
    print(f"\n== sf17-2200 vs sf19-2200  rounds={rounds} (x2 colors) ==", flush=True)
    with log.open("w") as handle:
        proc = subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT)
    if proc.returncode != 0:
        tail = log.read_text(errors="replace").splitlines()[-40:]
        print("\n".join(tail), file=sys.stderr)
        raise SystemExit(f"fastchess exited {proc.returncode}; log: {log}")


def points_by_elo(pgn_dir: Path, engine_name: str, family: str) -> dict[int, tuple[float, int]]:
    totals: dict[int, list[float]] = {}
    for game in fit_elo.load_games([pgn_dir]):
        score = fit_elo.player_score(game, engine_name)
        if score is None:
            continue
        opponent = game["Black"] if game.get("White") == engine_name else game["White"]
        match = re.fullmatch(rf"{family}-(\d+)", opponent)
        if not match:
            continue
        label = int(match.group(1))
        cell = totals.setdefault(label, [0.0, 0])
        cell[0] += score
        cell[1] += 1
    return {label: (cell[0], int(cell[1])) for label, cell in totals.items()}


def refine_targets(scores: dict[int, tuple[float, int]]) -> list[int]:
    """Levels around the first 50% crossing, reading from the weakest opponent up."""
    rated = {elo: points / n for elo, (points, n) in scores.items() if n}
    if not rated:
        return []
    ordered = sorted(rated)
    for low, high in zip(ordered, ordered[1:]):
        if rated[low] >= 0.5 >= rated[high]:
            targets = {low, high}
            if high - low > 100:
                interior = list(range(low + 100, high, 100))
                interior.sort(key=lambda elo: abs(elo - (low + high) / 2))
                targets.update(interior[:2])
            return sorted(targets)
    if all(pct >= 0.5 for pct in rated.values()):
        return [2900, 3100]
    return []


def sf19_mle(pgn_dir: Path, engine_name: str) -> float | None:
    pairs = []
    for game in fit_elo.load_games([pgn_dir]):
        score = fit_elo.player_score(game, engine_name)
        if score is None:
            continue
        opponent = game["Black"] if game.get("White") == engine_name else game["White"]
        match = re.fullmatch(r"sf19-(\d+)", opponent)
        if match:
            pairs.append((score, float(match.group(1))))
    if len(pairs) < 8:
        return None
    mle, _ = fit_elo.maximum_likelihood(pairs)
    return mle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Stockfish UCI_Elo bracket and fit Elo.")
    parser.add_argument("--engine", type=Path, help="UCI engine binary")
    parser.add_argument("--name", default="Helios", help="Name written into the PGN")
    parser.add_argument("--out", type=Path, default=Path("/tmp/elo-run"))
    parser.add_argument("--tc", default="8+0.08")
    parser.add_argument("--concurrency", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    parser.add_argument("--coarse-rounds", type=int, default=4, help="Openings per coarse level; both colors, so games = 2 * rounds")
    parser.add_argument("--refine-rounds", type=int, default=12)
    parser.add_argument("--cross-rounds", type=int, default=8)
    parser.add_argument("--skip-cross", action="store_true", help="Skip the Stockfish 17 cross-check")
    parser.add_argument("--calibrate", action="store_true", help="Also play Stockfish 17 vs 19 at UCI_Elo 2200")
    parser.add_argument("--calibrate-rounds", type=int, default=16)
    parser.add_argument("--only", help="Play one match, e.g. sf19:2000 or sf17:2200, then fit")
    parser.add_argument("--rounds", type=int, default=1, help="Rounds for --only")
    parser.add_argument("--sf19", type=Path, help="Existing Stockfish 19 binary")
    parser.add_argument("--sf17", type=Path, help="Existing Stockfish 17 binary")
    parser.add_argument("--fit-only", action="store_true", help="Fit PGNs already in --out/pgn")
    args = parser.parse_args(argv)

    out = args.out.resolve()
    pgn_dir = out / "pgn"
    log_dir = out / "logs"
    pgn_dir.mkdir(parents=True, exist_ok=True)
    if args.fit_only:
        return fit_elo.main([str(pgn_dir), "--engine-name", args.name])
    if args.engine is None or not args.engine.is_file():
        raise SystemExit("--engine must be the UCI binary to measure")
    engine = args.engine.resolve()
    if not args.only and any(pgn_dir.glob("*.pgn")):
        raise SystemExit(f"{pgn_dir} already has PGNs. Use a fresh --out, or --fit-only to refit them.")
    fastchess = fastchess_bin(repo_root())
    sf19 = args.sf19.resolve() if args.sf19 else ensure_stockfish(out, SF19_URL, "sf19.tar.gz", SF19_BIN)
    sf17 = args.sf17.resolve() if args.sf17 else ensure_stockfish(out, SF17_URL, "sf17.tar", SF17_BIN)
    for binary in (sf19, sf17):
        if not binary.is_file():
            raise SystemExit(f"Stockfish binary not found: {binary}")
    wrapper = write_wrapper(out, engine)

    if args.only:
        match = re.fullmatch(r"(sf\d+):(\d+)", args.only)
        if not match:
            raise SystemExit("--only expects sf19:2000 or sf17:2200")
        family, elo = match.group(1), int(match.group(2))
        if family not in ("sf17", "sf19"):
            raise SystemExit("--only supports sf17 and sf19, the two dials this bracket downloads")
        if not DIAL_MIN <= elo <= DIAL_MAX:
            raise SystemExit(f"UCI_Elo {elo} is outside {DIAL_MIN}–{DIAL_MAX}")
        opponent = sf19 if family == "sf19" else sf17
        play_match(
            fastchess, wrapper, args.name, opponent, f"{family}-{elo}", elo,
            args.rounds, args.concurrency, args.tc,
            pgn_dir / f"{family}-{elo}.pgn", log_dir / f"{family}-{elo}.log",
        )
        return fit_elo.main([str(pgn_dir), "--engine-name", args.name])

    print(
        f"Bracket for {args.name} at {args.tc}, concurrency {args.concurrency}. "
        f"PGNs in {pgn_dir}. Fastchess warnings are redirected to {log_dir}.",
        flush=True,
    )
    for elo in COARSE:
        play_match(
            fastchess, wrapper, args.name, sf19, f"sf19-{elo}", elo,
            args.coarse_rounds, args.concurrency, args.tc,
            pgn_dir / f"sf19-{elo}-coarse.pgn", log_dir / f"sf19-{elo}-coarse.log",
        )

    scores = points_by_elo(pgn_dir, args.name, "sf19")
    floor = scores.get(1320)
    if floor and floor[0] / floor[1] <= 0.25:
        print("\nBelow the UCI_Elo floor (1320). Stopping before the refinement matches.")
        return fit_elo.main([str(pgn_dir), "--engine-name", args.name])

    for elo in refine_targets(scores):
        if not DIAL_MIN <= elo <= DIAL_MAX:
            continue
        play_match(
            fastchess, wrapper, args.name, sf19, f"sf19-{elo}", elo,
            args.refine_rounds, args.concurrency, args.tc,
            pgn_dir / f"sf19-{elo}-refine.pgn", log_dir / f"sf19-{elo}-refine.log",
        )

    if not args.skip_cross:
        mle = sf19_mle(pgn_dir, args.name)
        if mle is None:
            print("\nNo Stockfish 19 estimate; skipping the Stockfish 17 cross-check.")
        else:
            center = int(round(mle / 100.0) * 100)
            center = min(DIAL_MAX, max(DIAL_MIN, center))
            higher = min(DIAL_MAX, center + 200)
            for elo in dict.fromkeys((center, higher)):
                play_match(
                    fastchess, wrapper, args.name, sf17, f"sf17-{elo}", elo,
                    args.cross_rounds, args.concurrency, args.tc,
                    pgn_dir / f"sf17-{elo}.pgn", log_dir / f"sf17-{elo}.log",
                )

    if args.calibrate:
        play_calibration(
            fastchess, sf17, sf19, args.calibrate_rounds, args.concurrency, args.tc,
            pgn_dir / "sf17-vs-sf19-2200.pgn", log_dir / "sf17-vs-sf19-2200.log",
        )

    print("\n== fit ==\n", flush=True)
    return fit_elo.main([str(pgn_dir), "--engine-name", args.name])


if __name__ == "__main__":
    raise SystemExit(main())
