#!/usr/bin/env python3
"""
Dixon-Coles model for football goal prediction.
Fits attack/defense parameters and rho (low-scoring draw correlation) via MLE.
"""

import math
from collections import defaultdict
from typing import Dict, List, Tuple


class DixonColesModel:
    """
    Dixon & Coles (1997) model for football scores.

    P(goals_h=x, goals_a=y | attack_h, defense_a, home_adv, rho) =
        tau(x, y, rho) * Poisson(x | lambda_h) * Poisson(y | lambda_a)

    where:
        lambda_h = exp(attack_h - defense_a + home_adv + gamma)
        lambda_a = exp(attack_a - defense_h + gamma)
        tau(x, y, rho) = 1 - rho * lambda_h * lambda_a  if x=0, y=0
                        = 1 + rho * lambda_h              if x=0, y=1
                        = 1 + rho * lambda_a              if x=1, y=0
                        = 1 - rho                          if x=1, y=1
                        = 1                                otherwise
    """

    def __init__(self, rho: float = -0.05):
        self.attack: Dict[str, float] = {}
        self.defense: Dict[str, float] = {}
        self.home_adv: float = 0.3  # home advantage in log-space
        self.intercept: float = 0.0  # baseline scoring rate (gamma)
        self.rho: float = rho  # low-scoring dependence parameter

    def fit(self, matches: List[dict], epochs: int = 100, lr: float = 0.01):
        """
        Fit attack/defense parameters via gradient descent on log-likelihood.

        matches: list of dicts with 'home', 'away', 'home_goals', 'away_goals'
        """
        teams = set()
        for m in matches:
            teams.add(m['home'])
            teams.add(m['away'])

        # Initialize parameters
        for t in teams:
            self.attack[t] = 0.0
            self.defense[t] = 0.0

        n = len(matches)
        for epoch in range(epochs):
            grad_att = defaultdict(float)
            grad_def = defaultdict(float)
            grad_ha = 0.0
            grad_int = 0.0
            grad_rho = 0.0
            total_ll = 0.0

            for m in matches:
                h, a = m['home'], m['away']
                x, y = m['home_goals'], m['away_goals']

                att_h = self.attack[h]
                def_h = self.defense[h]
                att_a = self.attack[a]
                def_a = self.defense[a]

                lambda_h = math.exp(att_h - def_a + self.home_adv + self.intercept)
                lambda_a = math.exp(att_a - def_h + self.intercept)

                # Log-likelihood: log(Poisson(x|λ_h)) + log(Poisson(y|λ_a)) + log(τ)
                ll = (x * math.log(max(lambda_h, 1e-10)) - lambda_h +
                      y * math.log(max(lambda_a, 1e-10)) - lambda_a)

                # τ correction
                tau = 1.0
                if x == 0 and y == 0:
                    tau = max(1e-10, 1.0 - self.rho * lambda_h * lambda_a)
                elif x == 0 and y == 1:
                    tau = max(1e-10, 1.0 + self.rho * lambda_h)
                elif x == 1 and y == 0:
                    tau = max(1e-10, 1.0 + self.rho * lambda_a)
                elif x == 1 and y == 1:
                    tau = max(1e-10, 1.0 - self.rho)
                ll += math.log(tau)
                total_ll += ll

                # Gradients for attack/defense
                # ∂λ_h/∂att_h = λ_h, ∂λ_h/∂def_a = -λ_h
                d_lh = (x / max(lambda_h, 1e-10) - 1.0) * lambda_h
                d_la = (y / max(lambda_a, 1e-10) - 1.0) * lambda_a

                grad_att[h] += d_lh
                grad_def[a] -= d_lh  # defense of away team affects home lambda
                grad_att[a] += d_la
                grad_def[h] -= d_la
                grad_ha += d_lh  # home advantage gradient
                grad_int += d_lh + d_la

                # τ gradient for rho
                if x == 0 and y == 0:
                    grad_rho += -lambda_h * lambda_a / tau
                elif x == 0 and y == 1:
                    grad_rho += lambda_h / tau
                elif x == 1 and y == 0:
                    grad_rho += lambda_a / tau
                elif x == 1 and y == 1:
                    grad_rho += -1.0 / tau

            # Update parameters
            for t in teams:
                self.attack[t] += lr * grad_att[t] / n
                self.defense[t] += lr * grad_def[t] / n
            self.home_adv += lr * grad_ha / n
            self.intercept += lr * grad_int / n
            self.rho += lr * grad_rho / n

            if epoch % 20 == 0:
                avg_ll = total_ll / n
                print(f"  Epoch {epoch}: avg LL = {avg_ll:.3f}, rho = {self.rho:.4f}")

    def predict_goals(self, home: str, away: str) -> Tuple[float, float]:
        """Return expected goals (λ_h, λ_a) for a match."""
        att_h = self.attack.get(home, 0.0)
        def_h = self.defense.get(home, 0.0)
        att_a = self.attack.get(away, 0.0)
        def_a = self.defense.get(away, 0.0)

        lambda_h = math.exp(att_h - def_a + self.home_adv + self.intercept)
        lambda_a = math.exp(att_a - def_h + self.intercept)
        return lambda_h, lambda_a

    def score_probability(self, home: str, away: str, max_goals: int = 8) -> dict:
        """Return probability matrix for all scorelines up to max_goals."""
        lh, la = self.predict_goals(home, away)
        probs = {}
        for x in range(max_goals + 1):
            for y in range(max_goals + 1):
                p = (self._poisson_pmf(x, lh) * self._poisson_pmf(y, la) *
                     self._tau(x, y, lh, la))
                probs[(x, y)] = max(0.0, p)
        return probs

    def outcome_probabilities(self, home: str, away: str) -> Tuple[float, float, float]:
        """Return (p_home_win, p_draw, p_away_win)."""
        lh, la = self.predict_goals(home, away)
        p_h = p_d = p_a = 0.0
        for x in range(9):
            for y in range(9):
                p = (self._poisson_pmf(x, lh) * self._poisson_pmf(y, la) *
                     self._tau(x, y, lh, la))
                if x > y:
                    p_h += p
                elif x == y:
                    p_d += p
                else:
                    p_a += p
        total = p_h + p_d + p_a
        return p_h / total, p_d / total, p_a / total

    def simulate_match(self, home: str, away: str) -> Tuple[int, int]:
        """Simulate a single match using fitted parameters."""
        import random
        lh, la = self.predict_goals(home, away)
        return min(random.randint(0, 8), int(random.gauss(lh, math.sqrt(lh)) + 0.5)), \
               min(random.randint(0, 8), int(random.gauss(la, math.sqrt(la)) + 0.5))

    @staticmethod
    def _poisson_pmf(k: int, lam: float) -> float:
        if lam <= 0:
            return 1.0 if k == 0 else 0.0
        return math.exp(-lam) * (lam ** k) / math.factorial(k)

    def _tau(self, x: int, y: int, lh: float, la: float) -> float:
        if x == 0 and y == 0:
            return max(0.0, 1.0 - self.rho * lh * la)
        elif x == 0 and y == 1:
            return max(0.0, 1.0 + self.rho * lh)
        elif x == 1 and y == 0:
            return max(0.0, 1.0 + self.rho * la)
        elif x == 1 and y == 1:
            return max(0.0, 1.0 - self.rho)
        return 1.0

    def team_strength(self, team: str) -> float:
        """Overall team strength = attack - defense."""
        return self.attack.get(team, 0.0) - self.defense.get(team, 0.0)
