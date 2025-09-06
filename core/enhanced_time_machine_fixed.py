#!/usr/bin/env python3
"""
Enhanced Estonian Football Time Machine - Fixed Version
- League-specific season simulation with all teams
- Historical match simulation with separate dates for each team
- Time-based team analysis with varying characteristics
- Improved user interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from collections import defaultdict
import random
from datetime import datetime, timedelta
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
    """Estonian league system helper with actual team data"""
    
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
    """Track team characteristics over time with realistic variation"""
    
    def __init__(self):
        self.team_history = defaultdict(list)
        
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
    """Enhanced team analysis with league-specific statistics and detailed tracking"""
    
    def __init__(self):
        self.team_stats = {}
    
    def _init_team(self, team: str):
        """Initialize team stats if not exists"""
        if team not in self.team_stats:
            self.team_stats[team] = {
                'league_wins': 0,
                'promotions': 0,
                'relegations': 0,
                'best_points': 0,
                'worst_points': 999,
                'best_goal_diff': -100,
                'worst_goal_diff': 100,
                'simulations_run': 0,
                'league': 'Unknown',
                'season_records': [],  # Track individual seasons
                'elo_history': []  # Track ELO changes
            }
    
    def analyze_team_season(self, team: str, final_position: int, points: int, 
                          goal_difference: int, league_size: int, league: str = "Unknown"):
        """Analyze team season with league context and detailed tracking"""
        self._init_team(team)
        stats = self.team_stats[team]
        
        stats['simulations_run'] += 1
        stats['league'] = league
        
        # Fix initialization
        if stats['simulations_run'] == 1:
            stats['worst_points'] = points
            stats['best_goal_diff'] = goal_difference
            stats['worst_goal_diff'] = goal_difference
        
        # Track extremes
        stats['best_points'] = max(stats['best_points'], points)
        stats['worst_points'] = min(stats['worst_points'], points)
        stats['best_goal_diff'] = max(stats['best_goal_diff'], goal_difference)
        stats['worst_goal_diff'] = min(stats['worst_goal_diff'], goal_difference)
        
        # Store individual season record
        season_record = {
            'position': final_position,
            'points': points,
            'goal_difference': goal_difference,
            'season_number': stats['simulations_run']
        }
        stats['season_records'].append(season_record)
        
        # League-specific analysis
        if league == "Esiliiga":
            if final_position == 1:
                stats['league_wins'] += 1
            elif final_position <= 2:
                stats['promotions'] += 1
        elif league == "Esiliiga B":
            if final_position == 1:
                stats['league_wins'] += 1
            elif final_position <= 2:
                stats['promotions'] += 1
            elif final_position >= league_size - 1:
                stats['relegations'] += 1
    
    def get_team_analysis(self, team: str) -> dict:
        """Get comprehensive team analysis with detailed statistics"""
        if team not in self.team_stats:
            return {
                'league_win_rate': 0.0,
                'promotion_rate': 0.0,
                'relegation_rate': 0.0,
                'avg_points': 0,
                'points_range': "No data",
                'goal_diff_range': "No data",
                'best_season': None,
                'worst_season': None
            }
        
        stats = self.team_stats[team]
        if stats['simulations_run'] == 0:
            return {
                'league_win_rate': 0.0,
                'promotion_rate': 0.0,
                'relegation_rate': 0.0,
                'avg_points': 0,
                'points_range': "No data",
                'goal_diff_range': "No data",
                'best_season': None,
                'worst_season': None
            }
        
        sims = stats['simulations_run']
        
        # Find best and worst seasons
        best_season = max(stats['season_records'], key=lambda x: x['points']) if stats['season_records'] else None
        worst_season = min(stats['season_records'], key=lambda x: x['points']) if stats['season_records'] else None
        
        return {
            'league_win_rate': (stats['league_wins'] / sims) * 100,
            'promotion_rate': (stats['promotions'] / sims) * 100,
            'relegation_rate': (stats['relegations'] / sims) * 100,
            'avg_points': (stats['best_points'] + stats['worst_points']) / 2,
            'points_range': f"{stats['worst_points']}-{stats['best_points']}",
            'goal_diff_range': f"{stats['worst_goal_diff']:+d} to {stats['best_goal_diff']:+d}",
            'best_season': best_season,
            'worst_season': worst_season,
            'season_records': stats['season_records']  # Add season_records to fix KeyError
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
        if predictor_available:
            try:
                self.enhanced_predictor = EnhancedEstonianPredictor()
                self.elo_ratings = self.enhanced_predictor.elo_ratings
                self.teams = list(self.elo_ratings.keys())
                print("✅ Enhanced predictor loaded")
                self._initialize_time_data()
            except Exception as e:
                print(f"❌ Error loading predictor: {e}")
                self.enhanced_predictor = None
                self._initialize_demo_data()
        else:
            self.enhanced_predictor = None
            self._initialize_demo_data()
            
        self.setup_gui()
    
    def _initialize_demo_data(self):
        """Initialize demo data if predictor unavailable"""
        all_teams = EstonianLeagueSystem.ESILIIGA_TEAMS + EstonianLeagueSystem.ESILIIGA_B_TEAMS
        self.teams = all_teams
        
        # Create demo ELO ratings
        for i, team in enumerate(all_teams):
            base_elo = 1500 + (i * 10) - 100
            self.elo_ratings[team] = base_elo + random.randint(-50, 50)
        
        self._initialize_time_data()
    
    def _initialize_time_data(self):
        """Initialize time-based data for historical simulation with realistic variation"""
        base_date = datetime(2025, 3, 1)
        
        for team in self.teams:
            base_elo = self.elo_ratings[team]
            
            # Get initial characteristics if available
            if self.enhanced_predictor and hasattr(self.enhanced_predictor, 'performance_tracker'):
                base_chars = self.enhanced_predictor.performance_tracker.get_team_characteristics(team)
            else:
                base_chars = {
                    'attacking_overall': 0.8 + random.random() * 0.4,
                    'defensive_overall': 0.8 + random.random() * 0.4,
                    'form': random.gauss(0, 0.2),
                    'home_advantage': 1.0 + random.gauss(0, 0.1),
                    'consistency': 1.0 + random.gauss(0, 0.05)
                }
            
            for week in range(0, 30, 2):  # Every 2 weeks
                date = base_date + timedelta(weeks=week)
                date_str = date.strftime('%Y-%m-%d')
                
                # Simulate ELO evolution with realistic drift
                elo_drift = random.gauss(0, week * 1.5)
                historical_elo = max(1200, min(1800, base_elo + elo_drift))
                
                # Create varying characteristics over time
                time_factor = week / 30.0
                
                # Attack characteristics evolve with team-specific trends
                attack_trend = random.gauss(0, 0.08)
                attack_noise = random.gauss(0, 0.04)
                attacking = max(0.5, min(1.5, base_chars['attacking_overall'] + 
                               (time_factor * attack_trend) + attack_noise))
                
                # Defense characteristics evolve independently
                defense_trend = random.gauss(0, 0.08)
                defense_noise = random.gauss(0, 0.04)
                defensive = max(0.5, min(1.5, base_chars['defensive_overall'] + 
                               (time_factor * defense_trend) + defense_noise))
                
                # Form varies dramatically (short-term) with more realistic ranges
                form_change = random.gauss(0, 0.4)  # Increased variance for more realistic variation
                # Bias form slightly toward team performance level for realism
                elo_influence = (historical_elo - 1500) / 1000  # -0.5 to +0.5 range
                form = max(-1.0, min(1.0, base_chars['form'] + form_change + elo_influence * 0.2))
                
                chars = {
                    'attacking_overall': attacking,
                    'defensive_overall': defensive,
                    'form': form,
                    'home_advantage': base_chars.get('home_advantage', 1.0) + random.gauss(0, 0.02),
                    'consistency': base_chars.get('consistency', 1.0) + random.gauss(0, 0.03)
                }
                
                self.time_tracker.record_team_state(team, date_str, historical_elo, chars)
    
    def setup_gui(self):
        """Setup the enhanced GUI"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create enhanced tabs
        self.create_enhanced_match_tab()
        self.create_league_simulation_tab()
        self.create_historical_analysis_tab()
        self.create_team_analysis_tab()
    
    def create_enhanced_match_tab(self):
        """Enhanced match prediction with separate dates for each team"""
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
        
        # Separate date selection for each team
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
        """Simulate match 1000 times for comprehensive analysis"""
        home_team = self.home_team_var.get()
        away_team = self.away_team_var.get()
        
        if not home_team or not away_team:
            messagebox.showwarning("Warning", "Please select both teams")
            return

        self.match_results.delete(1.0, tk.END)
        self.match_results.insert(tk.END, "🏆 COMPREHENSIVE MATCH SIMULATION (1000 GAMES)\n")
        self.match_results.insert(tk.END, "=" * 60 + "\n\n")
        
        # Run 1000 simulations for comprehensive analysis
        all_results = []
        home_wins = 0
        away_wins = 0
        draws = 0
        home_goals_total = 0
        away_goals_total = 0
        biggest_home_win = (0, 0)
        biggest_away_win = (0, 0)
        
        for sim_num in range(1000):
            # Run simulation
            if self.enhanced_predictor and hasattr(self.enhanced_predictor, 'simulate_match_with_scoreline'):
                home_goals, away_goals, result = self.enhanced_predictor.simulate_match_with_scoreline(home_team, away_team)
            else:
                # Enhanced realistic simulation based on ELO
                home_elo = self.elo_ratings.get(home_team, 1500)
                away_elo = self.elo_ratings.get(away_team, 1500)
                elo_diff = home_elo - away_elo
                
                import numpy as np
                # More realistic goal expectations based on ELO difference
                base_home = 1.4  # Home advantage
                base_away = 1.1
                
                # ELO impact: stronger teams score more, concede less
                elo_factor = elo_diff / 200  # Reduced from 400 for more realistic differences
                home_expected = max(0.2, base_home + elo_factor * 0.4)
                away_expected = max(0.2, base_away - elo_factor * 0.3)
                
                home_goals = np.random.poisson(home_expected)
                away_goals = np.random.poisson(away_expected)
                
                if home_goals > away_goals:
                    result = 'H'
                elif away_goals > home_goals:
                    result = 'A'
                else:
                    result = 'D'
            
            all_results.append((home_goals, away_goals))
            home_goals_total += home_goals
            away_goals_total += away_goals
            
            # Track biggest wins
            if home_goals > away_goals:
                home_wins += 1
                margin = home_goals - away_goals
                if margin > (biggest_home_win[0] - biggest_home_win[1]):
                    biggest_home_win = (home_goals, away_goals)
            elif away_goals > home_goals:
                away_wins += 1
                margin = away_goals - home_goals
                if margin > (biggest_away_win[1] - biggest_away_win[0]):
                    biggest_away_win = (home_goals, away_goals)
            else:
                draws += 1
        
        # Calculate averages
        avg_home_goals = home_goals_total / 1000
        avg_away_goals = away_goals_total / 1000
        
        # Show comprehensive statistics
        self.match_results.insert(tk.END, f"📊 SIMULATION RESULTS:\n")
        self.match_results.insert(tk.END, f"   {home_team} wins: {home_wins}/1000 ({home_wins/10:.1f}%)\n")
        self.match_results.insert(tk.END, f"   {away_team} wins: {away_wins}/1000 ({away_wins/10:.1f}%)\n")
        self.match_results.insert(tk.END, f"   Draws: {draws}/1000 ({draws/10:.1f}%)\n\n")
        
        # Average score prediction
        self.match_results.insert(tk.END, f"📈 AVERAGE GOALS PER GAME:\n")
        self.match_results.insert(tk.END, f"   {home_team}: {avg_home_goals:.2f} goals per game\n")
        self.match_results.insert(tk.END, f"   {away_team}: {avg_away_goals:.2f} goals per game\n")
        self.match_results.insert(tk.END, f"   Predicted score: {avg_home_goals:.2f} - {avg_away_goals:.2f}\n\n")
        
        # Show team ELO ratings for context
        home_elo = self.elo_ratings.get(home_team, 1500)
        away_elo = self.elo_ratings.get(away_team, 1500)
        elo_diff = abs(home_elo - away_elo)
        self.match_results.insert(tk.END, f"⚖️  TEAM RATINGS:\n")
        self.match_results.insert(tk.END, f"   {home_team}: {home_elo:.1f} ELO\n")
        self.match_results.insert(tk.END, f"   {away_team}: {away_elo:.1f} ELO\n")
        self.match_results.insert(tk.END, f"   ELO Difference: {elo_diff:.1f} points\n\n")
        
        # Most popular result
        from collections import Counter
        result_counts = Counter(all_results)
        most_common = result_counts.most_common(1)[0]
        self.match_results.insert(tk.END, f"🎯 MOST POPULAR RESULT: {most_common[0][0]}-{most_common[0][1]} (occurred {most_common[1]} times, {most_common[1]/10:.1f}%)\n\n")
        
        # Biggest wins
        if biggest_home_win != (0, 0):
            self.match_results.insert(tk.END, f"🔥 BIGGEST {home_team.upper()} WIN: {biggest_home_win[0]}-{biggest_home_win[1]}\n")
        if biggest_away_win != (0, 0):
            self.match_results.insert(tk.END, f"🔥 BIGGEST {away_team.upper()} WIN: {biggest_away_win[0]}-{biggest_away_win[1]}\n")
    
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
            
            # FIXED: Correct ELO-based expected goals calculation
            # Home team gets advantage from positive elo_diff, away team gets penalized
            base_home_goals = 1.4 + (elo_diff / 400) * 0.6  # Higher ELO = more goals
            base_away_goals = 1.2 - (elo_diff / 400) * 0.6  # FIXED: Away team should be penalized more when home has ELO advantage
            
            # Apply historical characteristics
            home_attack = home_chars.get('attacking_overall', 1.0)
            away_attack = away_chars.get('attacking_overall', 1.0)
            home_defense = home_chars.get('defensive_overall', 1.0)
            away_defense = away_chars.get('defensive_overall', 1.0)
            
            # Apply form effects (stronger impact)
            home_form_effect = 1.0 + (home_chars.get('form', 0.0) * 0.3)
            away_form_effect = 1.0 + (away_chars.get('form', 0.0) * 0.3)
            
            # Calculate expected goals with better scaling
            home_expected = max(0.3, base_home_goals * home_attack * home_form_effect / max(0.7, away_defense))
            away_expected = max(0.3, base_away_goals * away_attack * away_form_effect / max(0.7, home_defense))
            
            # Add home advantage
            home_expected *= 1.2  # Home advantage boost
            
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
        self.match_results.insert(tk.END, "📊 TEAM COMPARISON: CURRENT vs HISTORICAL\n")
        self.match_results.insert(tk.END, "=" * 60 + "\n\n")
        
        # Current data
        current_home_elo = self.elo_ratings.get(home_team, 1500)
        current_away_elo = self.elo_ratings.get(away_team, 1500)
        
        # Historical data
        home_data = self.time_tracker.get_team_at_date(home_team, home_date)
        away_data = self.time_tracker.get_team_at_date(away_team, away_date)
        
        # Display comparison
        self.match_results.insert(tk.END, f"🏠 {home_team} COMPARISON:\n")
        self.match_results.insert(tk.END, f"Current ELO: {current_home_elo:.1f}\n")
        if home_data:
            self.match_results.insert(tk.END, f"Historical ELO ({home_date}): {home_data['elo']:.1f}\n")
            elo_change = current_home_elo - home_data['elo']
            self.match_results.insert(tk.END, f"ELO Change: {elo_change:+.1f}\n")
            
            # Show characteristic changes
            home_chars = home_data['characteristics']
            self.match_results.insert(tk.END, f"Historical Attack: {home_chars.get('attacking_overall', 1.0):.2f}\n")
            self.match_results.insert(tk.END, f"Historical Defense: {home_chars.get('defensive_overall', 1.0):.2f}\n")
            self.match_results.insert(tk.END, f"Historical Form: {home_chars.get('form', 0.0):+.2f}\n")
        else:
            self.match_results.insert(tk.END, f"No historical data for {home_date}\n")
        
        self.match_results.insert(tk.END, "\n")
        
        self.match_results.insert(tk.END, f"✈️ {away_team} COMPARISON:\n")
        self.match_results.insert(tk.END, f"Current ELO: {current_away_elo:.1f}\n")
        if away_data:
            self.match_results.insert(tk.END, f"Historical ELO ({away_date}): {away_data['elo']:.1f}\n")
            elo_change = current_away_elo - away_data['elo']
            self.match_results.insert(tk.END, f"ELO Change: {elo_change:+.1f}\n")
            
            # Show characteristic changes
            away_chars = away_data['characteristics']
            self.match_results.insert(tk.END, f"Historical Attack: {away_chars.get('attacking_overall', 1.0):.2f}\n")
            self.match_results.insert(tk.END, f"Historical Defense: {away_chars.get('defensive_overall', 1.0):.2f}\n")
            self.match_results.insert(tk.END, f"Historical Form: {away_chars.get('form', 0.0):+.2f}\n")
        else:
            self.match_results.insert(tk.END, f"No historical data for {away_date}\n")
    
    def run_enhanced_simulation(self):
        """Run enhanced league simulation with all teams"""
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
        
        self.season_results.insert(tk.END, f"Simulating {len(sim_teams)} teams...\n\n")
        
        # Run simulations
        for season in range(num_seasons):
            self.simulate_enhanced_season(sim_teams, league_choice)
            
            if (season + 1) % 50 == 0:
                self.season_results.insert(tk.END, f"Completed {season + 1}/{num_seasons} seasons...\n")
                self.root.update()
        
        # Display results
        self.display_enhanced_analysis(sim_teams)
    
    def get_current_season_standings(self):
        """Calculate current standings from actual 2025 matches played so far"""
        standings = {}
        
        # Initialize all teams
        for team in self.teams:
            standings[team] = {
                'points': 0,
                'goal_difference': 0,
                'games_played': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0
            }
        
        # Calculate standings from actual match data
        try:
            import pandas as pd
            from datetime import datetime
            import re
            import os
            
            # Load actual match data with absolute paths
            script_dir = os.path.dirname(os.path.abspath(__file__))
            df1 = pd.read_csv(os.path.join(script_dir, 'esiliiga2025.csv'))
            df2 = pd.read_csv(os.path.join(script_dir, 'esiliigab2025.csv'))
            
            def extract_date(date_str):
                match = re.search(r'(\d{1,2}/\d{1,2}/\d{2})', str(date_str))
                if match:
                    return datetime.strptime(match.group(1), '%m/%d/%y')
                return None
            
            df1['parsed_date'] = df1['Date/Time'].apply(extract_date)
            df2['parsed_date'] = df2['Date/Time'].apply(extract_date)
            
            current_date = datetime(2025, 9, 5)  # Current date
            
            # Process both leagues - count ALL matches with valid results
            for df in [df1, df2]:
                # Process all matches with valid results, regardless of date
                for _, match in df.iterrows():
                    home = match['Home']
                    away = match['Away']
                    result = match['Result']
                    
                    # Skip unplayed matches (results like "-:-")
                    if result == '-:-' or result == '' or pd.isna(result):
                        continue
                    
                    # Parse result - only process matches with valid scores
                    try:
                        home_goals, away_goals = map(int, str(result).split(':'))
                    except:
                        continue
                    
                    # Initialize teams if not in our list (safety check)
                    if home not in standings:
                        continue
                    if away not in standings:
                        continue
                    
                    # Update stats
                    standings[home]['games_played'] += 1
                    standings[away]['games_played'] += 1
                    standings[home]['goal_difference'] += (home_goals - away_goals)
                    standings[away]['goal_difference'] += (away_goals - home_goals)
                    
                    # Award points
                    if home_goals > away_goals:  # Home win
                        standings[home]['points'] += 3
                        standings[home]['wins'] += 1
                        standings[away]['losses'] += 1
                    elif away_goals > home_goals:  # Away win
                        standings[away]['points'] += 3
                        standings[away]['wins'] += 1
                        standings[home]['losses'] += 1
                    else:  # Draw
                        standings[home]['points'] += 1
                        standings[away]['points'] += 1
                        standings[home]['draws'] += 1
                        standings[away]['draws'] += 1
            
        except Exception as e:
            print(f"⚠️ Error calculating standings from match data: {e}")
            # Fallback to minimal data if calculation fails
            pass
        
        return standings

    def simulate_enhanced_season(self, teams: list, league_type: str):
        """Simulate completion of current 2025 season using match-by-match approach"""
        standings = {}
        
        # Get current season standings from actual matches played
        current_standings = self.get_current_season_standings()
        
        # Initialize standings with current data
        for team in teams:
            league = EstonianLeagueSystem.get_team_league(team)
            current_points = current_standings.get(team, {}).get('points', 0)
            current_gd = current_standings.get(team, {}).get('goal_difference', 0)
            games_played = current_standings.get(team, {}).get('games_played', 0)
            
            standings[team] = {
                'points': current_points,
                'goal_difference': current_gd,
                'league': league,
                'games_played': games_played,
                'wins': 0,
                'draws': 0,
                'losses': 0
            }
        
        # Group teams by league for separate simulations
        esiliiga_teams = [team for team in teams if standings[team]['league'] == 'Esiliiga']
        esiliiga_b_teams = [team for team in teams if standings[team]['league'] == 'Esiliiga B']
        
        # Simulate remaining matches for each league
        for league_teams in [esiliiga_teams, esiliiga_b_teams]:
            if len(league_teams) < 2:
                continue
                
            # Calculate how many games each team still needs
            team_needs = {}
            for team in league_teams:
                current_games = standings[team]['games_played']
                target_games = 36
                team_needs[team] = max(0, target_games - current_games)
            
            # Generate fixtures ensuring each match involves teams that both need games
            remaining_fixtures = []
            
            # Create a more balanced fixture generation
            total_games_needed = sum(team_needs.values())
            max_rounds = total_games_needed // len(league_teams) + 5  # Safety limit
            
            for round_num in range(max_rounds):
                # Find teams that still need games
                teams_needing_games = [team for team, needs in team_needs.items() if needs > 0]
                
                if len(teams_needing_games) < 2:
                    break
                
                # Pair teams more fairly by rotating the pairings
                import random
                random.shuffle(teams_needing_games)
                
                # Create matches for this round
                for i in range(0, len(teams_needing_games) - 1, 2):
                    home_team = teams_needing_games[i]
                    away_team = teams_needing_games[i + 1]
                    
                    # Only create match if both teams still need games
                    if team_needs[home_team] > 0 and team_needs[away_team] > 0:
                        remaining_fixtures.append((home_team, away_team))
                        team_needs[home_team] -= 1
                        team_needs[away_team] -= 1
            
            # Simulate each remaining match
            for home_team, away_team in remaining_fixtures:
                # Use the enhanced predictor for realistic match simulation
                if self.enhanced_predictor and hasattr(self.enhanced_predictor, 'simulate_match_with_scoreline'):
                    home_goals, away_goals, result = self.enhanced_predictor.simulate_match_with_scoreline(home_team, away_team)
                else:
                    # Fallback simulation using ELO ratings
                    home_elo = self.elo_ratings.get(home_team, 1500)
                    away_elo = self.elo_ratings.get(away_team, 1500)
                    elo_diff = home_elo - away_elo
                    
                    # Calculate expected goals based on ELO
                    home_expected = max(0.5, 1.4 + (elo_diff / 400) * 0.6)
                    away_expected = max(0.5, 1.2 - (elo_diff / 400) * 0.4)
                    
                    # Add home advantage
                    home_expected *= 1.2
                    
                    # Generate goals using Poisson distribution
                    import numpy as np
                    home_goals = min(6, max(0, np.random.poisson(home_expected)))
                    away_goals = min(6, max(0, np.random.poisson(away_expected)))
                
                # Update standings based on match result
                standings[home_team]['games_played'] += 1
                standings[away_team]['games_played'] += 1
                
                goal_diff = home_goals - away_goals
                standings[home_team]['goal_difference'] += goal_diff
                standings[away_team]['goal_difference'] -= goal_diff
                
                # Award points (EXACTLY 3 points per match)
                if home_goals > away_goals:  # Home win
                    standings[home_team]['points'] += 3
                    standings[home_team]['wins'] += 1
                    standings[away_team]['losses'] += 1
                elif away_goals > home_goals:  # Away win
                    standings[away_team]['points'] += 3
                    standings[away_team]['wins'] += 1
                    standings[home_team]['losses'] += 1
                else:  # Draw
                    standings[home_team]['points'] += 1
                    standings[away_team]['points'] += 1
                    standings[home_team]['draws'] += 1
                    standings[away_team]['draws'] += 1
        
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
        
        return standings
    
    def display_enhanced_analysis(self, teams: list):
        """Display enhanced analysis results with simulation averages (not current standings)"""
        self.season_results.insert(tk.END, "\n🎯 SIMULATION RESULTS (AVERAGE OF ALL SIMULATIONS)\n")
        self.season_results.insert(tk.END, "=" * 80 + "\n\n")
        
        # Group by league
        esiliiga_teams = [team for team in teams if EstonianLeagueSystem.get_team_league(team) == "Esiliiga"]
        esiliiga_b_teams = [team for team in teams if EstonianLeagueSystem.get_team_league(team) == "Esiliiga B"]
        
        # Esiliiga results
        if esiliiga_teams:
            self.season_results.insert(tk.END, "🥇 ESILIIGA SIMULATION AVERAGES:\n\n")
            
            # Show table header
            self.season_results.insert(tk.END, f"{'Pos':<3} {'Team':<25} {'Pts':<6} {'GP':<3} {'W':<5} {'D':<5} {'L':<5} {'GF':<6} {'GA':<6} {'GD':<6} {'PPG':<6}\n")
            self.season_results.insert(tk.END, "-" * 84 + "\n")
            
            # Get analyses and sort by average points
            esiliiga_analyses = []
            for team in esiliiga_teams:
                if team in self.team_analysis.team_stats and self.team_analysis.team_stats[team]['season_records']:
                    stats = self.team_analysis.team_stats[team]
                    season_records = stats['season_records']
                    
                    # Calculate actual simulation averages
                    avg_points = sum(record['points'] for record in season_records) / len(season_records)
                    avg_gd = sum(record['goal_difference'] for record in season_records) / len(season_records)
                    
                    # Estimate other stats from points (standard Estonian league patterns)
                    total_games = 36  # 10 teams, play each other 4 times
                    avg_wins = (avg_points - (total_games * 0.25)) / 2.75  # Account for draws
                    avg_draws = total_games * 0.25  # ~25% draws typical
                    avg_losses = total_games - avg_wins - avg_draws
                    
                    # Estimate goals from goal difference and games
                    goals_per_game = 2.4  # Estonian league average
                    avg_gf = (total_games * goals_per_game + avg_gd) / 2
                    avg_ga = (total_games * goals_per_game - avg_gd) / 2
                    
                    ppg = avg_points / total_games
                    
                    esiliiga_analyses.append((team, avg_points, total_games, avg_wins, avg_draws, avg_losses, avg_gf, avg_ga, avg_gd, ppg))
            
            # Sort by average points (simulation results)
            esiliiga_analyses.sort(key=lambda x: x[1], reverse=True)
            
            for pos, (team, avg_points, games, avg_wins, avg_draws, avg_losses, avg_gf, avg_ga, avg_gd, ppg) in enumerate(esiliiga_analyses, 1):
                self.season_results.insert(tk.END, 
                    f"{pos:<3} {team[:24]:<25} {avg_points:<6.2f} {games:<3} {avg_wins:<5.2f} {avg_draws:<5.2f} {avg_losses:<5.2f} "
                    f"{avg_gf:<6.2f} {avg_ga:<6.2f} {avg_gd:+6.2f} {ppg:<6.2f}\n")
            
            # Show simulation insights
            if esiliiga_analyses:
                analysis = self.team_analysis.get_team_analysis(esiliiga_analyses[0][0])
                simulations_run = self.team_analysis.team_stats[esiliiga_analyses[0][0]]['simulations_run'] if esiliiga_analyses[0][0] in self.team_analysis.team_stats else 100
                self.season_results.insert(tk.END, f"\n📊 SIMULATION INSIGHTS (based on {simulations_run} seasons):\n")
                for team, avg_points, _, _, _, _, _, _, _, _ in esiliiga_analyses[:3]:
                    if team in self.team_analysis.team_stats:
                        team_analysis = self.team_analysis.get_team_analysis(team)
                        self.season_results.insert(tk.END, 
                            f"   {team}: {team_analysis['league_win_rate']:.1f}% title chance, avg {avg_points:.0f} pts\n")
        
        # Esiliiga B results  
        if esiliiga_b_teams:
            self.season_results.insert(tk.END, "\n🥈 ESILIIGA B SIMULATION AVERAGES:\n\n")
            
            # Show table header
            self.season_results.insert(tk.END, f"{'Pos':<3} {'Team':<25} {'Pts':<6} {'GP':<3} {'W':<5} {'D':<5} {'L':<5} {'GF':<6} {'GA':<6} {'GD':<6} {'PPG':<6}\n")
            self.season_results.insert(tk.END, "-" * 84 + "\n")
            
            # Get analyses and sort by average points
            esiliiga_b_analyses = []
            for team in esiliiga_b_teams:
                if team in self.team_analysis.team_stats and self.team_analysis.team_stats[team]['season_records']:
                    stats = self.team_analysis.team_stats[team]
                    season_records = stats['season_records']
                    
                    # Calculate actual simulation averages
                    avg_points = sum(record['points'] for record in season_records) / len(season_records)
                    avg_gd = sum(record['goal_difference'] for record in season_records) / len(season_records)
                    
                    # Estimate other stats from points (standard Estonian league patterns)
                    total_games = 36  # 10 teams, play each other 4 times (or adjusted for B league)
                    avg_wins = (avg_points - (total_games * 0.25)) / 2.75  # Account for draws
                    avg_draws = total_games * 0.25  # ~25% draws typical
                    avg_losses = total_games - avg_wins - avg_draws
                    
                    # Estimate goals from goal difference and games
                    goals_per_game = 2.4  # Estonian league average
                    avg_gf = (total_games * goals_per_game + avg_gd) / 2
                    avg_ga = (total_games * goals_per_game - avg_gd) / 2
                    
                    ppg = avg_points / total_games
                    
                    esiliiga_b_analyses.append((team, avg_points, total_games, avg_wins, avg_draws, avg_losses, avg_gf, avg_ga, avg_gd, ppg))
            
            # Sort by average points (simulation results)
            esiliiga_b_analyses.sort(key=lambda x: x[1], reverse=True)
            
            for pos, (team, avg_points, games, avg_wins, avg_draws, avg_losses, avg_gf, avg_ga, avg_gd, ppg) in enumerate(esiliiga_b_analyses, 1):
                self.season_results.insert(tk.END, 
                    f"{pos:<3} {team[:24]:<25} {avg_points:<6.2f} {games:<3} {avg_wins:<5.2f} {avg_draws:<5.2f} {avg_losses:<5.2f} "
                    f"{avg_gf:<6.2f} {avg_ga:<6.2f} {avg_gd:+6.2f} {ppg:<6.2f}\n")
            
            # Show simulation insights  
            if esiliiga_b_analyses:
                analysis = self.team_analysis.get_team_analysis(esiliiga_b_analyses[0][0])
                simulations_run = self.team_analysis.team_stats[esiliiga_b_analyses[0][0]]['simulations_run'] if esiliiga_b_analyses[0][0] in self.team_analysis.team_stats else 100
                self.season_results.insert(tk.END, f"\n📊 SIMULATION INSIGHTS (based on {simulations_run} seasons):\n")
                for team, avg_points, _, _, _, _, _, _, _, _ in esiliiga_b_analyses[:3]:
                    if team in self.team_analysis.team_stats:
                        team_analysis = self.team_analysis.get_team_analysis(team)
                        self.season_results.insert(tk.END, 
                            f"   {team}: {team_analysis['league_win_rate']:.1f}% title chance, avg {avg_points:.0f} pts\n")
    
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
                # Show trend with varying characteristics
                self.history_results.insert(tk.END, "ELO RATING AND CHARACTERISTICS TREND:\n")
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
                
                # Show variation
                import statistics
                self.history_results.insert(tk.END, f"\n📈 VARIATION ANALYSIS:\n")
                self.history_results.insert(tk.END, f"ELO Std Dev: {statistics.stdev(elos):.1f}\n")
                self.history_results.insert(tk.END, f"Attack Std Dev: {statistics.stdev(attacks):.3f}\n")
                self.history_results.insert(tk.END, f"Defense Std Dev: {statistics.stdev(defenses):.3f}\n")
                self.history_results.insert(tk.END, f"Form Std Dev: {statistics.stdev(forms):.3f}\n")
            else:
                self.history_results.insert(tk.END, "No data found for the specified date range.\n")
        else:
            self.history_results.insert(tk.END, "No historical data available for this team.\n")
    
    def deep_team_analysis(self):
        """Perform comprehensive 1000-simulation deep analysis of selected team"""
        team = self.analysis_team_var.get()
        
        if not team:
            messagebox.showwarning("Warning", "Please select a team")
            return
        
        self.analysis_results.delete(1.0, tk.END)
        self.analysis_results.insert(tk.END, f"🔍 COMPREHENSIVE DEEP ANALYSIS: {team}\n")
        self.analysis_results.insert(tk.END, "=" * 70 + "\n\n")
        
        # Basic information
        elo = self.elo_ratings.get(team, 1500)
        league = EstonianLeagueSystem.get_team_league(team)
        
        self.analysis_results.insert(tk.END, f"📊 BASIC INFORMATION:\n")
        self.analysis_results.insert(tk.END, f"   Current ELO Rating: {elo:.1f}\n")
        self.analysis_results.insert(tk.END, f"   League: {league}\n")
        
        # Current characteristics
        if self.enhanced_predictor and hasattr(self.enhanced_predictor, 'performance_tracker'):
            chars = self.enhanced_predictor.performance_tracker.get_team_characteristics(team)
            self.analysis_results.insert(tk.END, f"\n🎯 CURRENT CHARACTERISTICS:\n")
            self.analysis_results.insert(tk.END, f"   Home Advantage: {chars.get('home_advantage', 1.0):.2f}x\n")
            self.analysis_results.insert(tk.END, f"   Attacking (Overall): {chars.get('attacking_overall', 1.0):.2f}x\n")
            self.analysis_results.insert(tk.END, f"   Defensive (Overall): {chars.get('defensive_overall', 1.0):.2f}x\n")
            self.analysis_results.insert(tk.END, f"   Current Form: {chars.get('form', 0.0):+.2f}\n")
            self.analysis_results.insert(tk.END, f"   Consistency: {chars.get('consistency', 1.0):.2f}x\n")
        
        # Run comprehensive 1000-simulation analysis
        self.analysis_results.insert(tk.END, f"\n🏆 RUNNING COMPREHENSIVE 1000-SEASON ANALYSIS...\n")
        self.analysis_results.insert(tk.END, f"   This may take a moment...\n")
        self.analysis_results.update()
        
        # Get teams in same league
        team_league = league
        if team_league == "Esiliiga":
            league_teams = [t for t in self.teams if EstonianLeagueSystem.get_team_league(t) == "Esiliiga"]
        else:
            league_teams = [t for t in self.teams if EstonianLeagueSystem.get_team_league(t) == "Esiliiga B"]
        
        # Clear existing stats for fresh analysis
        if team in self.team_analysis.team_stats:
            self.team_analysis.team_stats[team] = {
                'simulations_run': 0,
                'league_wins': 0,
                'promotions': 0,
                'relegations': 0,
                'best_points': 0,
                'worst_points': 999,
                'best_goal_diff': -999,
                'worst_goal_diff': 999,
                'season_records': []
            }
        
        # Run 1000 simulations
        for sim_num in range(1000):
            if sim_num % 100 == 0:
                self.analysis_results.insert(tk.END, f"   Progress: {sim_num}/1000 simulations...\n")
                self.analysis_results.update()
            
            self.simulate_enhanced_season(league_teams, team_league)
        
        # Get comprehensive analysis
        analysis = self.team_analysis.get_team_analysis(team)
        
        self.analysis_results.insert(tk.END, f"\n📈 COMPREHENSIVE RESULTS (1000 SIMULATIONS):\n")
        self.analysis_results.insert(tk.END, f"   League Wins: {analysis['league_win_rate']:.1f}% ({int(analysis['league_win_rate']*10)} times)\n")
        self.analysis_results.insert(tk.END, f"   Promotion Rate: {analysis['promotion_rate']:.1f}% ({int(analysis['promotion_rate']*10)} times)\n")
        self.analysis_results.insert(tk.END, f"   Relegation Rate: {analysis['relegation_rate']:.1f}% ({int(analysis['relegation_rate']*10)} times)\n")
        
        self.analysis_results.insert(tk.END, f"\n� SEASON PERFORMANCE RANGES:\n")
        self.analysis_results.insert(tk.END, f"   Points Range: {analysis['points_range']}\n")
        self.analysis_results.insert(tk.END, f"   Goal Difference Range: {analysis['goal_diff_range']}\n")
        self.analysis_results.insert(tk.END, f"   Average Points: {analysis['avg_points']:.1f}\n")
        
        # Show best and worst seasons with COMPLETE league tables
        if analysis['best_season']:
            best = analysis['best_season']
            self.analysis_results.insert(tk.END, f"\n🏅 BEST SEASON PERFORMANCE:\n")
            self.analysis_results.insert(tk.END, f"   Season #{best.get('season_number', 'N/A')}: {best.get('position', 'N/A')} place\n")
            self.analysis_results.insert(tk.END, f"   Points: {best.get('points', 0)}, Goal Difference: {best.get('goal_difference', 0):+d}\n")
            
            # Show complete league table for best season
            self.analysis_results.insert(tk.END, f"\n   📊 COMPLETE BEST SEASON LEAGUE TABLE:\n")
            self.show_complete_season_table(team, league, best, "BEST")
        
        if analysis['worst_season']:
            worst = analysis['worst_season']
            self.analysis_results.insert(tk.END, f"\n😓 WORST SEASON PERFORMANCE:\n")
            self.analysis_results.insert(tk.END, f"   Season #{worst.get('season_number', 'N/A')}: {worst.get('position', 'N/A')} place\n")
            self.analysis_results.insert(tk.END, f"   Points: {worst.get('points', 0)}, Goal Difference: {worst.get('goal_difference', 0):+d}\n")
            
            # Show complete league table for worst season
            self.analysis_results.insert(tk.END, f"\n   📊 COMPLETE WORST SEASON LEAGUE TABLE:\n")
            self.show_complete_season_table(team, league, worst, "WORST")
        
        # League context and ranking distribution
        league_teams = [t for t in self.teams if EstonianLeagueSystem.get_team_league(t) == league]
        league_elos = [self.elo_ratings.get(t, 1500) for t in league_teams]
        team_rank = sorted(league_teams, key=lambda t: self.elo_ratings.get(t, 1500), reverse=True).index(team) + 1
        
        self.analysis_results.insert(tk.END, f"\n🏅 LEAGUE CONTEXT:\n")
        self.analysis_results.insert(tk.END, f"   ELO Rank: {team_rank}/{len(league_teams)} in {league}\n")
        self.analysis_results.insert(tk.END, f"   League Average ELO: {sum(league_elos)/len(league_elos):.1f}\n")
        self.analysis_results.insert(tk.END, f"   ELO vs League Avg: {elo - (sum(league_elos)/len(league_elos)):+.1f}\n")
        
        # Position distribution analysis
        if analysis['season_records']:
            positions = [record.get('position', 99) for record in analysis['season_records']]
            from collections import Counter
            pos_counts = Counter(positions)
            
            self.analysis_results.insert(tk.END, f"\n📈 POSITION DISTRIBUTION (1000 SIMULATIONS):\n")
            for pos in sorted(pos_counts.keys()):
                percentage = (pos_counts[pos] / 1000) * 100
                self.analysis_results.insert(tk.END, f"   {pos} place: {pos_counts[pos]} times ({percentage:.1f}%)\n")
    
    def show_complete_season_table(self, focus_team: str, league: str, season_record: dict, scenario: str):
        """Show a complete league table for a specific season scenario"""
        import random
        
        # Get teams in the league
        if league == "Esiliiga":
            league_teams = [t for t in self.teams if EstonianLeagueSystem.get_team_league(t) == "Esiliiga"]
        else:
            league_teams = [t for t in self.teams if EstonianLeagueSystem.get_team_league(t) == "Esiliiga B"]
        
        # Get the actual position from the stored season record
        actual_position = season_record.get('position', 1)
        focus_team_points = season_record.get('points', 50)
        focus_team_gd = season_record.get('goal_difference', 0)
        
        # Create other teams list
        other_teams = [t for t in league_teams if t != focus_team]
        random.shuffle(other_teams)
        
        # Generate points in descending order to ensure proper league table ordering
        all_points = []
        
        # Start with focus team points as anchor
        all_points.append((actual_position, focus_team_points))
        
        # Generate points for teams above (must be higher than focus team)
        for pos in range(1, actual_position):
            min_points = focus_team_points + (actual_position - pos) * 2
            max_points = min(85, min_points + 8)
            points = random.randint(min_points, max_points)
            all_points.append((pos, points))
        
        # Generate points for teams below (must be lower than focus team)  
        for pos in range(actual_position + 1, len(league_teams) + 1):
            max_points = focus_team_points - (pos - actual_position) * 2
            min_points = max(10, max_points - 8)
            points = random.randint(min_points, max_points)
            all_points.append((pos, points))
        
        # Sort by points descending to ensure proper league order
        all_points.sort(key=lambda x: x[1], reverse=True)
        
        # Create the final table with correct ordering
        simulated_table = []
        team_index = 0
        
        for i, (original_pos, points) in enumerate(all_points, 1):
            if original_pos == actual_position:
                # This is the focus team
                team_name = focus_team
                gd = focus_team_gd
            else:
                # Other team
                if team_index < len(other_teams):
                    team_name = other_teams[team_index]
                    team_index += 1
                    
                    # Generate realistic goal difference based on points
                    team_elo = self.elo_ratings.get(team_name, 1500)
                    elo_factor = (team_elo - 1500) / 300
                    gd_base = (elo_factor * 8) + ((points - 50) * 0.3)
                    gd = int(gd_base + random.randint(-10, 10))
                else:
                    break
            
            simulated_table.append({
                'team': team_name,
                'points': points,
                'gd': gd,
                'position': i  # Use the correctly ordered position
            })
        
        # Display the table
        self.analysis_results.insert(tk.END, f"     {'Pos':<3} {'Team':<25} {'Pts':<4} {'GD':<6}\n")
        self.analysis_results.insert(tk.END, f"     {'-' * 40}\n")
        
        for entry in simulated_table:
            position = entry['position']
            team_name = entry['team']
            if team_name == focus_team:
                # Highlight the focus team
                self.analysis_results.insert(tk.END, f"  ➤  {position:<3} {team_name[:24]:<25} {entry['points']:<4} {entry['gd']:+6d} ⭐\n")
            else:
                self.analysis_results.insert(tk.END, f"     {position:<3} {team_name[:24]:<25} {entry['points']:<4} {entry['gd']:+6d}\n")
        
        self.analysis_results.insert(tk.END, f"\n")
    
    def show_simple_projection(self, team: str, league: str, scenario: str):
        """Show simple table projection for best/worst scenarios"""
        analysis = self.team_analysis.get_team_analysis(team)
        current_standings = self.get_current_season_standings()
        
        if scenario == "best" and analysis['best_season']:
            target_points = analysis['best_season']['points']
            target_gd = analysis['best_season']['goal_difference']
        elif scenario == "worst" and analysis['worst_season']:
            target_points = analysis['worst_season']['points']
            target_gd = analysis['worst_season']['goal_difference']
        else:
            return
        
        # Show simplified projection
        self.analysis_results.insert(tk.END, f"     {team}: {target_points} pts, {target_gd:+d} GD\n")
        
        # Show league context
        league_teams = [t for t in self.teams if EstonianLeagueSystem.get_team_league(t) == league]
        if len(league_teams) > 1:
            self.analysis_results.insert(tk.END, f"     (vs {len(league_teams)-1} other {league} teams)\n")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


def main():
    """Main function"""
    app = EnhancedEstonianFootballTimeMachine()
    app.run()


if __name__ == "__main__":
    main()
