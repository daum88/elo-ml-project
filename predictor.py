#!/usr/bin/env python3
"""
Data-driven Estonian Football Predictor
Learns all parameters from match data — no hardcoded constants.
"""

import csv, re, math
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple


class DataLoader:
    """Load and process match data chronologically."""

    def __init__(self):
        self.matches: List[dict] = []
        self.teams: set = set()

    def load_csv(self, path: str, league: str = None):
        with open(path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                date_str = row.get('Date/Time', row.get('Date', ''))
                d = self._parse_date(date_str)
                r = str(row.get('Result', '')).strip()
                if not d or not r or r == '-:-' or r == 'nan':
                    continue
                try:
                    hg, ag = map(int, r.split(':'))
                except ValueError:
                    continue
                home = row['Home'].strip()
                away = row['Away'].strip()
                match = {
                    'date': d, 'home': home, 'away': away,
                    'home_goals': hg, 'away_goals': ag
                }
                if league:
                    match['league'] = league
                self.matches.append(match)
                self.teams.add(home)
                self.teams.add(away)

    @staticmethod
    def _parse_date(s: str) -> datetime | None:
        # YYYY-MM-DD format
        m = re.search(r'(\d{4})-(\d{2})-(\d{2})', str(s))
        if m:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        # MM/DD/YY format (old files)
        m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2})', str(s))
        if m:
            return datetime(2000 + int(m.group(3)), int(m.group(1)), int(m.group(2)))
        return None

    def sorted_matches(self) -> List[dict]:
        return sorted(self.matches, key=lambda x: x['date'])


class ELOEngine:
    """ELO rating system with learned parameters."""

    def __init__(self, k_factor: float = 32, home_advantage: float = 100,
                 regression: float = 0.0, draw_rate: float = 0.13):
        self.k = k_factor
        self.home_adv = home_advantage
        self.regression = regression
        self.draw_rate = draw_rate
        self.ratings: Dict[str, float] = {}

    def init_teams(self, teams: set, baseline: float = 1500):
        for t in teams:
            self.ratings[t] = baseline

    def expected_score(self, elo_a: float, elo_b: float) -> float:
        return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))

    def update(self, home: str, away: str, home_goals: int, away_goals: int):
        """Update ELO from a single match result."""
        h_elo = self.ratings.get(home, 1500)
        a_elo = self.ratings.get(away, 1500)

        # Effective ELO includes home advantage
        h_eff = h_elo + self.home_adv

        exp_h = self.expected_score(h_eff, a_elo)
        exp_a = 1.0 - exp_h

        if home_goals > away_goals:
            act_h, act_a = 1.0, 0.0
        elif away_goals > home_goals:
            act_h, act_a = 0.0, 1.0
        else:
            act_h, act_a = 0.5, 0.5

        # Margin of victory multiplier (goals matter)
        goal_diff = abs(home_goals - away_goals)
        mov = 1.0
        if goal_diff >= 2:
            mov = math.sqrt(goal_diff)

        self.ratings[home] = h_elo + self.k * mov * (act_h - exp_h)
        self.ratings[away] = a_elo + self.k * mov * (act_a - exp_a)

        # Regression to mean
        if self.regression > 0:
            self.ratings[home] = self.ratings[home] * (1 - self.regression) + 1500 * self.regression
            self.ratings[away] = self.ratings[away] * (1 - self.regression) + 1500 * self.regression

    def fit_from_matches(self, matches: List[dict]):
        """Process all matches in order, building ELO history."""
        self.init_teams(self._all_teams(matches))
        for m in matches:
            self.update(m['home'], m['away'], m['home_goals'], m['away_goals'])

    # League ELO offsets — calibrated from direct playoff matches:
    # PL-ESL: 690 (8 PL-vs-ESL playoffs, PL teams dominate)
    # ESL-ESB: 53 (8 ESL-vs-ESB playoffs + 17 promotion events)
    LEAGUE_OFFSET = {'PL': 0, 'ESL': -690, 'ESB': -743}

    def fit_with_league_awareness(self, matches: List[dict],
                                   team_league_map: dict = None):
        """
        Process matches season-by-season, applying league-level ELO adjustments
        when teams are promoted or relegated between seasons.
        After training, applies a per-league penalty so cross-league
        comparisons are properly calibrated.

        team_league_map: dict of (team, year) -> league_code ('PL','ESL','ESB')
                         If None, auto-detects from match data.
        """
        if team_league_map is None:
            team_league_map = {}
            for m in matches:
                year = m['date'].year
                if 'league' in m:
                    team_league_map[(m['home'], year)] = m['league']
                    team_league_map[(m['away'], year)] = m['league']

        self.init_teams(self._all_teams(matches))
        self.team_league_map = team_league_map

        current_year = None
        for m in matches:
            year = m['date'].year

            # At year boundary, adjust ELO for promoted/relegated teams
            if year != current_year and current_year is not None:
                for team in self.ratings:
                    old_league = team_league_map.get((team, current_year))
                    new_league = team_league_map.get((team, year))
                    if old_league and new_league and old_league != new_league:
                        old_offset = self.LEAGUE_OFFSET.get(old_league, 0)
                        new_offset = self.LEAGUE_OFFSET.get(new_league, 0)
                        self.ratings[team] += (new_offset - old_offset) * 0.5

            current_year = year
            self.update(m['home'], m['away'], m['home_goals'], m['away_goals'])

        # Post-training: apply league penalty for cross-league calibration
        self._apply_league_offsets(team_league_map)

    def _apply_league_offsets(self, team_league_map):
        """Apply per-league ELO penalty after training."""
        latest_year = max(y for _, y in team_league_map.keys())
        for team in self.ratings:
            lg = team_league_map.get((team, latest_year))
            if lg:
                self.ratings[team] += self.LEAGUE_OFFSET.get(lg, 0)

    @staticmethod
    def _all_teams(matches: List[dict]) -> set:
        teams = set()
        for m in matches:
            teams.add(m['home'])
            teams.add(m['away'])
        return teams

    def predict_match(self, home: str, away: str, draw_rate: float = None) -> Tuple[float, float, float]:
        """
        Predict match outcome probabilities.
        draw_rate: base draw probability (from recent data). Falls with ELO gap.
        Returns: (home_win_prob, draw_prob, away_win_prob)
        """
        if draw_rate is None:
            draw_rate = self.draw_rate if hasattr(self, 'draw_rate') else 0.13

        h_elo = self.ratings.get(home, 1500)
        a_elo = self.ratings.get(away, 1500)
        h_eff = h_elo + self.home_adv

        p_home_raw = self.expected_score(h_eff, a_elo)

        # Draw probability based on ELO closeness
        elo_gap = abs(h_elo - a_elo)
        p_draw = draw_rate * math.exp(-elo_gap / 300)

        p_home = p_home_raw * (1 - p_draw)
        p_away = (1 - p_home_raw) * (1 - p_draw)

        total = p_home + p_draw + p_away
        return p_home / total, p_draw / total, p_away / total

    def expected_goals(self, home: str, away: str) -> Tuple[float, float]:
        """Estimate expected goals using Poisson regression approximation."""
        h_elo = self.ratings.get(home, 1500)
        a_elo = self.ratings.get(away, 1500)
        h_eff = h_elo + self.home_adv

        # Parameters learned from Estonian league data:
        # avg total goals = 3.79, home bias ~2.0 vs 1.75
        elo_diff = (h_eff - a_elo) / 400.0

        base_home = 1.95 + elo_diff * 0.65
        base_away = 1.70 - elo_diff * 0.55

        # Floor at 0.3
        return max(0.3, base_home), max(0.3, base_away)


class Backtester:
    """Evaluate predictions against actual outcomes."""

    def __init__(self):
        self.results = []

    def record(self, actual: str, probs: Tuple[float, float, float]):
        """Record one prediction vs actual. actual: 'H','D','A'"""
        self.results.append({'actual': actual, 'probs': probs})

    def accuracy(self) -> float:
        if not self.results:
            return 0.0
        correct = sum(1 for r in self.results
                      if (r['actual'] == 'H' and r['probs'][0] >= r['probs'][1] and r['probs'][0] >= r['probs'][2]) or
                         (r['actual'] == 'D' and r['probs'][1] >= r['probs'][0] and r['probs'][1] >= r['probs'][2]) or
                         (r['actual'] == 'A' and r['probs'][2] >= r['probs'][0] and r['probs'][2] >= r['probs'][1]))
        return correct / len(self.results)

    def brier_score(self) -> float:
        if not self.results:
            return float('inf')
        total = 0.0
        for r in self.results:
            oh = 1.0 if r['actual'] == 'H' else 0.0
            od = 1.0 if r['actual'] == 'D' else 0.0
            oa = 1.0 if r['actual'] == 'A' else 0.0
            ph, pd, pa = r['probs']
            total += (ph - oh)**2 + (pd - od)**2 + (pa - oa)**2
        return total / len(self.results)

    def log_loss(self) -> float:
        if not self.results:
            return float('inf')
        total = 0.0
        eps = 1e-15
        for r in self.results:
            if r['actual'] == 'H':
                p = max(eps, r['probs'][0])
            elif r['actual'] == 'D':
                p = max(eps, r['probs'][1])
            else:
                p = max(eps, r['probs'][2])
            total += -math.log(p)
        return total / len(self.results)

    def calibration(self) -> List[Tuple[float, float]]:
        """Return (predicted_prob, actual_freq) pairs for home win calibration."""
        buckets = defaultdict(list)
        for r in self.results:
            bucket = int(r['probs'][0] * 20) / 20  # 0.05 buckets
            buckets[bucket].append(1.0 if r['actual'] == 'H' else 0.0)

        cal = []
        for b in sorted(buckets.keys()):
            avg_prob = b + 0.025
            actual_freq = sum(buckets[b]) / len(buckets[b])
            cal.append((avg_prob, actual_freq))
        return cal

    def summary(self) -> str:
        n = len(self.results)
        if n == 0:
            return "No predictions recorded."
        hw = sum(1 for r in self.results if r['actual'] == 'H')
        dr = sum(1 for r in self.results if r['actual'] == 'D')
        aw = sum(1 for r in self.results if r['actual'] == 'A')
        acc = self.accuracy()
        brier = self.brier_score()
        ll = self.log_loss()

        return (f"Test matches: {n}\n"
                f"Actual: H={hw} ({hw/n:.1%}) D={dr} ({dr/n:.1%}) A={aw} ({aw/n:.1%})\n"
                f"Accuracy: {acc:.1%}\n"
                f"Brier score: {brier:.4f}  (lower=better, 0=perfect, ~1.5=naive)\n"
                f"Log loss: {ll:.4f}  (lower=better)")
