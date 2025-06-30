import csv
import numpy as np
import pandas as pd
from collections import defaultdict
from scipy.optimize import minimize

def fit_team_attack_defense_strengths(fixtures_csv, tau_days=60):
    """
    Fit Poisson regression to estimate each team's attack (lambda_a) and defense (lambda_d) strengths.
    Uses time-decay weighting: weight = exp(-age/tau_days)
    Returns dicts: team_attack, team_defense
    """
    import datetime
    from .data_loader import parse_row
    # Read and parse fixtures
    rows = []
    with open(fixtures_csv, newline='', encoding='utf-8') as f:
        for row in csv.reader(f, delimiter=';'):
            parsed = parse_row(row)
            if parsed and parsed[4] is not None and parsed[5] is not None:
                rows.append(parsed)
    # Build data for regression
    teams = set()
    data = []
    today = datetime.datetime.today()
    for r in rows:
        date, season, home, away, score_h, score_a, _, _ = r
        teams.add(home)
        teams.add(away)
        # Robust date parsing for multiple formats
        try:
            match_date = datetime.datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            try:
                match_date = datetime.datetime.strptime(date, '%d.%m.%Y')
            except ValueError:
                continue  # skip if date is malformed
        age_days = (today - match_date).days
        weight = np.exp(-age_days / tau_days)
        data.append({
            'home': home, 'away': away, 'score_h': score_h, 'score_a': score_a, 'weight': weight
        })
    teams = sorted(teams)
    team_idx = {team: i for i, team in enumerate(teams)}
    # Model: log(mu_home) = base + atk_home - def_away + home_adv
    #        log(mu_away) = base + atk_away - def_home
    def loss(params):
        base, home_adv = params[0], params[1]
        atk = params[2:2+len(teams)]
        dfn = params[2+len(teams):]
        ll = 0
        for d in data:
            i, j = team_idx[d['home']], team_idx[d['away']]
            mu_h = np.exp(base + atk[i] - dfn[j] + home_adv)
            mu_a = np.exp(base + atk[j] - dfn[i])
            # Poisson log-likelihood, weighted
            ll += d['weight'] * (d['score_h'] * np.log(mu_h) - mu_h + d['score_a'] * np.log(mu_a) - mu_a)
        return -ll
    x0 = np.zeros(2 + 2*len(teams))
    res = minimize(loss, x0, method='L-BFGS-B')
    base, home_adv = res.x[0], res.x[1]
    atk = res.x[2:2+len(teams)]
    dfn = res.x[2+len(teams):]
    team_attack = {team: np.exp(base + atk[i]) for i, team in enumerate(teams)}
    team_defense = {team: np.exp(-dfn[i]) for i, team in enumerate(teams)}
    return team_attack, team_defense, home_adv
