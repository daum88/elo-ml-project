# ...migrated from src/utils/data_loader.py...

def parse_row(row):
    # For your CSV: Day;Date;Time;Home Team;Result;Away Team
    # row[1]=Date, row[3]=Home, row[4]=Result, row[5]=Away
    if len(row) < 6:
        # print(f"[DEBUG parse_row] Skipping malformed row: {row}")
        return None  # Skip malformed/empty rows
    if row[0].strip().lower() == 'day':
        return None  # Skip header row
    date = row[1]
    team_a = row[3]
    score = row[4]
    team_b = row[5]
    home_team = team_a
    away_team = team_b
    # Handle missing result (not played yet)
    if score.strip() == "-:-":
        # print(f"[DEBUG parse_row] Unplayed fixture: {row}")
        return date, '2025', team_a, team_b, None, None, home_team, away_team
    try:
        score_a, score_b = map(int, score.split(':'))
    except Exception:
        # print(f"[DEBUG parse_row] Could not parse score '{score}' in row: {row}")
        return date, '2025', team_a, team_b, None, None, home_team, away_team
    season = date[:4]  # Use year as season
    # print(f"[DEBUG parse_row] Played fixture: {row} -> {score_a}:{score_b}")
    return date, season, team_a, team_b, score_a, score_b, home_team, away_team

def get_team_form_stats(team_history, use_decay_model=False, decay_rate=0.85):
    """
    Returns form stats for a team, optionally using FormDecayModel for decayed form.
    """
    from elo_sim.ml.form_decay import FormDecayModel
    last5 = team_history[-5:] if len(team_history) >= 5 else team_history
    goals_for = [g['goals_for'] for g in last5 if 'goals_for' in g]
    goals_against = [g['goals_against'] for g in last5 if 'goals_against' in g]
    results = [3 if g.get('goals_for',0) > g.get('goals_against',0) else 1 if g.get('goals_for',0) == g.get('goals_against',0) else 0 for g in last5]
    if use_decay_model:
        model = FormDecayModel(decay_rate=decay_rate)
        form = model.predict(results)
    else:
        form = sum(results) / len(results) if results else 0
    attack_strength = sum(goals_for) / len(goals_for) if goals_for else 0
    defense_strength = sum(goals_against) / len(goals_against) if goals_against else 0
    return {
        'form': form,
        'attack_strength': attack_strength,
        'defense_strength': defense_strength,
        'goals_for': goals_for,
        'goals_against': goals_against,
        'results': results,
    }
