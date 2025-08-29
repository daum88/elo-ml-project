#!/usr/bin/env python3
"""
Enhanced Estonian Football Predictor with Dynamic Performance Tracking

Implements comprehensive opponent-weighted dynamic metrics:
- All team characteristics update after every match based on opponent strengt                print("  📁 Processing esiliigab2025.csv...")
                esiliiga_b_df = pd.read_csv('esiliigab2025.csv')- Beating strong teams has more impact than beating weak teams
- Metrics include: attacking performance, defensive strength, home/away advantage, form
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import csv
import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple, Any
import random
import math
import os


class DynamicPerformanceTracker:
    """Track dynamic team performance metrics weighted by opponent strength"""
    
    def __init__(self):
        self.team_metrics = defaultdict(lambda: {
            'attacking_performance': {'home': 1.0, 'away': 1.0, 'overall': 1.0},
            'defensive_strength': {'home': 1.0, 'away': 1.0, 'overall': 1.0},
            'home_advantage': 1.0,
            'form': 0.0,
            'consistency': 1.0,
            'recent_matches': deque(maxlen=10),
            'goals_for_trend': deque(maxlen=10),
            'goals_against_trend': deque(maxlen=10),
            'expected_performance': 1.0
        })
        
    def get_opponent_strength_factor(self, opponent_elo: float, league_avg: float = 1500) -> float:
        """Calculate opponent strength factor (0.5 to 2.0)"""
        strength_ratio = opponent_elo / league_avg
        return max(0.5, min(2.0, strength_ratio))
    
    def update_attacking_performance(self, team: str, goals_scored: int, expected_goals: float, 
                                   opponent_elo: float, is_home: bool, league_avg: float = 1500):
        """Update attacking performance based on goals vs expected goals, weighted by opponent"""
        opponent_factor = self.get_opponent_strength_factor(opponent_elo, league_avg)
        
        # Performance vs expectation
        if expected_goals > 0:
            performance_ratio = goals_scored / expected_goals
        else:
            performance_ratio = 1.0 if goals_scored == 0 else 2.0
            
        # Weight by opponent strength and recency
        weighted_performance = performance_ratio * opponent_factor * 0.1  # Small update
        
        venue = 'home' if is_home else 'away'
        current = self.team_metrics[team]['attacking_performance'][venue]
        self.team_metrics[team]['attacking_performance'][venue] = current * 0.9 + weighted_performance * 0.1
        
        # Update overall
        home_perf = self.team_metrics[team]['attacking_performance']['home']
        away_perf = self.team_metrics[team]['attacking_performance']['away']
        self.team_metrics[team]['attacking_performance']['overall'] = (home_perf + away_perf) / 2
        
    def update_defensive_strength(self, team: str, goals_conceded: int, expected_goals_against: float,
                                opponent_elo: float, is_home: bool, league_avg: float = 1500):
        """Update defensive strength based on goals conceded vs expected, weighted by opponent"""
        opponent_factor = self.get_opponent_strength_factor(opponent_elo, league_avg)
        
        # Lower goals conceded vs expectation = better defense
        if expected_goals_against > 0:
            defensive_ratio = expected_goals_against / max(1, goals_conceded)
        else:
            defensive_ratio = 2.0 if goals_conceded == 0 else 0.5
            
        # Weight by opponent strength
        weighted_defense = defensive_ratio * opponent_factor * 0.1
        
        venue = 'home' if is_home else 'away'
        current = self.team_metrics[team]['defensive_strength'][venue]
        new_value = current * 0.9 + weighted_defense * 0.1
        # Keep defensive values in reasonable bounds (0.5 to 2.0)
        self.team_metrics[team]['defensive_strength'][venue] = max(0.5, min(2.0, new_value))
        
        # Update overall
        home_def = self.team_metrics[team]['defensive_strength']['home']
        away_def = self.team_metrics[team]['defensive_strength']['away']
        self.team_metrics[team]['defensive_strength']['overall'] = (home_def + away_def) / 2
        
    def update_home_advantage(self, team: str, home_goals: int, away_goals: int, 
                            home_expected: float, away_expected: float, opponent_elo: float, league_avg: float = 1500):
        """Update home advantage based on home performance vs away performance"""
        opponent_factor = self.get_opponent_strength_factor(opponent_elo, league_avg)
        
        # Home advantage = (home performance - away performance when at home)
        home_performance = home_goals - home_expected if home_expected > 0 else 0
        
        # Weight by opponent and update gradually
        weighted_advantage = home_performance * opponent_factor * 0.05
        current = self.team_metrics[team]['home_advantage']
        self.team_metrics[team]['home_advantage'] = current * 0.95 + (1.0 + weighted_advantage) * 0.05
        
    def update_form(self, team: str, goals_for: int, goals_against: int, opponent_elo: float, 
                   is_home: bool, league_avg: float = 1500):
        """Update form based on recent match performance weighted by opponent strength"""
        opponent_factor = self.get_opponent_strength_factor(opponent_elo, league_avg)
        
        # Match performance score
        goal_diff = goals_for - goals_against
        if goal_diff > 0:
            match_score = 1.5 + (goal_diff - 1) * 0.3  # Win + goal margin bonus
        elif goal_diff == 0:
            match_score = 0.8  # Draw
        else:
            match_score = 0.2 + max(-0.1, goal_diff * 0.1)  # Loss with margin penalty
            
        # Weight by opponent strength
        weighted_score = match_score * opponent_factor
        
        # Add to recent matches
        metrics = self.team_metrics[team]
        metrics['recent_matches'].append({
            'score': weighted_score,
            'date': datetime.now(),
            'opponent_elo': opponent_elo,
            'goals_for': goals_for,
            'goals_against': goals_against
        })
        
        # Calculate weighted form (recent matches matter more)
        if metrics['recent_matches']:
            total_weight = 0
            total_score = 0
            for i, match in enumerate(metrics['recent_matches']):
                # More recent matches get higher weight
                weight = (i + 1) / len(metrics['recent_matches'])
                total_weight += weight
                total_score += match['score'] * weight
                
            metrics['form'] = total_score / total_weight if total_weight > 0 else 0
        
    def get_team_characteristics(self, team: str) -> Dict[str, float]:
        """Get current dynamic characteristics for a team"""
        metrics = self.team_metrics[team]
        return {
            'attacking_home': metrics['attacking_performance']['home'],
            'attacking_away': metrics['attacking_performance']['away'],
            'attacking_overall': metrics['attacking_performance']['overall'],
            'defensive_home': metrics['defensive_strength']['home'],
            'defensive_away': metrics['defensive_strength']['away'],
            'defensive_overall': metrics['defensive_strength']['overall'],
            'home_advantage': metrics['home_advantage'],
            'form': metrics['form'],
            'consistency': metrics['consistency']
        }


class EnhancedEstonianPredictor:
    """Enhanced Estonian Football Predictor with dynamic performance tracking"""
    
    def __init__(self, root=None):
        """Initialize the Enhanced Estonian Predictor"""
        # Initialize dynamic performance tracker
        self.performance_tracker = DynamicPerformanceTracker()
        
        if root:
            self.root = root
            self.root.title("Enhanced Estonian Football Predictor")
            self.root.geometry("1000x800")
            
        # Initialize data structures
        self.elo_ratings = {}
        self.teams = []
        self.team_characteristics = defaultdict(lambda: {
            'attacking_style': 1.0,    # How attacking vs defensive
            'home_advantage': 1.1,      # Home field advantage
            'form': 0.0,               # Recent form (-1 to +1)
            'consistency': 1.0,        # How consistent results are
            'recent_matches': deque(maxlen=6)  # Last 6 matches for form
        })
        
        # Enhanced model parameters
        self.draw_calibration = 0.25    # Calibration for draws (more realistic)
        self.time_decay_factor = 0.95   # Time decay for ratings
        self.season_regression = 0.25   # Regression to league mean
        self.k_factor = 32              # ELO K-factor
        
        if root:
            self.setup_gui()
        
        # Always load ELO data regardless of GUI
        self.load_elo_data()
        
        # Auto-initialize dynamic characteristics for all teams
        self.initialize_dynamic_characteristics()
            
    def load_elo_data(self):
        """Load ELO ratings by processing actual 2025 match results"""
        try:
            print("🏆 PROCESSING ACTUAL 2025 MATCH RESULTS FOR REALISTIC ELO RATINGS")
            
            # Initialize all teams with baseline ELO ratings based on league
            esiliiga_teams = {
                'FC Nomme United', 'Viimsi JK', 'Tartu JK Welco', 'FC Tallinn', 'FC Elva',
                'Kalju FC U21', 'FCI Levadia U21', 'Kalev Tallinn U21', 
                'Jalgpallikool Tammeka U21', 'FC Flora Tallinn U21'
            }
            
            esiliiga_b_teams = {
                'Johvi Phoenix', 'JK Tabasalu', 'FA Tartu Kalev', 'TJK Legion', 'Läänemaa JK',
                'Trans Narva U21', 'FC Nomme U21', 'Paide U21', 'Kuressaare U21', 'Maardu LM'
            }
            
            # Start with baseline ratings
            for team in esiliiga_teams:
                self.elo_ratings[team] = 1550  # Esiliiga baseline
            for team in esiliiga_b_teams:
                self.elo_ratings[team] = 1450  # Esiliiga B baseline
            
            # Process actual match results from 2025 season
            matches_processed = 0
            
            # Process Esiliiga 2025 results
            try:
                print("  📁 Processing esiliiga2025.csv...")
                esiliiga_df = pd.read_csv('esiliiga2025.csv')
                matches_processed += self._process_match_results(esiliiga_df, "Esiliiga")
            except Exception as e:
                print(f"  ⚠️ Error reading esiliiga2025.csv: {e}")
            
            # Process Esiliiga B 2025 results
            try:
                print("  📁 Processing esiliigab2025.csv...")
                esiliiga_b_df = pd.read_csv('esiliigab2025.csv')
                matches_processed += self._process_match_results(esiliiga_b_df, "Esiliiga B")
            except Exception as e:
                print(f"  ⚠️ Error reading esiliigab2025.csv: {e}")
            
            self.teams = list(self.elo_ratings.keys())
            print(f"✅ Processed {matches_processed} actual matches for realistic ELO ratings")
            print(f"📊 Loaded {len(self.teams)} teams with performance-based ELO ratings")
            
        except Exception as e:
            print(f"❌ Error processing match results: {e}")
            # Fallback to baseline ratings
            self._load_baseline_ratings()
    
    def _process_match_results(self, df, league_name):
        """Process match results and update ELO ratings"""
        matches_processed = 0
        
        for _, row in df.iterrows():
            try:
                home_team = str(row.get('Home', '')).strip()
                away_team = str(row.get('Away', '')).strip()
                result = str(row.get('Result', '')).strip()
                
                # Skip invalid rows
                if not home_team or not away_team or not result or result == 'nan':
                    continue
                
                # Parse score (format: "1:2" or "2:0")
                if ':' not in result:
                    continue
                    
                try:
                    home_goals, away_goals = map(int, result.split(':'))
                except:
                    continue
                
                # Update ELO ratings based on match result
                self._update_elo_ratings(home_team, away_team, home_goals, away_goals)
                matches_processed += 1
                
            except Exception as e:
                continue
        
        print(f"    ✅ {league_name}: {matches_processed} matches processed")
        return matches_processed
    
    def _update_elo_ratings(self, home_team, away_team, home_goals, away_goals):
        """Update ELO ratings based on match result"""
        # Get current ratings
        home_elo = self.elo_ratings.get(home_team, 1500)
        away_elo = self.elo_ratings.get(away_team, 1500)
        
        # Calculate expected scores
        home_expected = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        away_expected = 1 - home_expected
        
        # Determine actual scores
        if home_goals > away_goals:
            home_actual, away_actual = 1, 0  # Home win
        elif away_goals > home_goals:
            home_actual, away_actual = 0, 1  # Away win
        else:
            home_actual, away_actual = 0.5, 0.5  # Draw
        
        # Calculate ELO changes (K-factor = 32)
        k_factor = 32
        home_change = k_factor * (home_actual - home_expected)
        away_change = k_factor * (away_actual - away_expected)
        
        # Update ratings
        self.elo_ratings[home_team] = home_elo + home_change
        self.elo_ratings[away_team] = away_elo + away_change
    
    def _load_baseline_ratings(self):
        """Fallback: Load baseline ratings if match processing fails"""
        print("⚠️ Falling back to baseline ELO ratings")
        
        esiliiga_teams = {
            'FC Nomme United', 'Viimsi JK', 'Tartu JK Welco', 'FC Tallinn', 'FC Elva',
            'Kalju FC U21', 'FCI Levadia U21', 'Kalev Tallinn U21', 
            'Jalgpallikool Tammeka U21', 'FC Flora Tallinn U21'
        }
        
        esiliiga_b_teams = {
            'Johvi Phoenix', 'JK Tabasalu', 'FA Tartu Kalev', 'TJK Legion', 'Läänemaa JK',
            'Trans Narva U21', 'FC Nomme U21', 'Paide U21', 'Kuressaare U21', 'Maardu LM'
        }
        
        for team in esiliiga_teams:
            self.elo_ratings[team] = 1550
        for team in esiliiga_b_teams:
            self.elo_ratings[team] = 1450
            
        self.teams = list(self.elo_ratings.keys())
    
    def initialize_dynamic_characteristics(self):
        """Initialize all teams with realistic dynamic characteristics"""
        print("🔧 Initializing dynamic characteristics...")
        
        # Estonian league classifications
        esiliiga_teams = [
            'Maardu LM', 'FC Nomme United', 'Viimsi JK', 'Tartu JK Welco',
            'FC Tallinn', 'FC Elva', 'Johvi Phoenix', 'JK Tabasalu',
            'FA Tartu Kalev', 'TJK Legion', 'Läänemaa JK'
        ]
        
        # Initialize characteristics for ALL teams
        for team in self.teams:
            # Get team's league and ELO
            elo = self.elo_ratings.get(team, 1500)
            is_senior_team = team in esiliiga_teams
            
            # Base performance calculation
            if is_senior_team:
                base_performance = (elo - 1500) / 250
                variance_multiplier = 1.2
            else:
                # U21 teams: generally weaker, more variance
                base_performance = (elo - 1450) / 300
                variance_multiplier = 1.8
            
            # Create realistic characteristics with significant variance
            home_attack = max(0.5, min(1.8, 1.0 + random.gauss(base_performance * 0.2, 0.2 * variance_multiplier)))
            away_attack = max(0.5, min(1.8, 1.0 + random.gauss(base_performance * 0.15, 0.18 * variance_multiplier)))
            home_defense = max(0.5, min(1.8, 1.0 + random.gauss(base_performance * 0.18, 0.16 * variance_multiplier)))
            away_defense = max(0.5, min(1.8, 1.0 + random.gauss(base_performance * 0.12, 0.15 * variance_multiplier)))
            home_advantage = max(0.8, min(1.4, 1.0 + random.gauss(0.1, 0.12 * variance_multiplier)))
            form = random.gauss(base_performance * 0.3, 0.5 * variance_multiplier)
            consistency = max(0.6, min(1.5, random.uniform(0.7, 1.4) * (1 + base_performance * 0.1)))
            
            # Force create the team entry
            self.performance_tracker.team_metrics[team] = {
                'attacking_performance': {
                    'home': home_attack,
                    'away': away_attack,
                    'overall': (home_attack + away_attack) / 2
                },
                'defensive_strength': {
                    'home': home_defense,
                    'away': away_defense,
                    'overall': (home_defense + away_defense) / 2
                },
                'home_advantage': home_advantage,
                'form': form,
                'consistency': consistency,
                'recent_matches': deque(maxlen=10),
                'goals_for_trend': deque(maxlen=10),
                'goals_against_trend': deque(maxlen=10),
                'expected_performance': 1.0,
                'opponent_strength_sum': 0.0,
                'matches_played': 0
            }
        
        print(f"✅ Initialized dynamic characteristics for {len(self.teams)} teams")
            
    def calculate_expected_goals(self, home_team: str, away_team: str) -> Tuple[float, float]:
        """Calculate expected goals using team characteristics and ELO"""
        home_elo = self.elo_ratings.get(home_team, 1500)
        away_elo = self.elo_ratings.get(away_team, 1500)
        
        # Get dynamic characteristics
        home_chars = self.performance_tracker.get_team_characteristics(home_team)
        away_chars = self.performance_tracker.get_team_characteristics(away_team)
        
        # Base expected goals from ELO difference
        elo_diff = home_elo - away_elo
        base_home_goals = 1.3 + (elo_diff / 400) * 0.5
        base_away_goals = 1.1 - (elo_diff / 400) * 0.3
        
        # Apply dynamic characteristics
        home_attacking = home_chars.get('attacking_home', 1.0)
        home_defensive = home_chars.get('defensive_home', 1.0)
        home_advantage = home_chars.get('home_advantage', 1.1)
        home_form = home_chars.get('form', 0.0)
        
        away_attacking = away_chars.get('attacking_away', 1.0)
        away_defensive = away_chars.get('defensive_away', 1.0)
        away_form = away_chars.get('form', 0.0)
        
        # Calculate final expected goals with bounded defensive values
        # Ensure defensive values are reasonable (0.5 to 2.0 range)
        home_defensive_bounded = max(0.5, min(2.0, home_defensive))
        away_defensive_bounded = max(0.5, min(2.0, away_defensive))
        
        # Home goals = home attack * home advantage * home form, reduced by away defense
        home_expected = base_home_goals * home_attacking * home_advantage * (1 + home_form * 0.1) / away_defensive_bounded
        # Away goals = away attack * away form, reduced by home defense  
        away_expected = base_away_goals * away_attacking * (1 + away_form * 0.1) / home_defensive_bounded
        
        return max(0.1, home_expected), max(0.1, away_expected)
        
    def enhanced_match_probability(self, home_team: str, away_team: str) -> Tuple[float, float, float]:
        """
        Enhanced probability model with draw calibration
        Returns: (home_win_prob, draw_prob, away_win_prob)
        """
        home_elo = self.elo_ratings.get(home_team, 1500)
        away_elo = self.elo_ratings.get(away_team, 1500)
        
        # Get dynamic characteristics
        home_chars = self.performance_tracker.get_team_characteristics(home_team)
        away_chars = self.performance_tracker.get_team_characteristics(away_team)
        
        # Base ELO probability
        elo_diff = home_elo - away_elo
        
        # Apply dynamic factors
        home_advantage = home_chars.get('home_advantage', 1.1)
        home_form = home_chars.get('form', 0.0)
        away_form = away_chars.get('form', 0.0)
        
        # Adjust ELO difference with dynamic factors
        adjusted_diff = elo_diff + (home_advantage - 1) * 100 + (home_form - away_form) * 50
        
        # Calculate probabilities using logistic model
        home_prob_raw = 1 / (1 + 10 ** (-adjusted_diff / 400))
        
        # Apply draw calibration
        draw_factor = self.draw_calibration
        
        # Redistribute probabilities
        home_win = home_prob_raw * (1 - draw_factor)
        away_win = (1 - home_prob_raw) * (1 - draw_factor) 
        draw = draw_factor
        
        # Normalize to ensure they sum to 1
        total = home_win + draw + away_win
        return home_win/total, draw/total, away_win/total
        
    def poisson_goals(self, expected_goals: float) -> int:
        """Generate goals using Poisson distribution"""
        return np.random.poisson(expected_goals)
        
    def simulate_match_with_scoreline(self, home_team: str, away_team: str, update_dynamics: bool = False) -> Tuple[int, int, str]:
        """
        Simulate a match and return the scoreline
        Returns: (home_goals, away_goals, result)
        update_dynamics: Whether to update team characteristics (False for simulations, True for real matches)
        """
        home_expected, away_expected = self.calculate_expected_goals(home_team, away_team)
        
        # Generate goals using Poisson distribution
        home_goals = self.poisson_goals(home_expected)
        away_goals = self.poisson_goals(away_expected)
        
        # Determine result
        if home_goals > away_goals:
            result = 'H'
        elif away_goals > home_goals:
            result = 'A'
        else:
            result = 'D'
            
        # Only update dynamic performance metrics if requested (for real matches, not simulations)
        if update_dynamics:
            home_elo = self.elo_ratings.get(home_team, 1500)
            away_elo = self.elo_ratings.get(away_team, 1500)
            
            self.performance_tracker.update_attacking_performance(
                home_team, home_goals, home_expected, away_elo, True
            )
            self.performance_tracker.update_attacking_performance(
                away_team, away_goals, away_expected, home_elo, False
            )
            
            self.performance_tracker.update_defensive_strength(
                home_team, away_goals, away_expected, away_elo, True
            )
            self.performance_tracker.update_defensive_strength(
                away_team, home_goals, home_expected, home_elo, False
            )
            
            self.performance_tracker.update_form(
                home_team, home_goals, away_goals, away_elo, True
            )
            self.performance_tracker.update_form(
                away_team, away_goals, home_goals, home_elo, False
            )
            
            self.performance_tracker.update_home_advantage(
                home_team, home_goals, away_goals, home_expected, away_expected, away_elo
            )
            
        return home_goals, away_goals, result
        
    def update_elo_ratings(self, home_team: str, away_team: str, result: str, 
                          home_goals: int = None, away_goals: int = None):
        """Update ELO ratings with season regression"""
        home_elo = self.elo_ratings.get(home_team, 1500)
        away_elo = self.elo_ratings.get(away_team, 1500)
        
        # Calculate expected score
        expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        
        # Determine actual score
        if result == 'H':
            actual_home = 1.0
        elif result == 'A':
            actual_home = 0.0
        else:
            actual_home = 0.5
            
        # Calculate rating changes
        home_change = self.k_factor * (actual_home - expected_home)
        away_change = -home_change
        
        # Apply changes
        new_home_elo = home_elo + home_change
        new_away_elo = away_elo + away_change
        
        # Apply season regression (move towards league mean)
        league_mean = 1550  # Slightly above default
        new_home_elo = new_home_elo * (1 - self.season_regression) + league_mean * self.season_regression
        new_away_elo = new_away_elo * (1 - self.season_regression) + league_mean * self.season_regression
        
        self.elo_ratings[home_team] = new_home_elo
        self.elo_ratings[away_team] = new_away_elo
        
    def setup_gui(self):
        """Setup the enhanced GUI"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Enhanced Estonian Football Predictor", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Team selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Match Prediction", padding="10")
        selection_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Home team selection
        ttk.Label(selection_frame, text="Home Team:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.home_team_var = tk.StringVar()
        self.home_team_combo = ttk.Combobox(selection_frame, textvariable=self.home_team_var, 
                                          width=25, state="readonly")
        self.home_team_combo.grid(row=0, column=1, padx=(0, 20))
        
        # Away team selection
        ttk.Label(selection_frame, text="Away Team:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.away_team_var = tk.StringVar()
        self.away_team_combo = ttk.Combobox(selection_frame, textvariable=self.away_team_var, 
                                          width=25, state="readonly")
        self.away_team_combo.grid(row=0, column=3)
        
        # Predict button
        predict_btn = ttk.Button(selection_frame, text="Predict Match", 
                               command=self.predict_match, style="Accent.TButton")
        predict_btn.grid(row=0, column=4, padx=(20, 0))
        
        # Simulation controls
        sim_frame = ttk.LabelFrame(main_frame, text="Monte Carlo Simulation", padding="10")
        sim_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Number of simulations
        ttk.Label(sim_frame, text="Simulations:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.sim_count_var = tk.StringVar(value="1000")
        sim_count_entry = ttk.Entry(sim_frame, textvariable=self.sim_count_var, width=10)
        sim_count_entry.grid(row=0, column=1, padx=(0, 20))
        
        # Simulate button
        simulate_btn = ttk.Button(sim_frame, text="Run Simulation", 
                                command=self.run_simulation, style="Accent.TButton")
        simulate_btn.grid(row=0, column=2)
        
        # Results area
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Results text widget
        self.results_text = scrolledtext.ScrolledText(results_frame, height=20, width=80)
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Update team lists when teams are loaded
        self.root.after(100, self.update_team_lists)
        
    def update_team_lists(self):
        """Update the team dropdown lists"""
        if self.teams:
            sorted_teams = sorted(self.teams)
            self.home_team_combo['values'] = sorted_teams
            self.away_team_combo['values'] = sorted_teams
            
    def predict_match(self):
        """Predict a single match with enhanced analysis"""
        home_team = self.home_team_var.get()
        away_team = self.away_team_var.get()
        
        if not home_team or not away_team:
            messagebox.showwarning("Warning", "Please select both teams")
            return
            
        if home_team == away_team:
            messagebox.showwarning("Warning", "Please select different teams")
            return
            
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        # Get ELO ratings
        home_elo = self.elo_ratings.get(home_team, 1500)
        away_elo = self.elo_ratings.get(away_team, 1500)
        
        # Get dynamic characteristics
        home_chars = self.performance_tracker.get_team_characteristics(home_team)
        away_chars = self.performance_tracker.get_team_characteristics(away_team)
        
        # Calculate probabilities and expected goals
        home_prob, draw_prob, away_prob = self.enhanced_match_probability(home_team, away_team)
        home_expected, away_expected = self.calculate_expected_goals(home_team, away_team)
        
        # Display results
        result_text = f"""🏆 ENHANCED MATCH PREDICTION 🏆

📅 Match: {home_team} vs {away_team}

⚡ ELO RATINGS:
   🏠 {home_team}: {home_elo:.0f}
   ✈️  {away_team}: {away_elo:.0f}
   📊 Rating Difference: {home_elo - away_elo:+.0f}

🎯 MATCH PROBABILITIES:
   🏠 {home_team} Win: {home_prob:.1%}
   🤝 Draw: {draw_prob:.1%}
   ✈️  {away_team} Win: {away_prob:.1%}

⚽ EXPECTED GOALS:
   🏠 {home_team}: {home_expected:.2f}
   ✈️  {away_team}: {away_expected:.2f}

📈 DYNAMIC CHARACTERISTICS:

🏠 {home_team}:
   🏡 Home Advantage: {home_chars.get('home_advantage', 1.1):.2f}
   ⚔️  Attacking (Home): {home_chars.get('attacking_home', 1.0):.2f}
   🛡️  Defensive (Home): {home_chars.get('defensive_home', 1.0):.2f}
   📊 Current Form: {home_chars.get('form', 0.0):+.2f}

✈️  {away_team}:
   ⚔️  Attacking (Away): {away_chars.get('attacking_away', 1.0):.2f}
   🛡️  Defensive (Away): {away_chars.get('defensive_away', 1.0):.2f}
   📊 Current Form: {away_chars.get('form', 0.0):+.2f}

💡 PREDICTION INSIGHT:
"""
        
        # Add prediction insight
        if home_prob > 0.5:
            result_text += f"   Strong home advantage for {home_team}\n"
        elif away_prob > 0.5:
            result_text += f"   {away_team} favored despite playing away\n"
        else:
            result_text += f"   Very close match, slight edge to {'home' if home_prob > away_prob else 'away'} team\n"
            
        # Add goal expectation insight
        total_goals = home_expected + away_expected
        if total_goals > 2.8:
            result_text += f"   High-scoring match expected ({total_goals:.1f} total goals)\n"
        elif total_goals < 2.2:
            result_text += f"   Low-scoring match expected ({total_goals:.1f} total goals)\n"
        else:
            result_text += f"   Moderate scoring expected ({total_goals:.1f} total goals)\n"
            
        self.results_text.insert(tk.END, result_text)
        
    def run_simulation(self):
        """Run Monte Carlo simulation with enhanced features"""
        home_team = self.home_team_var.get()
        away_team = self.away_team_var.get()
        
        if not home_team or not away_team:
            messagebox.showwarning("Warning", "Please select both teams")
            return
            
        if home_team == away_team:
            messagebox.showwarning("Warning", "Please select different teams")
            return
            
        try:
            num_sims = int(self.sim_count_var.get())
            if num_sims <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of simulations")
            return
            
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"🎲 Running {num_sims:,} Monte Carlo simulations...\n\n")
        self.root.update()
        
        # Run simulations
        results = {'H': 0, 'D': 0, 'A': 0}
        scorelines = defaultdict(int)
        home_goals_total = 0
        away_goals_total = 0
        
        for _ in range(num_sims):
            home_goals, away_goals, result = self.simulate_match_with_scoreline(home_team, away_team)
            results[result] += 1
            scorelines[f"{home_goals}-{away_goals}"] += 1
            home_goals_total += home_goals
            away_goals_total += away_goals
            
        # Calculate statistics
        home_win_pct = results['H'] / num_sims * 100
        draw_pct = results['D'] / num_sims * 100
        away_win_pct = results['A'] / num_sims * 100
        
        avg_home_goals = home_goals_total / num_sims
        avg_away_goals = away_goals_total / num_sims
        
        # Get most common scorelines
        top_scorelines = sorted(scorelines.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Display enhanced results
        result_text = f"""🎲 MONTE CARLO SIMULATION RESULTS 🎲
({num_sims:,} simulations)

📊 OUTCOME PROBABILITIES:
   🏠 {home_team} Win: {home_win_pct:.1f}% ({results['H']:,} times)
   🤝 Draw: {draw_pct:.1f}% ({results['D']:,} times)  
   ✈️  {away_team} Win: {away_win_pct:.1f}% ({results['A']:,} times)

⚽ AVERAGE GOALS:
   🏠 {home_team}: {avg_home_goals:.2f} goals per game
   ✈️  {away_team}: {avg_away_goals:.2f} goals per game
   📈 Total: {avg_home_goals + avg_away_goals:.2f} goals per game

🎯 MOST LIKELY SCORELINES:
"""
        
        for i, (scoreline, count) in enumerate(top_scorelines):
            percentage = count / num_sims * 100
            result_text += f"   {i+1:2d}. {scoreline}: {percentage:.1f}% ({count:,} times)\n"
            
        # Add betting odds equivalent
        result_text += f"\n💰 IMPLIED BETTING ODDS:\n"
        if home_win_pct > 0:
            result_text += f"   🏠 {home_team}: {100/home_win_pct:.2f}\n"
        if draw_pct > 0:
            result_text += f"   🤝 Draw: {100/draw_pct:.2f}\n"
        if away_win_pct > 0:
            result_text += f"   ✈️  {away_team}: {100/away_win_pct:.2f}\n"
            
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, result_text)


def main():
    """Run the Enhanced Estonian Predictor"""
    root = tk.Tk()
    
    # Set up modern styling
    style = ttk.Style()
    style.theme_use('clam')
    
    app = EnhancedEstonianPredictor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
