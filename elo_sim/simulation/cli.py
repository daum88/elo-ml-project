"""
CLI entry point for football season simulation and analysis.
Modernized, modular, and uses the new elo_sim package structure.
"""
import csv
import numpy as np
import pandas as pd
from collections import Counter
import argparse

from elo_sim.simulation.core import simulate_season, simulate_game, process_fixtures, calc_home_away_advantage, compute_expected_points_table
from elo_sim.utils.data_loader import parse_row, get_team_form_stats

START_RATING = 1500
K = 60  # More reactionary

# --- Improved Poisson goal model helpers ---
def print_team_stats(team, summary, biggest_gd_win=None, biggest_gd_loss=None, sim_results=None):
    stats = summary[team]
    print(f"\n--- {team} ---")
    print(f"mean_pts: {stats['mean_pts']:.2f}")
    print(f"std_pts: {stats['std_pts']:.2f}")
    print(f"min_pts: {stats['min_pts']:.0f}")
    print(f"max_pts: {stats['max_pts']:.0f}")
    print(f"pts_ci_90: {stats['pts_ci_90']}")
    print(f"pts_ci_95: {stats['pts_ci_95']}")
    print(f"mean_elo: {stats['mean_elo']:.2f}")
    print(f"std_elo: {stats['std_elo']:.2f}")
    print(f"mean_gd: {stats['mean_gd']:.2f}")
    # Longest win streak
    lw = stats.get('longest_win_streak', {})
    if lw and lw.get('length', 0) > 0:
        streak_games = lw.get('games', [])
        streak_str = ", ".join([f"{g['score']} vs {g['opponent']}" for g in streak_games])
        print(f"Longest win streak: {lw['length']} (Sim {lw.get('sim','?')}, Games: {streak_str})")
    else:
        print("Longest win streak: []")
    # Longest unbeaten streak
    lu = stats.get('longest_unbeaten_streak', {})
    if lu and lu.get('length', 0) > 0:
        streak_games = lu.get('games', [])
        streak_str = ", ".join([f"{g['score']} vs {g['opponent']}" for g in streak_games])
        print(f"Longest unbeaten streak: {lu['length']} (Sim {lu.get('sim','?')}, Games: {streak_str})")
    else:
        print("Longest unbeaten streak: []")
    # Longest losing streak
    ll = stats.get('longest_losing_streak', {})
    if ll and ll.get('length', 0) > 0:
        streak_games = ll.get('games', [])
        streak_str = ", ".join([f"{g['score']} vs {g['opponent']}" for g in streak_games])
        print(f"Longest losing streak: {ll['length']} (Sim {ll.get('sim','?')}, Games: {streak_str})")
    else:
        print("Longest losing streak: []")
    # Clinch/elimination dates
    clinch = stats.get('clinch_dates', {})
    elim = stats.get('elimination_dates', {})
    print(f"Clinch dates: Earliest: {clinch.get('earliest')}, Latest: {clinch.get('latest')}")
    print(f"Elimination dates: Earliest: {elim.get('earliest')}, Latest: {elim.get('latest')}")
    # Most common scorelines and avg goals for/against
    if sim_results:
        scores = [f"{r['goals_a']}:{r['goals_b']}" for r in sim_results if r['team_a'] == team]
        if scores:
            most_common = Counter(scores).most_common(3)
            # print("Most common scorelines as home:", ", ".join(f"{s} ({c}x)" for s, c in most_common))
        goals_for = [r['goals_a'] for r in sim_results if r['team_a'] == team]
        goals_against = [r['goals_b'] for r in sim_results if r['team_a'] == team]
        if goals_for:
            # print(f"Avg goals for (home): {np.mean(goals_for):.2f}, against: {np.mean(goals_against):.2f}")
            pass

def main():
    DEFAULT_FILENAME = "data/your_data.csv"
    DEFAULT_SEASON = "2025"
    parser = argparse.ArgumentParser(description="Football season simulation and analysis CLI.")
    parser.add_argument('--simulate', type=int, help='Run N season simulations and print summary table')
    parser.add_argument('--export', action='store_true', help='Export last simulation results to CSV')
    parser.add_argument('--team', type=str, help='Analyze a team by (fuzzy) name')
    parser.add_argument('--h2h', nargs=2, metavar=('TEAM_A', 'TEAM_B'), help='Head-to-head analysis for two teams')
    parser.add_argument('--file', type=str, default=DEFAULT_FILENAME, help='CSV file to use')
    parser.add_argument('--season', type=str, default=DEFAULT_SEASON, help='Season to use')
    args, unknown = parser.parse_known_args()

    # If any CLI args are given, run in non-interactive mode
    if args.simulate or args.export or args.team or args.h2h:
        # --- Non-interactive mode logic ---
        if args.simulate:
            # Use the robust simulation summary from core
            from elo_sim.simulation.core import simulate_multiple_seasons
            summary, *_ = simulate_multiple_seasons(args.file, args.season, n_sim=1000, n_runs=args.simulate)
            print("\n--- Simulation summary table (mean, std, min, max, 90%/95% CI) ---")
            table = [
                (team,
                 stats.get('mean_pts', 0),
                 stats.get('std_pts', 0),
                 stats.get('min_pts', 0),
                 stats.get('max_pts', 0),
                 stats.get('mean_elo', 1500),
                 stats.get('std_elo', 0),
                 stats.get('mean_gd', 0),
                 stats.get('pts_ci_90', ('','')),
                 stats.get('pts_ci_95', ('',''))
                )
                for team, stats in summary.items()
            ]
            table = sorted(table, key=lambda x: (x[1], x[7], x[5]), reverse=True)
            print(f"{'Team':<20} {'MeanPts':>7} {'Std':>6} {'Min':>5} {'Max':>5} {'Elo':>7} {'StdElo':>7} {'GD':>6} {'90% CI':>18} {'95% CI':>18}")
            for team, mean_pts, std_pts, min_pts, max_pts, mean_elo, std_elo, mean_gd, ci90, ci95 in table:
                print(f"{team:<20} {mean_pts:7.2f} {std_pts:6.2f} {min_pts:5.0f} {max_pts:5.0f} {mean_elo:7.1f} {std_elo:7.1f} {mean_gd:6.2f} {str(ci90):>18} {str(ci95):>18}")
            return
        # Team analysis
        if args.team:
            team_name = args.team
            # Load the last simulation results
            with open('simulation_results.csv', 'r') as input_file:
                reader = csv.DictReader(input_file)
                team_results = [row for row in reader if row['team_a'] == team_name or row['team_b'] == team_name]
            if not team_results:
                print(f"No results found for team '{team_name}'.")
            else:
                # Calculate and print the desired statistics
                print(f"\n--- Season summary for {team_name} ---")
                print(f"Total games: {len(team_results)}")
                print(f"Total points: {sum(int(r['points_a']) if r['team_a'] == team_name else int(r['points_b']) for r in team_results)}")
                print(f"Goal difference: {sum(int(r['goals_a']) - int(r['goals_b']) if r['team_a'] == team_name else int(r['goals_b']) - int(r['goals_a']) for r in team_results)}")
                print(f"Average rank: {np.mean([int(r['rank_a']) if r['team_a'] == team_name else int(r['rank_b']) for r in team_results]):.2f}")
                print(f"Best rank: {min(int(r['rank_a']) if r['team_a'] == team_name else int(r['rank_b']) for r in team_results)}")
                print(f"Worst rank: {max(int(r['rank_a']) if r['team_a'] == team_name else int(r['rank_b']) for r in team_results)}")
                # Head-to-head analysis
                if args.h2h:
                    opponent = args.h2h[1] if args.h2h[0] == team_name else args.h2h[0]
                    h2h_results = [r for r in team_results if r['team_a'] == team_name and r['opponent'] == opponent or r['team_b'] == team_name and r['opponent'] == opponent]
                    if not h2h_results:
                        print(f"No head-to-head results found between {team_name} and {opponent}.")
                    else:
                        wins = sum(1 for r in h2h_results if (r['team_a'] == team_name and r['goals_a'] > r['goals_b']) or (r['team_b'] == team_name and r['goals_b'] > r['goals_a']))
                        losses = sum(1 for r in h2h_results if (r['team_a'] == team_name and r['goals_a'] < r['goals_b']) or (r['team_b'] == team_name and r['goals_b'] < r['goals_a']))
                        draws = len(h2h_results) - wins - losses
                        print(f"Head-to-head results against {opponent}: {wins}W-{losses}L-{draws}D")
        return

    # --- Interactive mode logic ---
    # Load the data
    try:
        with open(args.file, 'r') as f:
            reader = csv.DictReader(f)
            fixtures = [row for row in reader]
    except Exception as e:
        print(f"Error loading data file: {e}")
        return

    # Process the fixtures (always use file path and season)
    try:
        processed_fixtures = process_fixtures(args.file, args.season)
    except Exception as e:
        print(f"Error processing fixtures: {e}")
        return

    # Simulate the season
    try:
        season_results = simulate_season(args.file, args.season, k_factor=K)
    except Exception as e:
        print(f"Error simulating season: {e}")
        return

    # Print the results
    if not season_results or not isinstance(season_results, list):
        print("No valid season results to display.")
        return
    print("\n--- Season simulation results ---")
    for result in season_results:
        print(f"{result['team_a']} {result['goals_a']} - {result['goals_b']} {result['team_b']} (Elo: {result['elo_a']} - {result['elo_b']})")

    # Calculate and print league table
    try:
        # Calculate expected points for each team
        team_points = compute_expected_points_table(args.file, args.season, n_sim=1000)
        table = [
            {'team': team, 'points': round(pts, 2)}
            for team, pts in team_points.items()
        ]
        table = sorted(table, key=lambda x: x['points'], reverse=True)
        print("\n--- Final league table (actual + expected points) ---")
        for i, team in enumerate(table, start=1):
            print(f"{i}. {team['team']} - {team['points']} pts")
    except Exception as e:
        print(f"Error calculating league table: {e}")

    # Ask if the user wants to simulate another season
    while True:
        try:
            again = input("\nSimulate another season? (y/n): ").strip().lower()
            if again == 'y':
                main()
                break
            elif again == 'n':
                print("Exiting program. Goodbye!")
                break
            else:
                print("Invalid input, please enter 'y' or 'n'.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception as e:
        print("[FATAL ERROR] Unhandled exception in CLI main():")
        traceback.print_exc()
