#!/usr/bin/env python3
"""
Enhanced Estonian Football Time Machine
- League-specific season simulation
- Historical match simulation with date selection
- Time-based team analysis
- Improved user interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from collections import defaultdict, deque
import random
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# Add the core directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

try:
    from enhanced_estonian_predictor_fixed import EnhancedEstonianPredictor
    predictor_available = True
except ImportError:
    print("Warning: Enhanced predictor not available")
    predictor_available = False


class EstonianLeagueSystem:
    """Estonian league system helper"""
    
    ESILIIGA_TEAMS = [
        "FC Elva", "FC Flora Tallinn U21", "FC Nomme United", "FC Tallinn",
        "FCI Levadia U21", "Jalgpallikool Tammeka U21", "Kalev Tallinn U21",
        "Kalju FC U21", "Tartu JK Welco", "Viimsi JK"
    ]
    
    ESILIIGA_B_TEAMS = [
        "FA Tartu Kalev", "FA Tartu Kalev  (5.)", "FC Nomme U21", "JK Tabasalu",
        "Johvi Phoenix", "Kuressaare U21", "Kuressaare U21  (10.)", "Läänemaa JK",
        "Maardu LM", "Paide U21", "TJK Legion", "Trans Narva U21"
    ]
    
    @classmethod
    def get_team_league(cls, team_name: str) -> str:
        """Get league for team"""
        if team_name in cls.ESILIIGA_TEAMS:
            return "Esiliiga"
        elif team_name in cls.ESILIIGA_B_TEAMS:
            return "Esiliiga B"
        else:
            return "Unknown"


class TimeBasedTeamTracker:
    """Track team characteristics over time"""
    
    def __init__(self):
        self.team_history = defaultdict(list)  # {team: [(date, elo, characteristics), ...]}
        
    def record_team_state(self, team: str, date: str, elo: float, characteristics: dict):
        """Record team state at a specific date"""
        self.team_history[team].append({
            'date': date,
            'elo': elo,
            'characteristics': characteristics.copy()
        })
        
    def get_team_at_date(self, team: str, target_date: str):
        """Get team characteristics closest to target date"""
        if team not in self.team_history or not self.team_history[team]:
            return None
            
        # Find closest date
        target = datetime.strptime(target_date, '%Y-%m-%d')
        closest_record = None
        min_diff = float('inf')
        
        for record in self.team_history[team]:
            record_date = datetime.strptime(record['date'], '%Y-%m-%d')
            diff = abs((target - record_date).days)
            if diff < min_diff:
                min_diff = diff
                closest_record = record
                
        return closest_record


class EnhancedTeamAnalysisSystem:
    """Enhanced team analysis with league-specific statistics"""
    
    def __init__(self):
        self.team_stats = defaultdict(lambda: {
            'league_wins': 0,
            'promotions': 0,
            'promotion_playoffs': 0,
            'relegations': 0,
            'relegation_playoffs': 0,
            'best_points': 0,
            'worst_points': 999,
            'simulations_run': 0,
            'league': 'Unknown'
        })
    
    def analyze_team_season(self, team: str, final_position: int, points: int, 
                          goal_difference: int, league_size: int, league: str = "Unknown"):
        """Analyze team season with league context"""
        stats = self.team_stats[team]
        stats['simulations_run'] += 1
        stats['league'] = league
        
        # Fix worst_points initialization
        if stats['simulations_run'] == 1:
            stats['worst_points'] = points
        
        stats['best_points'] = max(stats['best_points'], points)
        stats['worst_points'] = min(stats['worst_points'], points)
        
        # League-specific analysis
        if league == "Esiliiga":
            if final_position == 1:
                stats['league_wins'] += 1
            elif final_position <= 2:
                stats['promotions'] += 1  # Top 2 to higher league
        elif league == "Esiliiga B":
            if final_position == 1:
                stats['league_wins'] += 1
            elif final_position <= 2:
                stats['promotions'] += 1  # Top 2 to Esiliiga
            elif final_position >= league_size - 1:
                stats['relegations'] += 1  # Bottom 2 relegated
    
    def get_team_analysis(self, team: str) -> dict:
        """Get comprehensive team analysis"""
        stats = self.team_stats[team]
        if stats['simulations_run'] == 0:
            return {
                'league_win_rate': 0.0,
                'promotion_rate': 0.0,
                'relegation_rate': 0.0,
                'avg_points': 0,
                'points_range': "No data"
            }
        
        return {
            'league_win_rate': (stats['league_wins'] / stats['simulations_run']) * 100,
            'promotion_rate': (stats['promotions'] / stats['simulations_run']) * 100,
            'relegation_rate': (stats['relegations'] / stats['simulations_run']) * 100,
            'avg_points': (stats['best_points'] + stats['worst_points']) / 2,
            'points_range': f"{stats['worst_points']}-{stats['best_points']}"
        }


class EnhancedEstonianFootballTimeMachine:
    """Enhanced Estonian Football Time Machine with advanced features"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Enhanced Estonian Football Time Machine")
        self.root.geometry("1600x1000")
        
        # Initialize systems
        self.team_analysis = EnhancedTeamAnalysisSystem()
        self.time_tracker = TimeBasedTeamTracker()
        self.elo_ratings = {}
        self.teams = []
        
        # Load enhanced predictor
        if EnhancedEstonianPredictor:
            try:
                self.enhanced_predictor = EnhancedEstonianPredictor()
                self.elo_ratings = self.enhanced_predictor.elo_ratings
                self.teams = list(self.elo_ratings.keys())
                print("✅ Enhanced predictor loaded")
                self._initialize_time_data()
            except Exception as e:
                print(f"❌ Error loading predictor: {e}")
                self.enhanced_predictor = None
        else:
            self.enhanced_predictor = None
            
        self.setup_gui()
        
    def _initialize_time_data(self):
        """Initialize time-based data for historical simulation"""
        # Create sample time points (in real app, this would come from match data)
        base_date = datetime(2025, 3, 1)
        
        for i, team in enumerate(self.teams):
            base_elo = self.elo_ratings[team]
            
            # Get initial characteristics if available
            if self.enhanced_predictor and hasattr(self.enhanced_predictor, 'performance_tracker'):
                base_chars = self.enhanced_predictor.performance_tracker.get_team_characteristics(team)
            else:
                base_chars = {
                    'attacking_overall': 0.8 + random.random() * 0.4,
                    'defensive_overall': 0.8 + random.random() * 0.4,
                    'form': random.gauss(0, 0.2)
                }
            
            for week in range(0, 30, 2):  # Every 2 weeks
                date = base_date + timedelta(weeks=week)
                date_str = date.strftime('%Y-%m-%d')
                
                # Simulate ELO evolution with more realistic variation
                elo_drift = random.gauss(0, week * 1.5)  # Gradual drift over time
                historical_elo = max(1200, min(1800, base_elo + elo_drift))
                
                # Create varying characteristics over time
                time_factor = week / 30.0  # 0 to 1 progression
                
                # Attack characteristics evolve
                attack_trend = random.gauss(0, 0.1)  # Random trend
                attack_noise = random.gauss(0, 0.05)  # Weekly noise
                attacking = max(0.5, min(1.5, base_chars['attacking_overall'] + 
                               (time_factor * attack_trend) + attack_noise))
                
                # Defense characteristics evolve  
                defense_trend = random.gauss(0, 0.1)
                defense_noise = random.gauss(0, 0.05)
                defensive = max(0.5, min(1.5, base_chars['defensive_overall'] + 
                               (time_factor * defense_trend) + defense_noise))
                
                # Form varies more dramatically
                form_change = random.gauss(0, 0.3)  # Form can change quickly
                form = max(-1.0, min(1.0, base_chars['form'] + form_change))
                
                chars = {
                    'attacking_overall': attacking,
                    'defensive_overall': defensive,
                    'form': form,
                    'home_advantage': base_chars.get('home_advantage', 1.0) + random.gauss(0, 0.02),
                    'consistency': base_chars.get('consistency', 1.0) + random.gauss(0, 0.05)
                }
                
                self.time_tracker.record_team_state(team, date_str, historical_elo, chars)
    
    def setup_gui(self):
        """Setup the enhanced GUI"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create enhanced tabs
        self.create_enhanced_match_tab()
        self.create_league_simulation_tab()
        self.create_historical_analysis_tab()
        self.create_team_analysis_tab()
    
    def create_enhanced_match_tab(self):
        """Enhanced match prediction with historical simulation"""
        match_frame = ttk.Frame(self.notebook)
        self.notebook.add(match_frame, text="Enhanced Match Simulation")
        
        # Team selection
        selection_frame = ttk.LabelFrame(match_frame, text="Match Setup", padding="10")
        selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Team dropdowns
        ttk.Label(selection_frame, text="Home Team:").grid(row=0, column=0, sticky=tk.W)
        self.home_team_var = tk.StringVar()
        home_combo = ttk.Combobox(selection_frame, textvariable=self.home_team_var,
                                values=self.teams, state="readonly", width=25)
        home_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(selection_frame, text="Away Team:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.away_team_var = tk.StringVar()
        away_combo = ttk.Combobox(selection_frame, textvariable=self.away_team_var,
                                values=self.teams, state="readonly", width=25)
        away_combo.grid(row=0, column=3, padx=5)
        
        # Date selection for historical simulation
        ttk.Label(selection_frame, text="Home Team Date:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.home_date_var = tk.StringVar(value="2025-08-29")
        home_date_entry = ttk.Entry(selection_frame, textvariable=self.home_date_var, width=15)
        home_date_entry.grid(row=1, column=1, padx=5, pady=(10, 0))
        
        ttk.Label(selection_frame, text="Away Team Date:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=(10, 0))
        self.away_date_var = tk.StringVar(value="2025-08-29")
        away_date_entry = ttk.Entry(selection_frame, textvariable=self.away_date_var, width=15)
        away_date_entry.grid(row=1, column=3, padx=5, pady=(10, 0))
        
        ttk.Label(selection_frame, text="(YYYY-MM-DD format for both dates)").grid(row=2, column=0, columnspan=4, pady=(5, 0))
        
        # Simulation buttons
        button_frame = ttk.Frame(selection_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=10)
        
        ttk.Button(button_frame, text="Simulate Current", 
                  command=self.simulate_current_match).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Simulate Historical", 
                  command=self.simulate_historical_match).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Compare Dates", 
                  command=self.compare_dates).pack(side=tk.LEFT, padx=5)
        
        # Results area
        results_frame = ttk.LabelFrame(match_frame, text="Simulation Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.match_results = scrolledtext.ScrolledText(results_frame, height=25, width=100)
        self.match_results.pack(fill=tk.BOTH, expand=True)
    
    def create_league_simulation_tab(self):
        """Enhanced league simulation with league selection"""
        season_frame = ttk.Frame(self.notebook)
        self.notebook.add(season_frame, text="League Simulation")
        
        # Controls
        controls_frame = ttk.LabelFrame(season_frame, text="Simulation Controls", padding="10")
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # League selection
        ttk.Label(controls_frame, text="League to Simulate:").grid(row=0, column=0, sticky=tk.W)
        self.league_selection_var = tk.StringVar(value="Both Leagues")
        league_combo = ttk.Combobox(controls_frame, textvariable=self.league_selection_var,
                                  values=["Esiliiga Only", "Esiliiga B Only", "Both Leagues"],
                                  state="readonly", width=20)
        league_combo.grid(row=0, column=1, padx=5)
        
        # Season count
        ttk.Label(controls_frame, text="Seasons:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.season_count_var = tk.StringVar(value="100")
        season_entry = ttk.Entry(controls_frame, textvariable=self.season_count_var, width=10)
        season_entry.grid(row=0, column=3, padx=5)
        
        # Simulation button
        ttk.Button(controls_frame, text="Run Simulation", 
                  command=self.run_enhanced_simulation).grid(row=0, column=4, padx=20)
        
        # Results
        results_frame = ttk.LabelFrame(season_frame, text="Simulation Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.season_results = scrolledtext.ScrolledText(results_frame, height=30, width=120)
        self.season_results.pack(fill=tk.BOTH, expand=True)
    
    def create_historical_analysis_tab(self):
        """Historical analysis and trends"""
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="Historical Analysis")
        
        # Team and date selection
        controls_frame = ttk.LabelFrame(history_frame, text="Analysis Controls", padding="10")
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(controls_frame, text="Team:").grid(row=0, column=0, sticky=tk.W)
        self.history_team_var = tk.StringVar()
        team_combo = ttk.Combobox(controls_frame, textvariable=self.history_team_var,
                                values=self.teams, state="readonly", width=25)
        team_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(controls_frame, text="Date Range:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.start_date_var = tk.StringVar(value="2025-03-01")
        start_entry = ttk.Entry(controls_frame, textvariable=self.start_date_var, width=12)
        start_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(controls_frame, text="to").grid(row=0, column=4)
        self.end_date_var = tk.StringVar(value="2025-08-29")
        end_entry = ttk.Entry(controls_frame, textvariable=self.end_date_var, width=12)
        end_entry.grid(row=0, column=5, padx=5)
        
        ttk.Button(controls_frame, text="Analyze", 
                  command=self.analyze_historical_performance).grid(row=0, column=6, padx=20)
        
        # Results
        results_frame = ttk.LabelFrame(history_frame, text="Historical Analysis", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.history_results = scrolledtext.ScrolledText(results_frame, height=30, width=120)
        self.history_results.pack(fill=tk.BOTH, expand=True)
    
    def create_team_analysis_tab(self):
        """Enhanced team analysis"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Team Analysis")
        
        # Team selection
        selection_frame = ttk.LabelFrame(analysis_frame, text="Team Selection", padding="10")
        selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(selection_frame, text="Team:").grid(row=0, column=0, sticky=tk.W)
        self.analysis_team_var = tk.StringVar()
        analysis_combo = ttk.Combobox(selection_frame, textvariable=self.analysis_team_var,
                                    values=self.teams, state="readonly", width=30)
        analysis_combo.grid(row=0, column=1, padx=5)
        
        ttk.Button(selection_frame, text="Deep Analysis", 
                  command=self.deep_team_analysis).grid(row=0, column=2, padx=20)
        
        # Results
        results_frame = ttk.LabelFrame(analysis_frame, text="Team Analysis Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.analysis_results = scrolledtext.ScrolledText(results_frame, height=30, width=120)
        self.analysis_results.pack(fill=tk.BOTH, expand=True)
    
    def simulate_current_match(self):
        """Simulate match with current team characteristics"""
        home_team = self.home_team_var.get()
        away_team = self.away_team_var.get()
        
        if not home_team or not away_team:
            messagebox.showwarning("Warning", "Please select both teams")
            return
        
        if not self.enhanced_predictor:
            messagebox.showerror("Error", "Enhanced predictor not available")
            return
        
        self.match_results.delete(1.0, tk.END)
        self.match_results.insert(tk.END, "🏆 CURRENT MATCH SIMULATION\n")
        self.match_results.insert(tk.END, "=" * 50 + "\n\n")
        
        # Run simulation
        home_goals, away_goals, result = self.enhanced_predictor.simulate_match_with_scoreline(home_team, away_team)
        
        # Display results
        self.match_results.insert(tk.END, f"Match: {home_team} vs {away_team}\n")
        self.match_results.insert(tk.END, f"Result: {home_goals}-{away_goals}\n")
        
        if result == 'H':
            winner = f"{home_team} wins!"
        elif result == 'A':
            winner = f"{away_team} wins!"
        else:
            winner = "Draw!"
        
        self.match_results.insert(tk.END, f"Outcome: {winner}\n\n")
        
        # Show team characteristics
        home_chars = self.enhanced_predictor.performance_tracker.get_team_characteristics(home_team)
        away_chars = self.enhanced_predictor.performance_tracker.get_team_characteristics(away_team)
        
        self.match_results.insert(tk.END, f"{home_team} Characteristics:\n")
        self.match_results.insert(tk.END, f"  ELO: {self.elo_ratings.get(home_team, 0):.1f}\n")
        self.match_results.insert(tk.END, f"  Attack: {home_chars.get('attacking_overall', 1.0):.2f}\n")
        self.match_results.insert(tk.END, f"  Defense: {home_chars.get('defensive_overall', 1.0):.2f}\n")
        self.match_results.insert(tk.END, f"  Form: {home_chars.get('form', 0.0):.2f}\n\n")
        
        self.match_results.insert(tk.END, f"{away_team} Characteristics:\n")
        self.match_results.insert(tk.END, f"  ELO: {self.elo_ratings.get(away_team, 0):.1f}\n")
        self.match_results.insert(tk.END, f"  Attack: {away_chars.get('attacking_overall', 1.0):.2f}\n")
        self.match_results.insert(tk.END, f"  Defense: {away_chars.get('defensive_overall', 1.0):.2f}\n")
        self.match_results.insert(tk.END, f"  Form: {away_chars.get('form', 0.0):.2f}\n")
    
    def simulate_historical_match(self):
        """Simulate match using historical team data with separate dates"""
        home_team = self.home_team_var.get()
        away_team = self.away_team_var.get()
        home_date = self.home_date_var.get()
        away_date = self.away_date_var.get()
        
        if not home_team or not away_team:
            messagebox.showwarning("Warning", "Please select both teams")
            return
        
        # Get historical data for each team on their respective dates
        home_data = self.time_tracker.get_team_at_date(home_team, home_date)
        away_data = self.time_tracker.get_team_at_date(away_team, away_date)
        
        self.match_results.delete(1.0, tk.END)
        self.match_results.insert(tk.END, "🕐 HISTORICAL MATCH SIMULATION\n")
        self.match_results.insert(tk.END, "=" * 50 + "\n\n")
        
        self.match_results.insert(tk.END, f"Match: {home_team} vs {away_team}\n")
        self.match_results.insert(tk.END, f"Home Team Date: {home_date}\n")
        self.match_results.insert(tk.END, f"Away Team Date: {away_date}\n\n")
        
        if home_data and away_data:
            self.match_results.insert(tk.END, f"Historical Team States:\n\n")
            
            self.match_results.insert(tk.END, f"{home_team} (as of {home_date}):\n")
            self.match_results.insert(tk.END, f"  ELO: {home_data['elo']:.1f}\n")
            home_chars = home_data['characteristics']
            self.match_results.insert(tk.END, f"  Attack: {home_chars.get('attacking_overall', 1.0):.2f}\n")
            self.match_results.insert(tk.END, f"  Defense: {home_chars.get('defensive_overall', 1.0):.2f}\n")
            self.match_results.insert(tk.END, f"  Form: {home_chars.get('form', 0.0):+.2f}\n\n")
            
            self.match_results.insert(tk.END, f"{away_team} (as of {away_date}):\n")
            self.match_results.insert(tk.END, f"  ELO: {away_data['elo']:.1f}\n")
            away_chars = away_data['characteristics']
            self.match_results.insert(tk.END, f"  Attack: {away_chars.get('attacking_overall', 1.0):.2f}\n")
            self.match_results.insert(tk.END, f"  Defense: {away_chars.get('defensive_overall', 1.0):.2f}\n")
            self.match_results.insert(tk.END, f"  Form: {away_chars.get('form', 0.0):+.2f}\n\n")
            
            # Simulate using historical characteristics
            elo_diff = home_data['elo'] - away_data['elo']
            base_home_goals = 1.3 + (elo_diff / 400) * 0.5
            base_away_goals = 1.1 - (elo_diff / 400) * 0.3
            
            # Apply historical characteristics
            home_attack = home_chars.get('attacking_overall', 1.0)
            away_attack = away_chars.get('attacking_overall', 1.0)
            home_defense = home_chars.get('defensive_overall', 1.0)
            away_defense = away_chars.get('defensive_overall', 1.0)
            
            # Apply form effects
            home_form_effect = 1.0 + (home_chars.get('form', 0.0) * 0.2)
            away_form_effect = 1.0 + (away_chars.get('form', 0.0) * 0.2)
            
            home_expected = base_home_goals * home_attack * home_form_effect / away_defense
            away_expected = base_away_goals * away_attack * away_form_effect / home_defense
            
            # Generate result
            import numpy as np
            home_goals = np.random.poisson(max(0.1, home_expected))
            away_goals = np.random.poisson(max(0.1, away_expected))
            
            self.match_results.insert(tk.END, f"Historical Simulation Result: {home_goals}-{away_goals}\n")
            
            if home_goals > away_goals:
                winner = f"{home_team} wins!"
            elif away_goals > home_goals:
                winner = f"{away_team} wins!"
            else:
                winner = "Draw!"
            
            self.match_results.insert(tk.END, f"Outcome: {winner}\n\n")
            
            # Show prediction analysis
            self.match_results.insert(tk.END, f"Prediction Analysis:\n")
            self.match_results.insert(tk.END, f"  Expected {home_team} goals: {home_expected:.2f}\n")
            self.match_results.insert(tk.END, f"  Expected {away_team} goals: {away_expected:.2f}\n")
            self.match_results.insert(tk.END, f"  ELO Advantage: {elo_diff:+.1f} for {home_team}\n")
        else:
            missing_data = []
            if not home_data:
                missing_data.append(f"{home_team} on {home_date}")
            if not away_data:
                missing_data.append(f"{away_team} on {away_date}")
            self.match_results.insert(tk.END, f"❌ No historical data available for: {', '.join(missing_data)}\n")
            import numpy as np
            home_goals = np.random.poisson(max(0.1, home_expected))
            away_goals = np.random.poisson(max(0.1, away_expected))
            
            self.match_results.insert(tk.END, f"Historical Simulation Result: {home_goals}-{away_goals}\n")
            
            if home_goals > away_goals:
                winner = f"{home_team} wins!"
            elif away_goals > home_goals:
                winner = f"{away_team} wins!"
            else:
                winner = "Draw!"
            
            self.match_results.insert(tk.END, f"Outcome: {winner}\n")
        def compare_dates(self):
        """Compare team performance between current and historical dates"""
        home_team = self.home_team_var.get()
        away_team = self.away_team_var.get()
        home_date = self.home_date_var.get()
        away_date = self.away_date_var.get()
        
        if not home_team or not away_team:
            messagebox.showwarning("Warning", "Please select both teams")
            return
        
        self.match_results.delete(1.0, tk.END)
        self.match_results.insert(tk.END, "📊 TEAM COMPARISON: CURRENT vs HISTORICAL
")
        self.match_results.insert(tk.END, "=" * 60 + "

")
        
        # Current data
        current_home_elo = self.elo_ratings.get(home_team, 1500)
        current_away_elo = self.elo_ratings.get(away_team, 1500)
        
        # Historical data
        home_data = self.time_tracker.get_team_at_date(home_team, home_date)
        away_data = self.time_tracker.get_team_at_date(away_team, away_date)
        
        # Display comparison
        self.match_results.insert(tk.END, f"🏠 {home_team} COMPARISON:
")
        self.match_results.insert(tk.END, f"Current ELO: {current_home_elo:.1f}
")
        if home_data:
            self.match_results.insert(tk.END, f"Historical ELO ({home_date}): {home_data['elo']:.1f}
")
            elo_change = current_home_elo - home_data['elo']
            self.match_results.insert(tk.END, f"ELO Change: {elo_change:+.1f}
")
            
            # Show characteristic changes
            home_chars = home_data['characteristics']
            self.match_results.insert(tk.END, f"Historical Attack: {home_chars.get('attacking_overall', 1.0):.2f}
")
            self.match_results.insert(tk.END, f"Historical Defense: {home_chars.get('defensive_overall', 1.0):.2f}
")
            self.match_results.insert(tk.END, f"Historical Form: {home_chars.get('form', 0.0):+.2f}
")
        else:
            self.match_results.insert(tk.END, f"No historical data for {home_date}
")
        
        self.match_results.insert(tk.END, "
")
        
        self.match_results.insert(tk.END, f"✈️ {away_team} COMPARISON:
")
        self.match_results.insert(tk.END, f"Current ELO: {current_away_elo:.1f}
")
        if away_data:
            self.match_results.insert(tk.END, f"Historical ELO ({away_date}): {away_data['elo']:.1f}
")
            elo_change = current_away_elo - away_data['elo']
            self.match_results.insert(tk.END, f"ELO Change: {elo_change:+.1f}
")
            
            # Show characteristic changes
            away_chars = away_data['characteristics']
            self.match_results.insert(tk.END, f"Historical Attack: {away_chars.get('attacking_overall', 1.0):.2f}
")
            self.match_results.insert(tk.END, f"Historical Defense: {away_chars.get('defensive_overall', 1.0):.2f}
")
            self.match_results.insert(tk.END, f"Historical Form: {away_chars.get('form', 0.0):+.2f}
")
        else:
            self.match_results.insert(tk.END, f"No historical data for {away_date}
")
    
    def compare_dates(self):
        """Compare team performance between current and historical date"""
        home_team = self.home_team_var.get()
        away_team = self.away_team_var.get()
        match_date = self.match_date_var.get()
        
        if not home_team or not away_team:
            messagebox.showwarning("Warning", "Please select both teams")
            return
        
        self.match_results.delete(1.0, tk.END)
        self.match_results.insert(tk.END, "📊 TEAM COMPARISON: CURRENT vs HISTORICAL\n")
        self.match_results.insert(tk.END, "=" * 60 + "\n\n")
        
        # Current data
        if self.enhanced_predictor:
            current_home_chars = self.enhanced_predictor.performance_tracker.get_team_characteristics(home_team)
            current_away_chars = self.enhanced_predictor.performance_tracker.get_team_characteristics(away_team)
            current_home_elo = self.elo_ratings.get(home_team, 1500)
            current_away_elo = self.elo_ratings.get(away_team, 1500)
        else:
            current_home_chars = {'attacking_overall': 1.0, 'defensive_overall': 1.0, 'form': 0.0}
            current_away_chars = {'attacking_overall': 1.0, 'defensive_overall': 1.0, 'form': 0.0}
            current_home_elo = 1500
            current_away_elo = 1500
        
        # Historical data
        home_data = self.time_tracker.get_team_at_date(home_team, match_date)
        away_data = self.time_tracker.get_team_at_date(away_team, match_date)
        
        # Display comparison
        self.match_results.insert(tk.END, f"🏠 {home_team} COMPARISON:\n")
        self.match_results.insert(tk.END, f"Current ELO: {current_home_elo:.1f}\n")
        if home_data:
            self.match_results.insert(tk.END, f"Historical ELO ({match_date}): {home_data['elo']:.1f}\n")
            elo_change = current_home_elo - home_data['elo']
            self.match_results.insert(tk.END, f"ELO Change: {elo_change:+.1f}\n")
        else:
            self.match_results.insert(tk.END, f"No historical data for {match_date}\n")
        
        self.match_results.insert(tk.END, "\n")
        
        self.match_results.insert(tk.END, f"✈️ {away_team} COMPARISON:\n")
        self.match_results.insert(tk.END, f"Current ELO: {current_away_elo:.1f}\n")
        if away_data:
            self.match_results.insert(tk.END, f"Historical ELO ({match_date}): {away_data['elo']:.1f}\n")
            elo_change = current_away_elo - away_data['elo']
            self.match_results.insert(tk.END, f"ELO Change: {elo_change:+.1f}\n")
        else:
            self.match_results.insert(tk.END, f"No historical data for {match_date}\n")
    
    def run_enhanced_simulation(self):
        """Run enhanced league simulation"""
        try:
            num_seasons = int(self.season_count_var.get())
            if num_seasons <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of seasons")
            return
        
        league_choice = self.league_selection_var.get()
        
        self.season_results.delete(1.0, tk.END)
        self.season_results.insert(tk.END, f"🏆 ENHANCED LEAGUE SIMULATION\n")
        self.season_results.insert(tk.END, f"League Selection: {league_choice}\n")
        self.season_results.insert(tk.END, f"Seasons: {num_seasons}\n")
        self.season_results.insert(tk.END, "=" * 60 + "\n\n")
        
        # Reset analysis
        self.team_analysis = EnhancedTeamAnalysisSystem()
        
        # Get teams for selected league(s)
        if league_choice == "Esiliiga Only":
            sim_teams = [team for team in self.teams if EstonianLeagueSystem.get_team_league(team) == "Esiliiga"]
        elif league_choice == "Esiliiga B Only":
            sim_teams = [team for team in self.teams if EstonianLeagueSystem.get_team_league(team) == "Esiliiga B"]
        else:
            sim_teams = self.teams
        
        # Run simulations
        for season in range(num_seasons):
            self.simulate_enhanced_season(sim_teams, league_choice)
            
            if (season + 1) % 50 == 0:
                self.season_results.insert(tk.END, f"Completed {season + 1}/{num_seasons} seasons...\n")
                self.root.update()
        
        # Display results
        self.display_enhanced_analysis(sim_teams)
    
    def simulate_enhanced_season(self, teams: list, league_type: str):
        """Simulate a single enhanced season"""
        standings = {}
        
        for team in teams:
            elo = self.elo_ratings.get(team, 1500)
            league = EstonianLeagueSystem.get_team_league(team)
            
            # Season simulation based on ELO and league
            base_strength = (elo - 1400) / 200
            season_modifier = random.gauss(0, 0.3)
            season_strength = base_strength + season_modifier
            
            # Calculate points
            matches = 36 if len(teams) >= 18 else 18  # Adjust for league size
            win_rate = max(0.05, min(0.95, 0.5 + season_strength * 0.2))
            
            expected_wins = matches * win_rate
            expected_draws = matches * 0.25
            expected_points = expected_wins * 3 + expected_draws * 1
            
            actual_points = max(5, int(expected_points + random.gauss(0, 8)))
            goal_difference = int((season_strength * 20) + random.gauss(0, 10))
            
            standings[team] = {
                'points': actual_points,
                'goal_difference': goal_difference,
                'league': league
            }
        
        # Sort teams by league first, then by points
        esiliiga_teams = [(team, stats) for team, stats in standings.items() 
                         if stats['league'] == 'Esiliiga']
        esiliiga_b_teams = [(team, stats) for team, stats in standings.items() 
                           if stats['league'] == 'Esiliiga B']
        
        # Analyze Esiliiga
        if esiliiga_teams:
            sorted_esiliiga = sorted(esiliiga_teams, 
                                   key=lambda x: (x[1]['points'], x[1]['goal_difference']), 
                                   reverse=True)
            for position, (team, stats) in enumerate(sorted_esiliiga, 1):
                self.team_analysis.analyze_team_season(
                    team, position, stats['points'], stats['goal_difference'], 
                    len(sorted_esiliiga), "Esiliiga"
                )
        
        # Analyze Esiliiga B
        if esiliiga_b_teams:
            sorted_esiliiga_b = sorted(esiliiga_b_teams, 
                                     key=lambda x: (x[1]['points'], x[1]['goal_difference']), 
                                     reverse=True)
            for position, (team, stats) in enumerate(sorted_esiliiga_b, 1):
                self.team_analysis.analyze_team_season(
                    team, position, stats['points'], stats['goal_difference'], 
                    len(sorted_esiliiga_b), "Esiliiga B"
                )
    
    def display_enhanced_analysis(self, teams: list):
        """Display enhanced analysis results"""
        self.season_results.insert(tk.END, "\n🎯 SIMULATION RESULTS\n")
        self.season_results.insert(tk.END, "=" * 60 + "\n\n")
        
        # Group by league
        esiliiga_teams = [team for team in teams if EstonianLeagueSystem.get_team_league(team) == "Esiliiga"]
        esiliiga_b_teams = [team for team in teams if EstonianLeagueSystem.get_team_league(team) == "Esiliiga B"]
        
        # Esiliiga results
        if esiliiga_teams:
            self.season_results.insert(tk.END, "🥇 ESILIIGA RESULTS:\n\n")
            esiliiga_analyses = [(team, self.team_analysis.get_team_analysis(team)) 
                               for team in esiliiga_teams]
            esiliiga_analyses.sort(key=lambda x: x[1]['league_win_rate'], reverse=True)
            
            for team, analysis in esiliiga_analyses:
                elo = self.elo_ratings.get(team, 1500)
                self.season_results.insert(tk.END, 
                    f"{team:<25} | ELO: {elo:4.0f} | Wins: {analysis['league_win_rate']:5.1f}% | "
                    f"Avg Points: {analysis['avg_points']:4.0f} | Range: {analysis['points_range']}\n")
        
        # Esiliiga B results  
        if esiliiga_b_teams:
            self.season_results.insert(tk.END, "\n🥈 ESILIIGA B RESULTS:\n\n")
            esiliiga_b_analyses = [(team, self.team_analysis.get_team_analysis(team)) 
                                 for team in esiliiga_b_teams]
            esiliiga_b_analyses.sort(key=lambda x: x[1]['league_win_rate'], reverse=True)
            
            for team, analysis in esiliiga_b_analyses:
                elo = self.elo_ratings.get(team, 1500)
                self.season_results.insert(tk.END, 
                    f"{team:<25} | ELO: {elo:4.0f} | Wins: {analysis['league_win_rate']:5.1f}% | "
                    f"Avg Points: {analysis['avg_points']:4.0f} | Range: {analysis['points_range']}\n")
    
    def analyze_historical_performance(self):
        """Analyze historical performance for selected team"""
        team = self.history_team_var.get()
        start_date = self.start_date_var.get()
        end_date = self.end_date_var.get()
        
        if not team:
            messagebox.showwarning("Warning", "Please select a team")
            return
        
        self.history_results.delete(1.0, tk.END)
        self.history_results.insert(tk.END, f"📈 HISTORICAL ANALYSIS: {team}\n")
        self.history_results.insert(tk.END, f"Period: {start_date} to {end_date}\n")
        self.history_results.insert(tk.END, "=" * 60 + "\n\n")
        
        # Get historical data
        if team in self.time_tracker.team_history:
            history = self.time_tracker.team_history[team]
            
            # Filter by date range
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            filtered_history = []
            for record in history:
                record_date = datetime.strptime(record['date'], '%Y-%m-%d')
                if start <= record_date <= end:
                    filtered_history.append(record)
            
            if filtered_history:
                # Show trend
                self.history_results.insert(tk.END, "ELO RATING TREND:\n")
                for record in filtered_history:
                    chars = record['characteristics']
                    self.history_results.insert(tk.END, 
                        f"{record['date']}: ELO {record['elo']:4.0f} | "
                        f"Attack {chars.get('attacking_overall', 1.0):.2f} | "
                        f"Defense {chars.get('defensive_overall', 1.0):.2f} | "
                        f"Form {chars.get('form', 0.0):+.2f}\n")
                
                # Calculate statistics
                elos = [r['elo'] for r in filtered_history]
                attacks = [r['characteristics'].get('attacking_overall', 1.0) for r in filtered_history]
                defenses = [r['characteristics'].get('defensive_overall', 1.0) for r in filtered_history]
                forms = [r['characteristics'].get('form', 0.0) for r in filtered_history]
                
                self.history_results.insert(tk.END, f"\n📊 SUMMARY STATISTICS:\n")
                self.history_results.insert(tk.END, f"ELO Range: {min(elos):.0f} - {max(elos):.0f}\n")
                self.history_results.insert(tk.END, f"Average ELO: {sum(elos)/len(elos):.1f}\n")
                self.history_results.insert(tk.END, f"Attack Range: {min(attacks):.2f} - {max(attacks):.2f}\n")
                self.history_results.insert(tk.END, f"Defense Range: {min(defenses):.2f} - {max(defenses):.2f}\n")
                self.history_results.insert(tk.END, f"Form Range: {min(forms):+.2f} - {max(forms):+.2f}\n")
            else:
                self.history_results.insert(tk.END, "No data found for the specified date range.\n")
        else:
            self.history_results.insert(tk.END, "No historical data available for this team.\n")
    
    def deep_team_analysis(self):
        """Perform deep analysis of selected team"""
        team = self.analysis_team_var.get()
        
        if not team:
            messagebox.showwarning("Warning", "Please select a team")
            return
        
        self.analysis_results.delete(1.0, tk.END)
        self.analysis_results.insert(tk.END, f"🔍 DEEP DIVE ANALYSIS: {team}\n")
        self.analysis_results.insert(tk.END, "=" * 60 + "\n\n")
        
        # Basic information
        elo = self.elo_ratings.get(team, 1500)
        league = EstonianLeagueSystem.get_team_league(team)
        
        self.analysis_results.insert(tk.END, f"📊 BASIC INFORMATION:\n")
        self.analysis_results.insert(tk.END, f"   Current ELO Rating: {elo:.1f}\n")
        self.analysis_results.insert(tk.END, f"   League: {league}\n")
        
        # Current characteristics
        if self.enhanced_predictor:
            chars = self.enhanced_predictor.performance_tracker.get_team_characteristics(team)
            self.analysis_results.insert(tk.END, f"\n🎯 CURRENT CHARACTERISTICS:\n")
            self.analysis_results.insert(tk.END, f"   Home Advantage: {chars.get('home_advantage', 1.0):.2f}x\n")
            self.analysis_results.insert(tk.END, f"   Attacking (Home): {chars.get('attacking_home', 1.0):.2f}x\n")
            self.analysis_results.insert(tk.END, f"   Attacking (Away): {chars.get('attacking_away', 1.0):.2f}x\n")
            self.analysis_results.insert(tk.END, f"   Defensive (Home): {chars.get('defensive_home', 1.0):.2f}x\n")
            self.analysis_results.insert(tk.END, f"   Defensive (Away): {chars.get('defensive_away', 1.0):.2f}x\n")
            self.analysis_results.insert(tk.END, f"   Current Form: {chars.get('form', 0.0):+.2f}\n")
            self.analysis_results.insert(tk.END, f"   Consistency: {chars.get('consistency', 1.0):.2f}x\n")
        
        # Season performance analysis
        analysis = self.team_analysis.get_team_analysis(team)
        simulations = self.team_analysis.team_stats[team]['simulations_run']
        
        self.analysis_results.insert(tk.END, f"\n🏆 SEASON PERFORMANCE ANALYSIS:\n")
        self.analysis_results.insert(tk.END, f"   Simulations Run: {simulations}\n")
        if simulations > 0:
            self.analysis_results.insert(tk.END, f"   League Wins: {analysis['league_win_rate']:.1f}%\n")
            self.analysis_results.insert(tk.END, f"   Promotion Rate: {analysis['promotion_rate']:.1f}%\n")
            self.analysis_results.insert(tk.END, f"   Relegation Rate: {analysis['relegation_rate']:.1f}%\n")
            
            stats = self.team_analysis.team_stats[team]
            self.analysis_results.insert(tk.END, f"\n📈 SIMULATION EXTREMES:\n")
            self.analysis_results.insert(tk.END, f"   Best Season: {stats['best_points']} points\n")
            self.analysis_results.insert(tk.END, f"   Worst Season: {stats['worst_points']} points\n")
        else:
            self.analysis_results.insert(tk.END, "   No simulation data available\n")
            self.analysis_results.insert(tk.END, "   Run league simulations to see performance analysis\n")
        
        # League context
        league_teams = [t for t in self.teams if EstonianLeagueSystem.get_team_league(t) == league]
        league_elos = [self.elo_ratings.get(t, 1500) for t in league_teams]
        team_rank = sorted(league_teams, key=lambda t: self.elo_ratings.get(t, 1500), reverse=True).index(team) + 1
        
        self.analysis_results.insert(tk.END, f"\n🏅 LEAGUE CONTEXT:\n")
        self.analysis_results.insert(tk.END, f"   League Rank: {team_rank}/{len(league_teams)}\n")
        self.analysis_results.insert(tk.END, f"   League Average ELO: {sum(league_elos)/len(league_elos):.1f}\n")
        self.analysis_results.insert(tk.END, f"   ELO vs League Avg: {elo - (sum(league_elos)/len(league_elos)):+.1f}\n")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main function"""
    app = EnhancedEstonianFootballTimeMachine()
    app.run()


if __name__ == "__main__":
    main()
