#!/usr/bin/env python3
"""Checks for the Elo fitter and the bracket's level picker. No engines required."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fit_elo  # noqa: E402
import run_bracket  # noqa: E402


class RefineTests(unittest.TestCase):
    def test_wide_gap_adds_the_interior_hundreds(self):
        self.assertEqual(
            run_bracket.refine_targets({1700: (6.4, 8), 2000: (2.4, 8)}),
            [1700, 1800, 1900, 2000],
        )

    def test_steps_from_1320_stay_on_that_grid(self):
        targets = run_bracket.refine_targets({1320: (8, 8), 1700: (2, 8)})
        self.assertEqual(targets, [1320, 1500, 1600, 1700])

    def test_above_every_level_goes_to_the_top_of_the_dial(self):
        self.assertEqual(run_bracket.refine_targets({1320: (8, 8), 2900: (7, 8)}), [2900, 3100])

    def test_below_every_level_adds_nothing(self):
        self.assertEqual(run_bracket.refine_targets({1320: (1, 8), 1700: (0, 8)}), [])


class FitTests(unittest.TestCase):
    def test_even_sample_interval_contains_the_crossing(self):
        pairs = [(1.0, 1800.0)] * 20 + [(0.0, 2200.0)] * 20
        mle, peak = fit_elo.maximum_likelihood(pairs)
        low, high = fit_elo.profile_interval(pairs, mle, peak)
        self.assertAlmostEqual(mle, 2000, delta=15)
        self.assertIsNotNone(low)
        self.assertIsNotNone(high)
        assert low is not None and high is not None
        self.assertLess(low, mle)
        self.assertGreater(high, mle)
        self.assertGreater(low, 1600)
        self.assertLess(high, 2400)

    def test_all_wins_leaves_the_upper_end_open(self):
        pairs = [(1.0, 1500.0)] * 30
        mle, peak = fit_elo.maximum_likelihood(pairs)
        low, high = fit_elo.profile_interval(pairs, mle, peak)
        self.assertIsNone(high)
        self.assertIsNotNone(low)
        assert low is not None
        self.assertGreater(low, 1500)
        self.assertGreaterEqual(mle, 3599)

    def test_abandoned_game_is_not_scored(self):
        games = [
            {
                "White": "Helios",
                "Black": "sf-1.0",
                "Result": "1-0",
                "Termination": "abandoned",
                "PlyCount": "4",
            },
            {
                "White": "sf-1.0",
                "Black": "Helios",
                "Result": "1-0",
                "Termination": "normal",
                "PlyCount": "20",
            },
        ]
        report = fit_elo.format_report(games, "Helios", 206)
        self.assertIn("Excluded 1", report)
        self.assertIn("0.0/1", report)
        self.assertNotIn("1.0/1", report)

    def test_tied_names_are_not_guessed(self):
        games = [
            {"White": "Helios", "Black": "Glaurung", "Result": "0-1", "Termination": "normal"},
            {"White": "Glaurung", "Black": "Helios", "Result": "1-0", "Termination": "normal"},
        ]
        self.assertIsNone(fit_elo.infer_engine_name(games))

    def test_single_label_dial_gap(self):
        calibration = [(1.0, "sf19-2200", "sf17-2200")] * 3 + [(0.0, "sf19-2200", "sf17-2200")]
        gaps = fit_elo.dial_gaps(calibration)
        self.assertAlmostEqual(gaps[("sf19", "sf17")], 400 * math.log10(3), delta=0.1)

    def test_two_labels_are_not_collapsed_into_one_gap(self):
        calibration = [
            (1.0, "sf19-2200", "sf17-2200"),
            (0.5, "sf19-2000", "sf17-2000"),
        ]
        self.assertEqual(fit_elo.dial_gaps(calibration), {})


if __name__ == "__main__":
    unittest.main()
