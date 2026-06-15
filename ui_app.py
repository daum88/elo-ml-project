#!/usr/bin/env python3
"""
Estonian Football League Simulator
Predicts final league tables using Monte Carlo simulation with league-calibrated ELO.
Data: 1997-2025, 29 seasons, 3 leagues, 11,000+ matches.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from datetime import datetime
from collections import defaultdict
from predictor import DataLoader, ELOEngine


class LeagueSimulator:
    def __init__(self):
        self.loader = DataLoader()
        for fn, lg in [('premium_liiga','PL'),('esiliiga','ESL'),('esiliiga_b','ESB')]:
            for yr in ['2022','2023','2024','2025']:
                self.loader.load_csv(f'data/{fn}_{yr}.csv', lg)
        self.all_matches = [m for m in self.loader.sorted_matches() if m['date'].year >= 2022]
        self.team_league_map = {}
        for m in self.all_matches:
            y = m['date'].year
            if 'league' in m:
                self.team_league_map[(m['home'], y)] = m['league']
                self.team_league_map[(m['away'], y)] = m['league']
        self.cutoff = datetime(2025, 9, 1)
        train = [m for m in self.all_matches if m['date'] < self.cutoff]
        t2025 = [m for m in train if m['date'] >= datetime(2025, 1, 1)]
        dr = sum(1 for m in t2025 if m['home_goals'] == m['away_goals']) / max(1, len(t2025))
        self.elo = ELOEngine(k_factor=20, home_advantage=50, draw_rate=dr)
        self.elo.fit_with_league_awareness(train, self.team_league_map)
        self.teams = sorted(set(m['home'] for m in self.all_matches) | set(m['away'] for m in self.all_matches))
        self.last_results = None; self.last_sim_records = None
        self.last_game_logs = None; self.last_n_sims = None; self.last_league = None

    def sim_match(self, home, away):
        hg, ag = self.elo.expected_goals(home, away)
        return min(np.random.poisson(hg), 8), min(np.random.poisson(ag), 8)

    def get_league_data(self, year, league):
        teams = set(); matches = []
        for m in self.all_matches:
            if m['date'].year != year: continue
            if self.team_league_map.get((m['home'], year)) == league:
                teams.add(m['home']); teams.add(m['away']); matches.append(m)
        return teams, matches

    def build_standings(self, teams, played):
        s = {t: {'pts': 0, 'gd': 0, 'gf': 0, 'ga': 0, 'gp': 0, 'w': 0, 'd': 0, 'l': 0} for t in teams}
        for m in played:
            h, a = m['home'], m['away']; gd = m['home_goals'] - m['away_goals']
            s[h]['gf'] += m['home_goals']; s[h]['ga'] += m['away_goals']; s[h]['gp'] += 1; s[h]['gd'] += gd
            s[a]['gf'] += m['away_goals']; s[a]['ga'] += m['home_goals']; s[a]['gp'] += 1; s[a]['gd'] -= gd
            if gd > 0: s[h]['pts'] += 3; s[h]['w'] += 1; s[a]['l'] += 1
            elif gd < 0: s[a]['pts'] += 3; s[a]['w'] += 1; s[h]['l'] += 1
            else: s[h]['pts'] += 1; s[a]['pts'] += 1; s[h]['d'] += 1; s[a]['d'] += 1
        return s

    def generate_fixtures(self, teams, played):
        required = {}
        tl = list(teams)
        for i, h in enumerate(tl):
            for a in tl[i+1:]: required[(min(h,a), max(h,a))] = 4
        for m in played:
            key = (min(m['home'],m['away']), max(m['home'],m['away']))
            if key in required: required[key] = max(0, required[key]-1)
        fixtures = []
        for (t1, t2), count in required.items():
            for _ in range(count):
                fixtures.append((t1, t2) if np.random.random() < 0.5 else (t2, t1))
        np.random.shuffle(fixtures)
        return fixtures

    def run_simulation(self, league_code, n_sims=1000):
        teams, matches = self.get_league_data(2025, league_code)
        played = [m for m in matches if m['date'] < self.cutoff]
        base = self.build_standings(teams, played)
        n_teams = len(teams)
        if n_teams < 4: return None

        sim_records = {t: [] for t in teams}
        all_game_logs = []

        for _ in range(n_sims):
            s = {t: dict(base[t]) for t in teams}
            fixtures = self.generate_fixtures(teams, played)
            game_log = []
            for h, a in fixtures:
                hg, ag = self.sim_match(h, a)
                s[h]['gp'] += 1; s[a]['gp'] += 1
                s[h]['gf'] += hg; s[h]['ga'] += ag; s[a]['gf'] += ag; s[a]['ga'] += hg
                gd = hg - ag; s[h]['gd'] += gd; s[a]['gd'] -= gd
                if hg > ag: s[h]['pts'] += 3; s[h]['w'] += 1; s[a]['l'] += 1
                elif ag > hg: s[a]['pts'] += 3; s[a]['w'] += 1; s[h]['l'] += 1
                else: s[h]['pts'] += 1; s[a]['pts'] += 1; s[h]['d'] += 1; s[a]['d'] += 1
                game_log.append((h, a, hg, ag))

            table = sorted(teams, key=lambda t: (-s[t]['pts'], -s[t]['gd'], -s[t]['gf']))
            for pos, t in enumerate(table, 1):
                sim_records[t].append({'pos': pos, 'pts': s[t]['pts'], 'gd': s[t]['gd'],
                    'gf': s[t]['gf'], 'ga': s[t]['ga'], 'gp': s[t]['gp'],
                    'w': s[t]['w'], 'd': s[t]['d'], 'l': s[t]['l']})
            all_game_logs.append(game_log)

        avg_pos = {t: np.mean([r['pos'] for r in sim_records[t]]) for t in teams}
        sorted_teams = sorted(teams, key=lambda t: avg_pos[t])

        self.last_results = sorted_teams; self.last_sim_records = sim_records
        self.last_game_logs = all_game_logs; self.last_n_sims = n_sims
        self.last_league = league_code; self.last_teams = teams
        return sorted_teams, sim_records, base, n_sims, teams

    def get_historic_teams(self, year, league_code):
        """Get all teams that played in a given league in a given year."""
        teams = set()
        for m in self.all_matches:
            if m['date'].year == year:
                lg = self.team_league_map.get((m['home'], year))
                if lg == league_code:
                    teams.add(m['home']); teams.add(m['away'])
        return sorted(teams)

    def get_all_historic_teams(self):
        """Get all unique team names ever."""
        return sorted(set(m['home'] for m in self.all_matches) | set(m['away'] for m in self.all_matches))

    def replay_season(self, year, league_code, n_sims=1000):
        """Replay a full historic season from scratch."""
        teams = self.get_historic_teams(year, league_code)
        if len(teams) < 4: return None

        sim_records = {t: [] for t in teams}
        for _ in range(n_sims):
            s = {t: {'pts': 0, 'gd': 0, 'gf': 0, 'ga': 0, 'gp': 0, 'w': 0, 'd': 0, 'l': 0} for t in teams}
            fixtures = self.generate_fixtures(teams, [])
            for h, a in fixtures:
                hg, ag = self.sim_match(h, a)
                s[h]['gp'] += 1; s[a]['gp'] += 1
                s[h]['gf'] += hg; s[h]['ga'] += ag; s[a]['gf'] += ag; s[a]['ga'] += hg
                gd = hg - ag; s[h]['gd'] += gd; s[a]['gd'] -= gd
                if hg > ag: s[h]['pts'] += 3; s[h]['w'] += 1; s[a]['l'] += 1
                elif ag > hg: s[a]['pts'] += 3; s[a]['w'] += 1; s[h]['l'] += 1
                else: s[h]['pts'] += 1; s[a]['pts'] += 1; s[h]['d'] += 1; s[a]['d'] += 1

            table = sorted(teams, key=lambda t: (-s[t]['pts'], -s[t]['gd'], -s[t]['gf']))
            for pos, t in enumerate(table, 1):
                sim_records[t].append({'pos': pos, 'pts': s[t]['pts'], 'gd': s[t]['gd'],
                    'gf': s[t]['gf'], 'ga': s[t]['ga'], 'gp': s[t]['gp'],
                    'w': s[t]['w'], 'd': s[t]['d'], 'l': s[t]['l']})

        avg_pos = {t: np.mean([r['pos'] for r in sim_records[t]]) for t in teams}
        self.last_results = sorted(teams, key=lambda t: avg_pos[t])
        self.last_sim_records = sim_records; self.last_n_sims = n_sims
        self.last_league = league_code; self.last_teams = teams
        return self.last_results, sim_records, None, n_sims, teams

    def sim_custom_league(self, teams, n_sims=1000):
        """Simulate a custom league with any set of teams."""
        if len(teams) < 3: return None
        sim_records = {t: [] for t in teams}
        for _ in range(n_sims):
            s = {t: {'pts': 0, 'gd': 0, 'gf': 0, 'ga': 0, 'gp': 0, 'w': 0, 'd': 0, 'l': 0} for t in teams}
            fixtures = self.generate_fixtures(teams, [])
            for h, a in fixtures:
                hg, ag = self.sim_match(h, a)
                s[h]['gp'] += 1; s[a]['gp'] += 1
                s[h]['gf'] += hg; s[h]['ga'] += ag; s[a]['gf'] += ag; s[a]['ga'] += hg
                gd = hg - ag; s[h]['gd'] += gd; s[a]['gd'] -= gd
                if hg > ag: s[h]['pts'] += 3; s[h]['w'] += 1; s[a]['l'] += 1
                elif ag > hg: s[a]['pts'] += 3; s[a]['w'] += 1; s[h]['l'] += 1
                else: s[h]['pts'] += 1; s[a]['pts'] += 1; s[h]['d'] += 1; s[a]['d'] += 1

            table = sorted(teams, key=lambda t: (-s[t]['pts'], -s[t]['gd'], -s[t]['gf']))
            for pos, t in enumerate(table, 1):
                sim_records[t].append({'pos': pos, 'pts': s[t]['pts'], 'gd': s[t]['gd'],
                    'gf': s[t]['gf'], 'ga': s[t]['ga'], 'gp': s[t]['gp'],
                    'w': s[t]['w'], 'd': s[t]['d'], 'l': s[t]['l']})

        return sim_records, n_sims


class SimulatorUI:
    def __init__(self):
        self.sim = LeagueSimulator()
        self.root = tk.Tk()
        self.root.title("Estonian Football League Simulator")
        self.root.geometry("1300x900")
        self.root.configure(bg='#1a1a2e')
        self._apply_theme()
        self._build()
        self.root.mainloop()

    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        bg = '#1a1a2e'; fg = '#e0e0e0'; accent = '#e94560'; accent2 = '#0f3460'
        style.configure('TFrame', background=bg)
        style.configure('TLabel', background=bg, foreground=fg, font=('Segoe UI', 10))
        style.configure('TButton', background=accent2, foreground=fg, font=('Segoe UI', 10, 'bold'), padding=8)
        style.map('TButton', background=[('active', accent)])
        style.configure('TCombobox', fieldbackground='#16213e', foreground=fg, font=('Segoe UI', 10))
        style.configure('TNotebook', background=bg)
        style.configure('TNotebook.Tab', background='#16213e', foreground=fg, font=('Segoe UI', 10, 'bold'), padding=[12, 6])
        style.map('TNotebook.Tab', background=[('selected', accent2)], foreground=[('selected', '#ffffff')])
        style.configure('TLabelframe', background=bg, foreground=fg)
        style.configure('TLabelframe.Label', background=bg, foreground=accent, font=('Segoe UI', 11, 'bold'))
        style.configure('Treeview', background='#16213e', foreground=fg, fieldbackground='#16213e', font=('Consolas', 10), rowheight=26)
        style.configure('Treeview.Heading', background=accent2, foreground='#ffffff', font=('Segoe UI', 9, 'bold'))
        style.map('Treeview', background=[('selected', accent)])
        style.configure('Accent.TButton', background=accent, foreground='white', font=('Segoe UI', 10, 'bold'), padding=10)
        style.map('Accent.TButton', background=[('active', '#ff6b81')])
        style.configure('TProgressbar', background=accent, troughcolor='#16213e')

    def _build(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        for name, builder in [("League Tables", self._build_league_tab),
                               ("Match Prediction", self._build_match_tab),
                               ("Team Deep Analysis", self._build_team_tab),
                               ("Season Browser", self._build_season_tab),
                               ("What-If Scenarios", self._build_whatif_tab)]:
            tab = ttk.Frame(nb); nb.add(tab, text=name); builder(tab)

    def _build_league_tab(self, parent=None):
        if parent is None: parent = self.league_tab
        ctrl = ttk.Frame(parent, padding="10"); ctrl.pack(fill=tk.X)
        ttk.Label(ctrl, text="Simulations:").pack(side=tk.LEFT, padx=5)
        self.sim_count = tk.StringVar(value="1000")
        ttk.Combobox(ctrl, textvariable=self.sim_count, values=["100","500","1000","2000","5000","10000"], width=7).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="Run All Leagues", style='Accent.TButton', command=self._run_league).pack(side=tk.LEFT, padx=15)
        self.league_status = ttk.Label(ctrl, text=""); self.league_status.pack(side=tk.LEFT, padx=10)

        self.league_notebook = ttk.Notebook(parent)
        self.league_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        for lg in ['PL', 'ESL', 'ESB']:
            frm = ttk.Frame(self.league_notebook)
            self.league_notebook.add(frm, text={'PL':'Premium Liiga','ESL':'Esiliiga','ESB':'Esiliiga B'}[lg])

    def _build_team_tab(self, parent=None):
        if parent is None: parent = self.team_tab
        ctrl = ttk.Frame(parent, padding="10"); ctrl.pack(fill=tk.X)
        ttk.Label(ctrl, text="Team:").pack(side=tk.LEFT, padx=5)
        self.team_var = tk.StringVar()
        ttk.Combobox(ctrl, textvariable=self.team_var, values=self.sim.teams, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Label(ctrl, text="Sims:").pack(side=tk.LEFT, padx=(20,5))
        self.team_sim_count = tk.StringVar(value="1000")
        ttk.Combobox(ctrl, textvariable=self.team_sim_count, values=["500","1000","2000","5000"], width=7).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="Analyze", style='Accent.TButton', command=self._team_analysis).pack(side=tk.LEFT, padx=15)
        self.team_status = ttk.Label(ctrl, text=""); self.team_status.pack(side=tk.LEFT, padx=10)
        self.team_output = tk.Text(parent, bg='#16213e', fg='#e0e0e0', insertbackground='white',
                                    font=('Consolas', 10), relief='flat', padx=10, pady=10)
        self.team_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _build_match_tab(self, parent=None):
        if parent is None: parent = self.match_tab
        frm = ttk.LabelFrame(parent, text="Predict Any Match", padding="15")
        frm.pack(fill=tk.X, padx=15, pady=10)
        ttk.Label(frm, text="Home:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.match_home = tk.StringVar()
        ttk.Combobox(frm, textvariable=self.match_home, values=self.sim.teams, width=28).grid(row=0, column=1, padx=5)
        ttk.Label(frm, text="Away:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.match_away = tk.StringVar()
        ttk.Combobox(frm, textvariable=self.match_away, values=self.sim.teams, width=28).grid(row=0, column=3, padx=5)
        ttk.Label(frm, text="Sims:").grid(row=0, column=4, padx=(25,5))
        self.match_sims = tk.StringVar(value="5000")
        ttk.Entry(frm, textvariable=self.match_sims, width=7).grid(row=0, column=5)
        ttk.Button(frm, text="Predict", style='Accent.TButton', command=self._predict_match).grid(row=0, column=6, padx=15)
        self.match_output = tk.Text(parent, bg='#16213e', fg='#e0e0e0', insertbackground='white',
                                     font=('Consolas', 10), relief='flat', padx=10, pady=10)
        self.match_output.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

    def _build_season_tab(self, parent=None):
        if parent is None: parent = self.season_tab
        ctrl = ttk.Frame(parent, padding="10"); ctrl.pack(fill=tk.X)
        ttk.Label(ctrl, text="League:").pack(side=tk.LEFT, padx=5)
        self.season_lg = tk.StringVar(value="PL")
        ttk.Combobox(ctrl, textvariable=self.season_lg, values=["PL","ESL","ESB"], width=4).pack(side=tk.LEFT, padx=5)
        ttk.Label(ctrl, text="Sims:").pack(side=tk.LEFT, padx=(20,5))
        self.season_sim_count = tk.StringVar(value="1000")
        ttk.Combobox(ctrl, textvariable=self.season_sim_count, values=["100","500","1000","2000","5000"], width=7).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="Run", style='Accent.TButton', command=self._run_season_sim).pack(side=tk.LEFT, padx=10)
        ttk.Label(ctrl, text="  Season #:").pack(side=tk.LEFT, padx=(20,5))
        self.season_num = tk.StringVar(value="1")
        ttk.Entry(ctrl, textvariable=self.season_num, width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(ctrl, text="Team:").pack(side=tk.LEFT, padx=5)
        self.season_team = tk.StringVar()
        ttk.Combobox(ctrl, textvariable=self.season_team, values=self.sim.teams, width=28).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="View Season", command=self._view_season).pack(side=tk.LEFT, padx=5)
        ttk.Button(ctrl, text="Extremes", command=self._show_extremes).pack(side=tk.LEFT, padx=5)
        self.season_status = ttk.Label(ctrl, text=""); self.season_status.pack(side=tk.LEFT, padx=10)
        self.season_output = tk.Text(parent, bg='#16213e', fg='#e0e0e0', insertbackground='white',
                                      font=('Consolas', 10), relief='flat', padx=10, pady=10)
        self.season_output.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # ─── LEAGUE TABLE ───
    def _run_league(self):
        try: n = int(self.sim_count.get())
        except: n = 1000
        self.league_status.config(text="Simulating..."); self.root.update()

        for lg_code, lg_name in [('PL','Premium Liiga'),('ESL','Esiliiga'),('ESB','Esiliiga B')]:
            result = self.sim.run_simulation(lg_code, n)
            if not result: continue
            sorted_teams, sim_records, base, n_sims, teams = result
            n_teams = len(teams)

            tab_idx = {'PL':0,'ESL':1,'ESB':2}[lg_code]
            tab = self.league_notebook.winfo_children()[tab_idx]
            for w in tab.winfo_children(): w.destroy()

            tree = ttk.Treeview(tab, columns=('pos','team','pts','pt_range','gd','gf','ga','champ','prom','rel'),
                                show='headings', height=12)
            tree.heading('pos', text='#'); tree.column('pos', width=30, anchor='center')
            tree.heading('team', text='Team'); tree.column('team', width=240)
            tree.heading('pts', text='AvgPts'); tree.column('pts', width=65, anchor='center')
            tree.heading('pt_range', text='Pts Range'); tree.column('pt_range', width=100, anchor='center')
            tree.heading('gd', text='AvgGD'); tree.column('gd', width=60, anchor='center')
            tree.heading('gf', text='GF/g'); tree.column('gf', width=55, anchor='center')
            tree.heading('ga', text='GA/g'); tree.column('ga', width=55, anchor='center')
            tree.heading('champ', text='Champ'); tree.column('champ', width=65, anchor='center')
            tree.heading('prom', text='Prom'); tree.column('prom', width=60, anchor='center')
            tree.heading('rel', text='Releg'); tree.column('rel', width=60, anchor='center')
            tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            for rank, t in enumerate(sorted_teams, 1):
                recs = sim_records[t]
                avg_pts = np.mean([r['pts'] for r in recs])
                mn, mx = np.min([r['pts'] for r in recs]), np.max([r['pts'] for r in recs])
                avg_gd = np.mean([r['gd'] for r in recs])
                avg_gf = np.mean([r['gf'] for r in recs]); avg_ga = np.mean([r['ga'] for r in recs])
                c = sum(1 for r in recs if r['pos']==1)/n_sims
                p = sum(1 for r in recs if r['pos']<=2)/n_sims
                rl = sum(1 for r in recs if r['pos']>=n_teams-1)/n_sims
                tags = ""
                if c>0.3: tags=" C"
                elif p>0.3: tags=" P"
                if rl>0.5: tags=" R"
                tree.insert('', 'end', values=(rank, f"{t} {tags}", f"{avg_pts:.1f}",
                    f"{mn:.0f} - {mx:.0f}", f"{avg_gd:+.1f}", f"{avg_gf:.1f}", f"{avg_ga:.1f}",
                    f"{c:.1%}", f"{p:.1%}", f"{rl:.1%}"))

            rules = { 'PL': '10th auto-relegated | 9th playoff vs Esiliiga 2nd',
                      'ESL': '1st auto-promoted, 2nd playoff vs PL 9th | 9-10th relegated, 8th playoff vs ESB 3rd',
                      'ESB': '1st-2nd auto-promoted, 3rd playoff vs Esiliiga 8th' }[lg_code]
            summary = ttk.Label(tab, text=f"{lg_name}: {n_sims:,} simulations | {rules} | C=Champ P=Prom R=Releg")
            summary.pack(pady=3)

        self.league_status.config(text=f"Done. {n:,} sims per league")

    # ─── TEAM DEEP ANALYSIS ───
    def _team_analysis(self):
        team = self.team_var.get()
        if not team: return
        try: n = int(self.team_sim_count.get())
        except: n = 1000
        self.team_status.config(text=f"Analyzing {team}..."); self.root.update()

        team_lg = self.sim.team_league_map.get((team,2025)) or self.sim.team_league_map.get((team,2024)) or 'ESL'
        result = self.sim.run_simulation(team_lg, n)
        if not result: return
        _, sim_records, _, n_sims, teams = result
        recs = sim_records[team]; out = self.team_output
        out.delete(1.0, tk.END)

        elo_val = self.sim.elo.ratings.get(team, 1500)
        pts = [r['pts'] for r in recs]; pos = [r['pos'] for r in recs]
        gd = [r['gd'] for r in recs]; gf = [r['gf'] for r in recs]; ga = [r['ga'] for r in recs]
        wins = [r['w'] for r in recs]; draws = [r['d'] for r in recs]; losses = [r['l'] for r in recs]
        lpos = sorted(teams, key=lambda t: np.mean([rr['pos'] for rr in sim_records[t]])).index(team)+1
        best = max(recs, key=lambda r: r['pts']); worst = min(recs, key=lambda r: r['pts'])

        out.insert(tk.END, f"\n  DEEP ANALYSIS: {team} ({team_lg})\n")
        out.insert(tk.END, f"  {'='*70}\n\n")
        out.insert(tk.END, f"  ELO: {elo_val:.0f}  |  Expected finish: {lpos}/{len(teams)}\n")
        out.insert(tk.END, f"  Projected: {np.mean(pts):.1f} pts | GD {np.mean(gd):+.1f} | GF/g {np.mean(gf):.1f} | GA/g {np.mean(ga):.1f}\n\n")
        out.insert(tk.END, f"  BEST SEASON:  {best['pos']}. place, {best['pts']} pts, W{best['w']}-D{best['d']}-L{best['l']}, GD {best['gd']:+d}, GF {best['gf']}\n")
        out.insert(tk.END, f"  WORST SEASON: {worst['pos']}. place, {worst['pts']} pts, W{worst['w']}-D{worst['d']}-L{worst['l']}, GD {worst['gd']:+d}, GF {worst['gf']}\n")
        out.insert(tk.END, f"  RECORDS: Wins {np.min(wins)}-{np.max(wins)} (avg {np.mean(wins):.1f}) | Draws {np.min(draws)}-{np.max(draws)} (avg {np.mean(draws):.1f}) | Losses {np.min(losses)}-{np.max(losses)} (avg {np.mean(losses):.1f})\n")

        out.insert(tk.END, f"\n  POSITION DISTRIBUTION:\n")
        pc = defaultdict(int)
        for p in pos: pc[p] += 1
        mx = max(pc.values())
        for p in sorted(pc.keys()):
            bar = "|" * int(50 * pc[p] / mx)
            out.insert(tk.END, f"    {p:2d}: {bar:<50} {pc[p]/n_sims:.1%} ({pc[p]})\n")

        out.insert(tk.END, f"\n  POINTS DISTRIBUTION:\n")
        pb = defaultdict(int)
        for p in pts: pb[int(p)//4*4] += 1
        mx = max(pb.values())
        for b in sorted(pb.keys()):
            bar = "|" * int(40 * pb[b] / mx)
            out.insert(tk.END, f"    {b:3d}-{b+3:3d}: {bar:<40} {pb[b]/n_sims:.1%}\n")

        # Game-based stats
        if self.sim.last_game_logs and self.sim.last_league == team_lg:
            all_logs = self.sim.last_game_logs
            big_wins = []; big_losses = []
            opp_stats = defaultdict(lambda: {'gf': 0, 'ga': 0, 'g': 0})
            total_gf = total_ga = total_g = 0

            for si, logs in enumerate(all_logs):
                for h, a, hg, ag in logs:
                    if h == team:
                        total_gf += hg; total_ga += ag; total_g += 1
                        opp_stats[a]['gf'] += hg; opp_stats[a]['ga'] += ag; opp_stats[a]['g'] += 1
                        if hg > ag: big_wins.append((hg-ag, a, f"{hg}-{ag}", si+1))
                        elif ag > hg: big_losses.append((ag-hg, a, f"{hg}-{ag}", si+1))
                    elif a == team:
                        total_gf += ag; total_ga += hg; total_g += 1
                        opp_stats[h]['gf'] += ag; opp_stats[h]['ga'] += hg; opp_stats[h]['g'] += 1
                        if ag > hg: big_wins.append((ag-hg, h, f"{ag}-{hg}", si+1))
                        elif hg > ag: big_losses.append((hg-ag, h, f"{hg}-{ag}", si+1))

            big_wins.sort(key=lambda x: -x[0]); big_losses.sort(key=lambda x: -x[0])

            out.insert(tk.END, f"\n  SIMULATED GAMES: {total_g:,} total | {total_gf/max(1,total_g):.2f} GF/g | {total_ga/max(1,total_g):.2f} GA/g\n")
            out.insert(tk.END, f"\n  BIGGEST WINS:\n")
            for margin, opp, score, sn in big_wins[:5]:
                out.insert(tk.END, f"    +{margin}  {score}  vs  {opp}  (season {sn})\n")
            out.insert(tk.END, f"\n  BIGGEST LOSSES:\n")
            for margin, opp, score, sn in big_losses[:5]:
                out.insert(tk.END, f"    -{margin}  {score}  vs  {opp}  (season {sn})\n")

            out.insert(tk.END, f"\n  PER-OPPONENT:\n")
            sorted_opp = sorted(opp_stats.items(), key=lambda x: -(x[1]['gf']/x[1]['g'] - x[1]['ga']/x[1]['g']))
            for opp, s in sorted_opp:
                g = s['g']; out.insert(tk.END, f"    vs {opp[:28]:<29} {s['gf']/g:.1f} GF  {s['ga']/g:.1f} GA  ({g} games)\n")

        self.team_status.config(text=f"Done - {team} analyzed over {n_sims:,} seasons")

    # ─── MATCH PREDICTION ───
    def _predict_match(self):
        h = self.match_home.get(); a = self.match_away.get()
        if not h or not a or h == a: return
        try: n = int(self.match_sims.get())
        except: n = 5000
        out = self.match_output; out.delete(1.0, tk.END)
        h_elo = self.sim.elo.ratings.get(h, 1500); a_elo = self.sim.elo.ratings.get(a, 1500)
        hg_xg, ag_xg = self.sim.elo.expected_goals(h, a)

        results = {'H':0,'D':0,'A':0}; scorelines = defaultdict(int); gh=ga=0
        for _ in range(n):
            hg, ag = self.sim.sim_match(h, a)
            if hg>ag: results['H']+=1
            elif ag>hg: results['A']+=1
            else: results['D']+=1
            scorelines[(hg,ag)]+=1; gh+=hg; ga+=ag

        out.insert(tk.END, f"\n  {h} vs {a}\n")
        out.insert(tk.END, f"  {'='*60}\n\n")
        out.insert(tk.END, f"  ELO: {h_elo:.0f}  vs  {a_elo:.0f}  (diff: {h_elo-a_elo:+.0f})\n")
        out.insert(tk.END, f"  Expected goals: {hg_xg:.2f} - {ag_xg:.2f}\n\n")
        out.insert(tk.END, f"  {n:,} SIMULATIONS:\n")
        out.insert(tk.END, f"    {h} win:  {results['H']/n:.1%}  ({results['H']:,})\n")
        out.insert(tk.END, f"    Draw:       {results['D']/n:.1%}  ({results['D']:,})\n")
        out.insert(tk.END, f"    {a} win:  {results['A']/n:.1%}  ({results['A']:,})\n\n")
        out.insert(tk.END, f"  Average goals: {gh/n:.2f} - {ga/n:.2f}  (total {gh/n+ga/n:.2f})\n\n")
        out.insert(tk.END, f"  Most common scorelines:\n")
        for (hg,ag), cnt in sorted(scorelines.items(), key=lambda x:-x[1])[:12]:
            out.insert(tk.END, f"    {hg}-{ag}  {cnt:6d}  ({cnt/n:.1%})\n")

    # ─── SEASON BROWSER ───
    def _run_season_sim(self):
        lg = self.season_lg.get()
        try: n = int(self.season_sim_count.get())
        except: n = 1000
        self.season_status.config(text="Running..."); self.root.update()
        self.sim.run_simulation(lg, n)
        self.season_status.config(text=f"Saved {n:,} seasons for {lg}. Browse below.")

    def _view_season(self):
        if self.sim.last_game_logs is None:
            self.season_status.config(text="Run a simulation first!"); return
        try: sn = int(self.season_num.get()) - 1
        except: sn = 0
        team = self.season_team.get()
        if sn < 0 or sn >= len(self.sim.last_game_logs):
            self.season_status.config(text=f"Season {sn+1} out of range"); return

        out = self.season_output; out.delete(1.0, tk.END)
        logs = self.sim.last_game_logs[sn]; n_sims = len(self.sim.last_game_logs)

        team_games = [(h,a,hg,ag) for h,a,hg,ag in logs if h==team or a==team]
        w=d=l=0; gf=ga=0
        for h,a,hg,ag in team_games:
            if team==h:
                gf+=hg; ga+=ag
                if hg>ag: w+=1
                elif hg<ag: l+=1
                else: d+=1
            else:
                gf+=ag; ga+=hg
                if ag>hg: w+=1
                elif ag<hg: l+=1
                else: d+=1
        pts = w*3+d

        out.insert(tk.END, f"\n  SEASON #{sn+1}: {team}\n")
        out.insert(tk.END, f"  {'='*55}\n")
        out.insert(tk.END, f"  Record: W{w}-D{d}-L{l}  |  {pts} pts  |  GF {gf}  GA {ga}  GD {gf-ga:+d}\n")
        out.insert(tk.END, f"  Games: {len(team_games)}  |  PPG: {pts/max(1,len(team_games)):.2f}\n\n")
        out.insert(tk.END, f"  {'Home':<28} {'Away':<28} {'Result':<6}\n")
        out.insert(tk.END, f"  {'-'*64}\n")

        bw = (0,"",""); bl = (0,"","")
        for h,a,hg,ag in team_games:
            out.insert(tk.END, f"  {h[:27]:<28} {a[:27]:<28} {hg}-{ag:<4}\n")
            if team==h:
                if hg-ag > bw[0]: bw = (hg-ag, a, f"{hg}-{ag}")
                if ag-hg > bl[0]: bl = (ag-hg, a, f"{hg}-{ag}")
            else:
                if ag-hg > bw[0]: bw = (ag-hg, h, f"{ag}-{hg}")
                if hg-ag > bl[0]: bl = (hg-ag, h, f"{hg}-{ag}")

        out.insert(tk.END, f"\n  Biggest win:  +{bw[0]} vs {bw[1]} ({bw[2]})\n")
        out.insert(tk.END, f"  Biggest loss: -{bl[0]} vs {bl[1]} ({bl[2]})\n")
        self.season_status.config(text=f"Season {sn+1}/{n_sims}")

    def _show_extremes(self):
        if self.sim.last_game_logs is None:
            self.season_status.config(text="Run a simulation first!"); return
        team = self.season_team.get()
        if not team: return

        all_logs = self.sim.last_game_logs; out = self.season_output; out.delete(1.0, tk.END)
        out.insert(tk.END, f"\n  EXTREME RESULTS: {team} (across {len(all_logs):,} seasons)\n")
        out.insert(tk.END, f"  {'='*55}\n\n")

        wins = []; losses = []
        for si, logs in enumerate(all_logs):
            for h,a,hg,ag in logs:
                if h==team and hg>ag: wins.append((hg-ag, a, f"{hg}-{ag}", si+1))
                elif a==team and ag>hg: wins.append((ag-hg, h, f"{ag}-{hg}", si+1))
                if h==team and ag>hg: losses.append((ag-hg, a, f"{hg}-{ag}", si+1))
                elif a==team and hg>ag: losses.append((hg-ag, h, f"{hg}-{ag}", si+1))

        wins.sort(key=lambda x: -x[0]); losses.sort(key=lambda x: -x[0])

        out.insert(tk.END, f"  BIGGEST WINS:\n")
        for margin, opp, score, sn in wins[:12]:
            out.insert(tk.END, f"    +{margin:<3} {score:<6} vs {opp:<28} (s{sn})\n")
        out.insert(tk.END, f"\n  BIGGEST LOSSES:\n")
        for margin, opp, score, sn in losses[:12]:
            out.insert(tk.END, f"    -{margin:<3} {score:<6} vs {opp:<28} (s{sn})\n")

    # ─── WHAT-IF SCENARIOS ───
    def _build_whatif_tab(self, parent=None):
        if parent is None: parent = self.whatif_tab
        self.whatif_output = tk.Text(parent, bg='#16213e', fg='#e0e0e0', insertbackground='white',
                                      font=('Consolas', 10), relief='flat', padx=10, pady=10)
        self.whatif_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ctrl = ttk.Frame(parent, padding="10"); ctrl.pack(fill=tk.X, side=tk.BOTTOM)

        # Row 1: Replay historic season
        ttk.Label(ctrl, text="Replay:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.wi_year = tk.StringVar(value="2024")
        ttk.Combobox(ctrl, textvariable=self.wi_year, values=["2022","2023","2024"], width=5).grid(row=0, column=1, padx=2)
        self.wi_lg = tk.StringVar(value="PL")
        ttk.Combobox(ctrl, textvariable=self.wi_lg, values=["PL","ESL","ESB"], width=4).grid(row=0, column=2, padx=2)
        ttk.Button(ctrl, text="Replay Season", command=self._replay_season).grid(row=0, column=3, padx=10)

        ttk.Label(ctrl, text="|  Match:").grid(row=0, column=4, sticky=tk.W, padx=(15,5))
        self.wi_home = tk.StringVar()
        ttk.Combobox(ctrl, textvariable=self.wi_home, values=self.sim.get_all_historic_teams(), width=22).grid(row=0, column=5, padx=2)
        ttk.Label(ctrl, text="vs").grid(row=0, column=6, padx=2)
        self.wi_away = tk.StringVar()
        ttk.Combobox(ctrl, textvariable=self.wi_away, values=self.sim.get_all_historic_teams(), width=22).grid(row=0, column=7, padx=2)
        ttk.Button(ctrl, text="Simulate", command=self._sim_historic_match).grid(row=0, column=8, padx=10)

        # Row 2: Custom league with team+year selection
        ttk.Label(ctrl, text="").grid(row=1, column=0)
        ttk.Label(ctrl, text="Custom League:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=(10,0))

        # Build team+year list from data
        all_teams_year = []
        for team in self.sim.get_all_historic_teams():
            for yr in range(2022, 2026):
                if team in self.sim.get_historic_teams(yr, 'PL') or team in self.sim.get_historic_teams(yr, 'ESL') or team in self.sim.get_historic_teams(yr, 'ESB'):
                    all_teams_year.append(f"{team} ({yr})")
                    break
            else:
                all_teams_year.append(team)  # fallback if no year found
        all_teams_year.sort()

        self.wi_team_entry = ttk.Combobox(ctrl, values=all_teams_year, width=30, font=('Segoe UI', 9))
        self.wi_team_entry.grid(row=2, column=1, columnspan=2, padx=2, pady=(10,0))
        ttk.Button(ctrl, text="Add Team", command=self._add_custom_team).grid(row=2, column=3, padx=5, pady=(10,0))
        ttk.Button(ctrl, text="Clear All", command=self._clear_custom).grid(row=2, column=4, padx=5, pady=(10,0))
        ttk.Button(ctrl, text="Simulate League", style='Accent.TButton', command=self._sim_custom).grid(row=2, column=5, columnspan=2, padx=5, pady=(10,0))

        self.custom_teams = []
        self.custom_label = ttk.Label(ctrl, text="No teams added")
        self.custom_label.grid(row=2, column=7, columnspan=2, padx=5, pady=(10,0))

    def _replay_season(self):
        try: yr = int(self.wi_year.get())
        except: yr = 2024
        lg = self.wi_lg.get()
        result = self.sim.replay_season(yr, lg, 500)
        if not result:
            self.whatif_output.delete(1.0, tk.END)
            self.whatif_output.insert(tk.END, f"No data for {lg} in {yr}\n"); return

        sorted_teams, sim_records, _, n_sims, teams = result
        out = self.whatif_output; out.delete(1.0, tk.END)
        out.insert(tk.END, f"\n  REPLAY: {lg} {yr} — {n_sims:,} full seasons from scratch\n")
        out.insert(tk.END, f"  {'='*75}\n\n")
        for rank, t in enumerate(sorted_teams, 1):
            recs = sim_records[t]
            avg_pts = np.mean([r['pts'] for r in recs])
            mn, mx = np.min([r['pts'] for r in recs]), np.max([r['pts'] for r in recs])
            avg_gd = np.mean([r['gd'] for r in recs])
            champ = sum(1 for r in recs if r['pos']==1)/n_sims
            rel = sum(1 for r in recs if r['pos']>=len(teams)-1)/n_sims
            tags = ""
            if champ>0.3: tags=" CHAMPION"
            elif rel>0.5: tags=" RELEGATED"
            out.insert(tk.END, f"  {rank:2d}. {t[:30]:<31} {avg_pts:5.1f} pts ({mn:.0f}-{mx:.0f})  GD {avg_gd:+7.1f}  C:{champ:.0%}  R:{rel:.0%}{tags}\n")

    def _sim_historic_match(self):
        h = self.wi_home.get(); a = self.wi_away.get()
        if not h or not a or h == a: return
        out = self.whatif_output; out.delete(1.0, tk.END)
        h_elo = self.sim.elo.ratings.get(h, 1500); a_elo = self.sim.elo.ratings.get(a, 1500)

        n = 5000; results = {'H':0,'D':0,'A':0}; gh=ga=0
        for _ in range(n):
            hg, ag = self.sim.sim_match(h, a)
            if hg>ag: results['H']+=1
            elif ag>hg: results['A']+=1
            else: results['D']+=1
            gh+=hg; ga+=ag

        out.insert(tk.END, f"\n  HISTORIC MATCHUP: {h}  vs  {a}\n")
        out.insert(tk.END, f"  {'='*60}\n\n")
        out.insert(tk.END, f"  ELO: {h_elo:.0f}  vs  {a_elo:.0f}  (diff: {h_elo-a_elo:+.0f})\n\n")
        out.insert(tk.END, f"  {n:,} simulations:\n")
        out.insert(tk.END, f"    {h} win:  {results['H']/n:.1%}  ({results['H']:,})\n")
        out.insert(tk.END, f"    Draw:       {results['D']/n:.1%}  ({results['D']:,})\n")
        out.insert(tk.END, f"    {a} win:  {results['A']/n:.1%}  ({results['A']:,})\n")
        out.insert(tk.END, f"\n  Avg goals: {gh/n:.2f} - {ga/n:.2f}\n")

    def _add_custom_team(self):
        t = self.wi_team_entry.get().strip()
        if not t: return
        if t in self.custom_teams:
            self.custom_label.config(text=f"'{t}' already added"); return
        self.custom_teams.append(t)
        self.wi_team_entry.delete(0, tk.END)
        self.custom_label.config(text=f"{len(self.custom_teams)} teams: {', '.join(self.custom_teams[:5])}{'...' if len(self.custom_teams)>5 else ''}")

    def _clear_custom(self):
        self.custom_teams = []
        self.custom_label.config(text="Cleared")

    def _sim_custom(self):
        if len(self.custom_teams) < 2:
            self.custom_label.config(text="Add at least 2 teams"); return
        teams = list(self.custom_teams)
        result = self.sim.sim_custom_league(teams, 500)
        if not result: return
        sim_records, n_sims = result
        avg_pos = {t: np.mean([r['pos'] for r in sim_records[t]]) for t in teams}
        sorted_teams = sorted(teams, key=lambda t: avg_pos[t])

        out = self.whatif_output; out.delete(1.0, tk.END)
        out.insert(tk.END, f"\n  CUSTOM LEAGUE: {len(teams)} teams — {n_sims:,} simulations\n")
        out.insert(tk.END, f"  {'='*70}\n\n")
        for rank, t in enumerate(sorted_teams, 1):
            recs = sim_records[t]
            avg_pts = np.mean([r['pts'] for r in recs])
            mn, mx = np.min([r['pts'] for r in recs]), np.max([r['pts'] for r in recs])
            avg_gd = np.mean([r['gd'] for r in recs])
            champ = sum(1 for r in recs if r['pos']==1)/n_sims
            out.insert(tk.END, f"  {rank:2d}. {t[:35]:<36} {avg_pts:5.1f} pts ({mn:.0f}-{mx:.0f})  GD {avg_gd:+7.1f}  Win: {champ:.0%}\n")
        self.custom_label.config(text=f"Simulated {len(teams)} teams")


if __name__ == '__main__':
    SimulatorUI()
