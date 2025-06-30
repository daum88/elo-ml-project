# ...migrated from src/utils/home_away_attack_defense.py...
import numpy as np
import csv
import datetime
from .data_loader import parse_row

def fit_home_away_attack_defense(fixtures_csv, tau_days=60):
    """
    Estimate home/away attack and defense for each team using time-decay weighting.
    Returns: dicts for home_attack, home_defense, away_attack, away_defense
    """
    today = datetime.datetime.today()
    teams = set()
    data = []
    with open(fixtures_csv, newline='', encoding='utf-8') as f:
        for row in csv.reader(f, delimiter=';'):
            parsed = parse_row(row)
            if parsed and parsed[4] is not None and parsed[5] is not None:
                date = parsed[0]
                home, away = parsed[2], parsed[3]
                score_h, score_a = parsed[4], parsed[5]
                teams.add(home)
                teams.add(away)
                try:
                    match_date = datetime.datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    try:
                        match_date = datetime.datetime.strptime(date, '%d.%m.%Y')
                    except ValueError:
                        continue
                age_days = (today - match_date).days
                weight = np.exp(-age_days / tau_days)
                data.append({'home': home, 'away': away, 'score_h': score_h, 'score_a': score_a, 'weight': weight})
    teams = sorted(teams)
    team_idx = {team: i for i, team in enumerate(teams)}
    # Model: log(mu_home) = base + home_atk_home - away_def_away
    #        log(mu_away) = base + away_atk_away - home_def_home
    def loss(params):
        base = params[0]
        home_atk = params[1:1+len(teams)]
        home_def = params[1+len(teams):1+2*len(teams)]
        away_atk = params[1+2*len(teams):1+3*len(teams)]
        away_def = params[1+3*len(teams):]
        ll = 0
        for d in data:
            i, j = team_idx[d['home']], team_idx[d['away']]
            mu_h = np.exp(base + home_atk[i] - away_def[j])
            mu_a = np.exp(base + away_atk[j] - home_def[i])
            ll += d['weight'] * (d['score_h'] * np.log(mu_h) - mu_h + d['score_a'] * np.log(mu_a) - mu_a)
        return -ll
    x0 = np.zeros(1 + 4*len(teams))
    from scipy.optimize import minimize
    res = minimize(loss, x0, method='L-BFGS-B')
    base = res.x[0]
    home_atk = res.x[1:1+len(teams)]
    home_def = res.x[1+len(teams):1+2*len(teams)]
    away_atk = res.x[1+2*len(teams):1+3*len(teams)]
    away_def = res.x[1+3*len(teams):]
    home_attack = {team: np.exp(base + home_atk[i]) for i, team in enumerate(teams)}
    home_defense = {team: np.exp(-home_def[i]) for i, team in enumerate(teams)}
    away_attack = {team: np.exp(base + away_atk[i]) for i, team in enumerate(teams)}
    away_defense = {team: np.exp(-away_def[i]) for i, team in enumerate(teams)}
    return home_attack, home_defense, away_attack, away_defense
