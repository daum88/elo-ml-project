"""
Core simulation logic for football season simulation and analytics.
Refactored from src/utils/__init__.py and helpers.
"""
import csv
import numpy as np
import collections
import pandas as pd
from itertools import groupby
from elo_sim.utils.data_loader import parse_row, get_team_form_stats
from elo_sim.utils.fit_team_attack_defense_strengths import fit_team_attack_defense_strengths
from elo_sim.utils.home_away_attack_defense import fit_home_away_attack_defense

# --- Poisson/Elo helpers ---
def expected_goals_v2(elo_a, elo_b, team_a_stats, team_b_stats, home_adv):
    atk = float(np.clip(team_a_stats.get("avg_goals_for", 1.5), 0.7, 3.0))
    def_opp = float(np.clip(team_b_stats.get("avg_goals_against", 1.5), 0.7, 3.0))
    elo_effect = 0.12 * ((elo_a - elo_b) / 100)
    base = (atk * 1.15) / (0.85 * def_opp + 0.7) + 0.15
    mu = base + elo_effect + home_adv
    return max(0.8, min(mu, 4.0))

def poisson_match(mu_a, mu_b):
    goals_a = np.random.poisson(mu_a)
    goals_b = np.random.poisson(mu_b)
    return goals_a, goals_b

def expected_score(rating_a, rating_b):
    # Clamp exponent to avoid overflow
    diff = (rating_b - rating_a) / 400
    diff = max(min(diff, 100), -100)
    return 1 / (1 + 10 ** diff)

def update_elo(rating, expected, actual, volatility=1.0, k=60):
    return rating + k * volatility * (actual - expected)

def process_fixtures(csv_file, season_to_analyze, history_csv="elo_history.csv"):
    ratings = {}
    history_rows = []
    team_game_history = {}
    fixtures = []
    biggest_gain = {"team": None, "gain": float('-inf'), "game": None}
    biggest_loss = {"team": None, "loss": float('inf'), "game": None}
    try:
        all_teams = set()
        with open(csv_file, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)
            for row in reader:
                parsed = parse_row(row)
                if not parsed or len(parsed) != 8:
                    continue
                date, season, team_a, team_b, score_a, score_b, home_team, away_team = parsed
                if season != season_to_analyze:
                    continue
                # Only append if all required fields are present (except scores)
                if None in (date, season, team_a, team_b, home_team, away_team):
                    continue
                fixtures.append((date, team_a, team_b, home_team, away_team, score_a, score_b, -1))
                all_teams.update([home_team, away_team])
        # Initialize ratings and team_game_history for all teams
        for team in all_teams:
            if team not in ratings:
                ratings[team] = 1500
            if team not in team_game_history:
                team_game_history[team] = {"attack_strength": 1.0, "defense_strength": 1.0, "goals_for": 0, "goals_against": 0, "matches": 0}
        return ratings, biggest_gain, biggest_loss, team_game_history, fixtures
    except Exception as e:
        import traceback
        traceback.print_exc()
        return ratings, biggest_gain, biggest_loss, team_game_history, fixtures

def calc_home_away_advantage(played_games, teams):
    """
    Calculate home and away advantage for teams based on played games.
    Migrated code from src/utils/__init__.py
    """
    home_away_advantage = {}
    for team in teams:
        home_games = [game for game in played_games if game["home_team"] == team]
        away_games = [game for game in played_games if game["away_team"] == team]

        home_wins = sum(1 for game in home_games if game["home_goals"] > game["away_goals"])
        home_draws = sum(1 for game in home_games if game["home_goals"] == game["away_goals"])
        home_losses = sum(1 for game in home_games if game["home_goals"] < game["away_goals"])

        away_wins = sum(1 for game in away_games if game["away_goals"] > game["home_goals"])
        away_draws = sum(1 for game in away_games if game["away_goals"] == game["home_goals"])
        away_losses = sum(1 for game in away_games if game["away_goals"] < game["home_goals"])

        total_games = len(home_games) + len(away_games)
        if total_games > 0:
            home_win_rate = home_wins / len(home_games) if len(home_games) > 0 else 0
            away_win_rate = away_wins / len(away_games) if len(away_games) > 0 else 0
            home_draw_rate = home_draws / len(home_games) if len(home_games) > 0 else 0
            away_draw_rate = away_draws / len(away_games) if len(away_games) > 0 else 0

            # Simple linear model for home/away advantage
            home_advantage = home_win_rate - away_win_rate
            away_advantage = away_win_rate - home_win_rate

            home_away_advantage[team] = {"home_advantage": home_advantage, "away_advantage": away_advantage}
        else:
            home_away_advantage[team] = {"home_advantage": 0, "away_advantage": 0}

    return home_away_advantage

def simulate_game(elo_a, elo_b, n_sim=10000, home_adv_goals=0.0, team_a_stats=None, team_b_stats=None):
    """
    Simulate a game between two teams using their Elo ratings and other factors.
    Migrated code from src/utils/__init__.py
    """
    elo_a = float(elo_a)
    elo_b = float(elo_b)

    # Calculate home advantage based on historical data
    home_advantage = 0.0
    away_advantage = 0.0

    if team_a_stats is not None and team_b_stats is not None:
        home_advantage = team_a_stats.get("home_advantage", 0.0)
        away_advantage = team_b_stats.get("away_advantage", 0.0)

    # Simulate multiple seasons to get a distribution of outcomes
    results = {"home_wins": 0, "away_wins": 0, "draws": 0}
    for _ in range(n_sim):
        # Calculate expected goals for each team
        mu_home = expected_goals_v2(elo_a, elo_b, team_a_stats, team_b_stats, home_advantage)
        mu_away = expected_goals_v2(elo_b, elo_a, team_b_stats, team_a_stats, away_advantage)

        # Simulate the match using the Poisson distribution
        simulated_goals_home, simulated_goals_away = poisson_match(mu_home, mu_away)

        # Determine result
        if simulated_goals_home > simulated_goals_away:
            results["home_wins"] += 1
        elif simulated_goals_home < simulated_goals_away:
            results["away_wins"] += 1
        else:
            results["draws"] += 1

    return results

def simulate_season(
    csv_file, season_to_analyze, n_sim=1, injury_prob=0.05, k_decay=0.98,
    poisson_base=1.4, ml_model=None, head2head_boost=0.25, fatigue_penalty=0.1, shock_prob=0.01, shock_strength=0.5,
    calibration_params=None, visualize_callback=None, backtest_actual=None,
    fatigue_window=5, dynamic_home_adv=True, use_ml_xg=False, k_factor=75
):
    """
    Simulate an entire season for all teams in the league.
    For played games, use actual result. For unplayed, sample a single Poisson outcome and update Elo/points.
    Adds a fixed home advantage, a head-to-head bonus, and a slightly smaller random form factor.
    """
    import traceback
    try:
        ratings, biggest_gain, biggest_loss, team_game_history, fixtures = process_fixtures(csv_file, season_to_analyze)

        if not fixtures:
            return []

        # Helper: rolling window for attack/defense (last N games)
        def get_rolling_stats(team, last_n=7):
            games = []
            for fx in fixtures:
                date, team_a, team_b, home_team, away_team, score_a, score_b, _ = fx
                if score_a is not None and score_b is not None and str(score_a).isdigit() and str(score_b).isdigit():
                    if home_team == team:
                        games.append((int(score_a), int(score_b)))
                    elif away_team == team:
                        games.append((int(score_b), int(score_a)))
            games = games[-last_n:]
            if not games:
                return {"avg_goals_for": 1.5, "avg_goals_against": 1.5}
            gf = np.mean([g[0] for g in games])
            ga = np.mean([g[1] for g in games])
            return {"avg_goals_for": gf, "avg_goals_against": ga}

        HOME_ADV = 0.2  # Fixed home advantage in goals
        FORM_STD = 0.10  # Reduced form noise
        HEAD2HEAD_BONUS = head2head_boost  # Bonus to Poisson mean if team has already beaten opponent

        # Build head-to-head win map from played games
        h2h_wins = {}
        for fx in fixtures:
            date, team_a, team_b, home_team, away_team, score_a, score_b, _ = fx
            if score_a is not None and score_b is not None and str(score_a).isdigit() and str(score_b).isdigit():
                if int(score_a) > int(score_b):
                    h2h_wins.setdefault((home_team, away_team), 0)
                    h2h_wins[(home_team, away_team)] += 1
                elif int(score_b) > int(score_a):
                    h2h_wins.setdefault((away_team, home_team), 0)
                    h2h_wins[(away_team, home_team)] += 1

        results = []
        for fx in fixtures:
            if not fx or len(fx) != 8:
                continue
            date, team_a, team_b, home_team, away_team, score_a, score_b, _ = fx
            if any(x is None for x in (date, team_a, team_b, home_team, away_team)):
                continue
            # If played, use actual result
            if score_a is not None and score_b is not None and str(score_a).isdigit() and str(score_b).isdigit():
                score_a = int(score_a)
                score_b = int(score_b)
                results.append({
                    'date': date,
                    'team_a': team_a,
                    'team_b': team_b,
                    'goals_a': score_a,
                    'goals_b': score_b,
                    'elo_a': ratings.get(team_a, 1500),
                    'elo_b': ratings.get(team_b, 1500),
                    'points_a': 3 if score_a > score_b else 1 if score_a == score_b else 0,
                    'points_b': 3 if score_b > score_a else 1 if score_a == score_b else 0,
                    'actual': True
                })
                # Update Elo ratings for played games
                home_expected = expected_score(ratings[home_team], ratings[away_team])
                away_expected = expected_score(ratings[away_team], ratings[home_team])
                ratings[home_team] = update_elo(ratings[home_team], home_expected, 1 if score_a > score_b else 0.5 if score_a == score_b else 0, k=k_factor)
                ratings[away_team] = update_elo(ratings[away_team], away_expected, 1 if score_b > score_a else 0.5 if score_a == score_b else 0, k=k_factor)
            else:
                # Simulate a single random result for unplayed fixture
                home_stats = get_rolling_stats(home_team, last_n=7)
                away_stats = get_rolling_stats(away_team, last_n=7)
                form_home = np.random.normal(0, FORM_STD)
                form_away = np.random.normal(0, FORM_STD)
                # Head-to-head bonus: if home_team has already beaten away_team, boost their Poisson mean
                h2h_bonus_home = HEAD2HEAD_BONUS if h2h_wins.get((home_team, away_team), 0) > 0 else 0
                h2h_bonus_away = HEAD2HEAD_BONUS if h2h_wins.get((away_team, home_team), 0) > 0 else 0

                # --- Dynamic momentum bonus: recalculate current leader(s) and margin before each fixture ---
                current_points = {team: 0 for team in ratings}
                for r in results:
                    current_points[r['team_a']] += r['points_a']
                    current_points[r['team_b']] += r['points_b']
                max_pts = max(current_points.values())
                leaders = [t for t, v in current_points.items() if v == max_pts]
                leader_margins = {t: max_pts - max([v for t2, v in current_points.items() if t2 != t], default=0) for t in leaders}
                momentum_bonus = 0.15 if (home_team in leaders and leader_margins.get(home_team, 0) >= 4) else 0
                mu_home = expected_goals_v2(ratings[home_team], ratings[away_team], home_stats, away_stats, HOME_ADV) + form_home + h2h_bonus_home + momentum_bonus
                momentum_bonus_away = 0.15 if (away_team in leaders and leader_margins.get(away_team, 0) >= 4) else 0
                mu_away = expected_goals_v2(ratings[away_team], ratings[home_team], away_stats, home_stats, 0) + form_away + h2h_bonus_away + momentum_bonus_away
                mu_home = max(0.5, mu_home)
                mu_away = max(0.5, mu_away)
                simulated_goals_home, simulated_goals_away = poisson_match(mu_home, mu_away)
                results.append({
                    'date': date,
                    'team_a': team_a,
                    'team_b': team_b,
                    'goals_a': simulated_goals_home,
                    'goals_b': simulated_goals_away,
                    'elo_a': ratings.get(team_a, 1500),
                    'elo_b': ratings.get(team_b, 1500),
                    'points_a': 3 if simulated_goals_home > simulated_goals_away else 1 if simulated_goals_home == simulated_goals_away else 0,
                    'points_b': 3 if simulated_goals_away > simulated_goals_home else 1 if simulated_goals_home == simulated_goals_away else 0,
                    'actual': False
                })
                # Update Elo ratings for simulated games
                home_expected = expected_score(ratings[home_team], ratings[away_team])
                away_expected = expected_score(ratings[away_team], ratings[home_team])
                ratings[home_team] = update_elo(ratings[home_team], home_expected, 1 if simulated_goals_home > simulated_goals_away else 0.5 if simulated_goals_home == simulated_goals_away else 0, k=k_factor)
                ratings[away_team] = update_elo(ratings[away_team], away_expected, 1 if simulated_goals_away > simulated_goals_home else 0.5 if simulated_goals_home == simulated_goals_away else 0, k=k_factor)
                # Update team stats
                team_game_history[home_team]["goals_for"] += simulated_goals_home
                team_game_history[home_team]["goals_against"] += simulated_goals_away
                team_game_history[home_team]["matches"] += 1
                team_game_history[away_team]["goals_for"] += simulated_goals_away
                team_game_history[away_team]["goals_against"] += simulated_goals_home
                team_game_history[away_team]["matches"] += 1
        return results
    except Exception as e:
        traceback.print_exc()
        return []

def compute_expected_points_table(csv_file, season_to_analyze, n_sim=1000):
    """
    For each fixture, if played, use actual result and update Elo/points. If unplayed, simulate n_sim times using current ratings, average points, and update Elo with expected result.
    Returns: dict {team: points}
    """
    ratings, _, _, team_game_history, fixtures = process_fixtures(csv_file, season_to_analyze)
    team_points = {team: 0.0 for team in ratings}
    played, unplayed = 0, 0
    for fx in fixtures:
        # Only skip if required non-score fields are missing
        if not fx or len(fx) != 8:
            continue
        date, team_a, team_b, home_team, away_team, score_a, score_b, _ = fx
        if None in (date, team_a, team_b, home_team, away_team):
            continue
        # If played, use actual result and update Elo
        if score_a is not None and score_b is not None and str(score_a).isdigit() and str(score_b).isdigit():
            played += 1
            score_a = int(score_a)
            score_b = int(score_b)
            if score_a > score_b:
                team_points[home_team] += 3
            elif score_a == score_b:
                team_points[home_team] += 1
                team_points[away_team] += 1
            else:
                team_points[away_team] += 3
            # Update Elo ratings
            home_expected = expected_score(ratings[home_team], ratings[away_team])
            away_expected = expected_score(ratings[away_team], ratings[home_team])
            actual_home = 1 if score_a > score_b else 0.5 if score_a == score_b else 0
            actual_away = 1 if score_b > score_a else 0.5 if score_a == score_b else 0
            ratings[home_team] = update_elo(ratings[home_team], home_expected, actual_home)
            ratings[away_team] = update_elo(ratings[away_team], away_expected, actual_away)
        else:
            unplayed += 1
            # Simulate n_sim times for unplayed
            sim = simulate_game(
                ratings[home_team], ratings[away_team],
                n_sim=n_sim, home_adv_goals=0.0, team_a_stats=team_game_history[home_team], team_b_stats=team_game_history[away_team]
            )
            total = sim['home_wins'] + sim['away_wins'] + sim['draws']
            win_prob_home = sim['home_wins'] / total if total > 0 else 0.0
            win_prob_away = sim['away_wins'] / total if total > 0 else 0.0
            draw_prob = sim['draws'] / total if total > 0 else 0.0
            team_points[home_team] += 3 * win_prob_home + 1 * draw_prob
            team_points[away_team] += 3 * win_prob_away + 1 * draw_prob
            # Optionally update Elo with expected result (for realism)
            actual_home = win_prob_home + 0.5 * draw_prob
            actual_away = win_prob_away + 0.5 * draw_prob
            home_expected = expected_score(ratings[home_team], ratings[away_team])
            away_expected = expected_score(ratings[away_team], ratings[home_team])
            ratings[home_team] = update_elo(ratings[home_team], home_expected, actual_home)
            ratings[away_team] = update_elo(ratings[away_team], away_expected, actual_away)
    return team_points

def simulate_multiple_seasons(csv_file, season_to_analyze, n_sim=1000, n_runs=100):
    """
    Run simulate_season n_runs times, aggregate points/rank stats for each team.
    Returns: (summary, biggest_sim_win, biggest_sim_loss, biggest_gd_win, biggest_gd_loss, all_sim_results)
    Now also tracks win/unbeaten/losing streaks, clinch and elimination dates.
    """
    all_sim_results = []
    team_points_runs = {}
    team_elo_runs = {}
    team_gd_runs = {}
    win_streaks = {}
    unbeaten_streaks = {}
    losing_streaks = {}
    clinch_dates = {}
    elimination_dates = {}
    # Track biggest win/loss/elo gain/loss
    biggest_gd_win = {}
    biggest_gd_loss = {}
    biggest_elo_win = {}
    biggest_elo_loss = {}
    for run in range(n_runs):
        results = simulate_season(csv_file, season_to_analyze, n_sim=n_sim)
        all_sim_results.append({'results': results})
        # Aggregate points, elo, gd per team
        points = {}
        elos = {}
        gds = {}
        team_results = {}
        # Track per-run biggests
        run_gd_win = {}
        run_gd_loss = {}
        run_elo_win = {}
        run_elo_loss = {}
        for r in results:
            for team, is_home in [(r['team_a'], True), (r['team_b'], False)]:
                opponent = r['team_b'] if is_home else r['team_a']
                if team not in points:
                    points[team] = 0.0
                    elos[team] = []
                    gds[team] = 0
                    team_results[team] = []
                if is_home:
                    ga, gb = r['goals_a'], r['goals_b']
                    elo = r.get('elo_a', 1500)
                else:
                    ga, gb = r['goals_b'], r['goals_a']
                    elo = r.get('elo_b', 1500)
                elos[team].append(elo)
                # Track result for streaks
                if ga > gb:
                    result = 'W'
                elif ga == gb:
                    result = 'D'
                else:
                    result = 'L'
                team_results[team].append({'result': result, 'score': f"{ga}:{gb}", 'opponent': opponent, 'sim': run})
                # Points and GD
                if result == 'W':
                    points[team] += 3
                elif result == 'D':
                    points[team] += 1
                gds[team] += (ga or 0) - (gb or 0)
                # Track biggest win/loss by GD
                gd = (ga or 0) - (gb or 0)
                if team not in run_gd_win or gd > run_gd_win[team]['gd']:
                    run_gd_win[team] = {'gd': gd, 'score': f"{ga}:{gb}", 'opponent': opponent, 'date': r['date'], 'sim': run}
                if team not in run_gd_loss or gd < run_gd_loss[team]['gd']:
                    run_gd_loss[team] = {'gd': gd, 'score': f"{ga}:{gb}", 'opponent': opponent, 'date': r['date'], 'sim': run}
                # Track biggest Elo gain/loss (difference from previous match)
                if len(elos[team]) > 1:
                    elo_diff = elos[team][-1] - elos[team][-2]
                    if team not in run_elo_win or elo_diff > run_elo_win[team]['elo_diff']:
                        run_elo_win[team] = {'elo_diff': elo_diff, 'score': f"{ga}:{gb}", 'opponent': opponent, 'date': r['date'], 'sim': run}
                    if team not in run_elo_loss or elo_diff < run_elo_loss[team]['elo_diff']:
                        run_elo_loss[team] = {'elo_diff': elo_diff, 'score': f"{ga}:{gb}", 'opponent': opponent, 'date': r['date'], 'sim': run}
        # Aggregate per-run biggests
        for team in points:
            if team in run_gd_win:
                if team not in biggest_gd_win or run_gd_win[team]['gd'] > biggest_gd_win[team]['gd']:
                    biggest_gd_win[team] = run_gd_win[team]
            if team in run_gd_loss:
                if team not in biggest_gd_loss or run_gd_loss[team]['gd'] < biggest_gd_loss[team]['gd']:
                    biggest_gd_loss[team] = run_gd_loss[team]
            if team in run_elo_win:
                if team not in biggest_elo_win or run_elo_win[team]['elo_diff'] > biggest_elo_win[team]['elo_diff']:
                    biggest_elo_win[team] = run_elo_win[team]
            if team in run_elo_loss:
                if team not in biggest_elo_loss or run_elo_loss[team]['elo_diff'] < biggest_elo_loss[team]['elo_diff']:
                    biggest_elo_loss[team] = run_elo_loss[team]
            team_points_runs.setdefault(team, []).append(points[team])
            team_elo_runs.setdefault(team, []).append(np.mean(elos[team]) if elos[team] else 1500)
            team_gd_runs.setdefault(team, []).append(gds[team])
    # Compute summary stats
    summary = {}
    for team in team_points_runs:
        pts = np.array(team_points_runs[team])
        elos = np.array(team_elo_runs[team])
        gds = np.array(team_gd_runs[team])
        # Find best win/unbeaten/losing streaks
        best_win = max(win_streaks.get(team, []), key=lambda x: x['length'], default={})
        best_unbeaten = max(unbeaten_streaks.get(team, []), key=lambda x: x['length'], default={})
        best_losing = max(losing_streaks.get(team, []), key=lambda x: x['length'], default={})
        summary[team] = {
            'mean_pts': float(np.mean(pts)),
            'std_pts': float(np.std(pts)),
            'min_pts': float(np.min(pts)),
            'max_pts': float(np.max(pts)),
            'pts_ci_90': (float(np.percentile(pts, 5)), float(np.percentile(pts, 95))),
            'pts_ci_95': (float(np.percentile(pts, 2.5)), float(np.percentile(pts, 97.5))),
            'mean_elo': float(np.mean(elos)),
            'std_elo': float(np.std(elos)),
            'mean_gd': float(np.mean(gds)),
            'longest_win_streak': best_win,
            'longest_unbeaten_streak': best_unbeaten,
            'longest_losing_streak': best_losing,
            # 'clinch_dates': [],
            # 'elimination_dates': [],
        }
    # Dummy values for biggest_sim_win/loss/gd_win/gd_loss for now
    biggest_sim_win = biggest_sim_loss = biggest_gd_win = biggest_gd_loss = None
    for team in team_points_runs:
        # Aggregate clinch/elimination dates
        clinch_list = [d for d in clinch_dates.get(team, []) if d is not None]
        elim_list = [d for d in elimination_dates.get(team, []) if d is not None]
        summary[team].update({
            'clinch_dates': {
                'earliest': min(clinch_list) if clinch_list else None,
                'latest': max(clinch_list) if clinch_list else None,
                'all': clinch_list
            },
            'elimination_dates': {
                'earliest': min(elim_list) if elim_list else None,
                'latest': max(elim_list) if elim_list else None,
                'all': elim_list
            }
        })
    return summary, biggest_gd_win, biggest_gd_loss, biggest_elo_win, biggest_elo_loss, all_sim_results
