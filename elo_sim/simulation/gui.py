"""
Tkinter GUI for elo_sim (modern, full-featured)
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import queue
from functools import partial
import numpy as np

from elo_sim.simulation.core import simulate_multiple_seasons, expected_goals_v2, poisson_match

class EloSimGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Football League Simulation GUI")
        self.geometry("1200x800")
        self.sim_thread = None
        self.sim_queue = queue.Queue()
        self.sim_results = None
        self.summary = None
        self.biggest_gd_win = None
        self.biggest_gd_loss = None
        self.all_sim_results = None
        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)
        # Table Tab
        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text="Summary Table")
        self._create_table_tab(self.table_frame)
        # Team Analysis Tab
        self.team_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.team_frame, text="Team Analysis")
        self._create_team_tab(self.team_frame)
        # H2H Tab
        self.h2h_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.h2h_frame, text="Head-to-Head")
        self._create_h2h_tab(self.h2h_frame)
        # Export/Advanced Tab
        self.export_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.export_frame, text="Export/Advanced")
        self._create_export_tab(self.export_frame)

    def _create_table_tab(self, parent):
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill='x', padx=10, pady=5)
        ttk.Label(file_frame, text="CSV File:").pack(side='left')
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=60)
        self.file_entry.pack(side='left', padx=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side='left')
        ttk.Label(file_frame, text="Season:").pack(side='left', padx=10)
        self.season_var = tk.StringVar(value="2025")
        self.season_entry = ttk.Entry(file_frame, textvariable=self.season_var, width=10)
        self.season_entry.pack(side='left', padx=5)
        ttk.Label(file_frame, text="Simulations:").pack(side='left', padx=10)
        self.sim_var = tk.IntVar(value=1000)
        self.sim_entry = ttk.Entry(file_frame, textvariable=self.sim_var, width=10)
        self.sim_entry.pack(side='left', padx=5)
        self.sim_button = ttk.Button(file_frame, text="Start Simulation", command=self.run_simulation)
        self.sim_button.pack(side='left', padx=10)
        self.progress = ttk.Progressbar(parent, orient='horizontal', mode='determinate')
        self.progress.pack(fill='x', padx=10, pady=5)
        self.tree = ttk.Treeview(parent, columns=("Team", "AvgPts", "StdPts", "MinPts", "MaxPts", "AvgElo", "StdElo", "AvgGD", "90% CI", "95% CI", "Rank 90% CI", "Rank 95% CI"), show='headings')
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90, anchor='center')
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)

    def _create_team_tab(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill='x', padx=10, pady=5)
        ttk.Label(top, text="Select Team:").pack(side='left')
        self.team_select = ttk.Combobox(top, state='readonly')
        self.team_select.pack(side='left', padx=5)
        ttk.Button(top, text="Show Analysis", command=self.show_team_analysis).pack(side='left', padx=10)
        self.team_text = tk.Text(parent, height=30, width=120)
        self.team_text.pack(fill='both', expand=True, padx=10, pady=10)

    def _create_h2h_tab(self, parent):
        top = ttk.Frame(parent)
        top.pack(fill='x', padx=10, pady=5)
        ttk.Label(top, text="Team A:").pack(side='left')
        self.h2h_a = ttk.Combobox(top, state='readonly')
        self.h2h_a.pack(side='left', padx=5)
        ttk.Label(top, text="Team B:").pack(side='left')
        self.h2h_b = ttk.Combobox(top, state='readonly')
        self.h2h_b.pack(side='left', padx=5)
        ttk.Button(top, text="Analyze H2H", command=self.show_h2h_analysis).pack(side='left', padx=10)
        self.h2h_text = tk.Text(parent, height=30, width=120)
        self.h2h_text.pack(fill='both', expand=True, padx=10, pady=10)

    def _create_export_tab(self, parent):
        ttk.Button(parent, text="Export Last Simulation to CSV", command=self.export_csv).pack(pady=10)
        self.export_label = ttk.Label(parent, text="")
        self.export_label.pack()
        self.adv_text = tk.Text(parent, height=20, width=120)
        self.adv_text.pack(fill='both', expand=True, padx=10, pady=10)

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if filename:
            self.file_var.set(filename)

    def run_simulation(self):
        csv_file = self.file_var.get()
        season = self.season_var.get()
        n_sim = self.sim_var.get()
        if not os.path.isfile(csv_file):
            messagebox.showerror("Error", "Please select a valid CSV file.")
            return
        self.progress['value'] = 0
        self.tree.delete(*self.tree.get_children())
        self.sim_thread = threading.Thread(target=self.simulate, args=(csv_file, season, n_sim))
        self.sim_thread.start()
        self.after(100, self.check_sim_queue)

    def simulate(self, csv_file, season, n_sim):
        try:
            n_runs = 100  # Or make this configurable in the GUI
            summary, biggest_sim_win, biggest_sim_loss, biggest_gd_win, biggest_gd_loss, all_sim_results = simulate_multiple_seasons(csv_file, season, n_sim=n_sim, n_runs=n_runs)
            self.sim_queue.put(('done', (summary, biggest_sim_win, biggest_sim_loss, biggest_gd_win, biggest_gd_loss, all_sim_results)))
        except Exception as e:
            self.sim_queue.put(('error', str(e)))

    def check_sim_queue(self):
        try:
            msg, data = self.sim_queue.get_nowait()
            if msg == 'done':
                self.show_results(*data)
                self.progress['value'] = 100
            elif msg == 'error':
                messagebox.showerror("Simulation Error", data)
        except queue.Empty:
            if self.sim_thread and self.sim_thread.is_alive():
                self.progress['value'] += 1
                self.after(100, self.check_sim_queue)

    def show_results(self, summary, biggest_sim_win, biggest_sim_loss, biggest_gd_win, biggest_gd_loss, all_sim_results):
        self.summary = summary
        self.biggest_gd_win = biggest_gd_win
        self.biggest_gd_loss = biggest_gd_loss
        self.all_sim_results = all_sim_results
        self.tree.delete(*self.tree.get_children())

        # --- Display simulation summary stats directly ---
        # summary: {team: {mean_pts, std_pts, min_pts, max_pts, pts_ci_90, pts_ci_95, mean_elo, std_elo, mean_gd}}
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
             stats.get('pts_ci_95', ('','')),
             stats.get('rank_ci_90', ('','')),
             stats.get('rank_ci_95', ('',''))
            )
            for team, stats in summary.items()
        ]
        table = sorted(table, key=lambda x: (x[1], x[7], x[5]), reverse=True)
        for team, mean_pts, std_pts, min_pts, max_pts, mean_elo, std_elo, mean_gd, ci90, ci95, rank90, rank95 in table:
            self.tree.insert('', 'end', values=(team, f"{mean_pts:.2f}", f"{std_pts:.2f}", f"{min_pts:.0f}", f"{max_pts:.0f}", f"{mean_elo:.1f}", f"{std_elo:.1f}", f"{mean_gd:.2f}", f"{ci90}", f"{ci95}", f"{rank90}", f"{rank95}"))
        teams = list(summary.keys())
        self.team_select['values'] = teams
        self.h2h_a['values'] = teams
        self.h2h_b['values'] = teams
        self.adv_text.delete('1.0', tk.END)
        self.adv_text.insert(tk.END, f"Biggest Elo gain: {biggest_sim_win}\n")
        self.adv_text.insert(tk.END, f"Biggest Elo loss: {biggest_sim_loss}\n")
        self.adv_text.insert(tk.END, f"Biggest win by GD: {biggest_gd_win}\n")
        self.adv_text.insert(tk.END, f"Biggest loss by GD: {biggest_gd_loss}\n")

    def show_sim_results(self, sim_idx):
        # Show full simulation results for a given sim index in a popup
        if not self.all_sim_results or sim_idx is None or sim_idx >= len(self.all_sim_results):
            messagebox.showinfo("Simulation Results", "No simulation data available for this index.")
            return
        sim = self.all_sim_results[sim_idx]
        results = sim.get('results', [])
        popup = tk.Toplevel(self)
        popup.title(f"Simulation {sim_idx} Results")
        text = tk.Text(popup, height=30, width=100)
        text.pack(fill='both', expand=True)
        for r in results:
            text.insert(tk.END, f"{r['date']}: {r['team_a']} {r['goals_a']} - {r['goals_b']} {r['team_b']} (Elo: {r.get('elo_a','?')} vs {r.get('elo_b','?')})\n")
        text.config(state='disabled')

    def show_team_analysis(self):
        team = self.team_select.get()
        if not team or not self.summary:
            return
        stats = self.summary[team]
        self.team_text.delete('1.0', tk.END)
        self.team_text.insert(tk.END, f"--- {team} ---\n")
        for k, v in stats.items():
            if k in ('longest_win_streak', 'longest_unbeaten_streak', 'longest_losing_streak', 'clinch_dates', 'elimination_dates'):
                continue  # We'll format these below
            self.team_text.insert(tk.END, f"{k}: {v}\n")
        # Biggest win/loss/elo gain/loss (robust to missing keys)
        try:
            gd_win = getattr(self, 'biggest_gd_win', {}) or {}
            gd_win = gd_win.get(team)
            gd_loss = getattr(self, 'biggest_gd_loss', {}) or {}
            gd_loss = gd_loss.get(team)
            elo_win = getattr(self, 'biggest_elo_win', {}) or {}
            elo_win = elo_win.get(team)
            elo_loss = getattr(self, 'biggest_elo_loss', {}) or {}
            elo_loss = elo_loss.get(team)
            if gd_win and 'gd' in gd_win:
                self.team_text.insert(tk.END, f"\nBiggest win by GD: {gd_win.get('score','?')} vs {gd_win.get('opponent','?')} (GD: {gd_win.get('gd','?')}, Date: {gd_win.get('date','?')}, Sim: {gd_win.get('sim','?')})\n")
            if gd_loss and 'gd' in gd_loss:
                self.team_text.insert(tk.END, f"Biggest loss by GD: {gd_loss.get('score','?')} vs {gd_loss.get('opponent','?')} (GD: {gd_loss.get('gd','?')}, Date: {gd_loss.get('date','?')}, Sim: {gd_loss.get('sim','?')})\n")
            if elo_win and 'elo_diff' in elo_win:
                self.team_text.insert(tk.END, f"Biggest Elo gain: {elo_win.get('score','?')} vs {elo_win.get('opponent','?')} (ΔElo: {elo_win.get('elo_diff',0):.2f}, Date: {elo_win.get('date','?')}, Sim: {elo_win.get('sim','?')})\n")
            if elo_loss and 'elo_diff' in elo_loss:
                self.team_text.insert(tk.END, f"Biggest Elo loss: {elo_loss.get('score','?')} vs {elo_loss.get('opponent','?')} (ΔElo: {elo_loss.get('elo_diff',0):.2f}, Date: {elo_loss.get('date','?')}, Sim: {elo_loss.get('sim','?')})\n")
        except Exception as e:
            self.team_text.insert(tk.END, f"\n[Error displaying biggest win/loss: {e}]\n")
        # --- Always show streaks and advanced stats, robust to errors ---
        # Longest win streak
        try:
            lw = stats.get('longest_win_streak', {})
            if lw and lw.get('length', 0) > 0:
                streak_games = lw.get('games', [])
                streak_str = ", ".join([f"{g['score']} vs {g['opponent']}" for g in streak_games])
                tag = f"win_streak_{lw.get('sim','?')}"
                self.team_text.insert(tk.END, f"\nLongest win streak: {lw['length']} (Sim {lw.get('sim','?')}, Games: {streak_str})\n", tag)
                self.team_text.tag_bind(tag, '<Button-1>', lambda e, sim=lw.get('sim'): self.show_sim_results(sim))
            else:
                self.team_text.insert(tk.END, "\nLongest win streak: []\n")
        except Exception as e:
            self.team_text.insert(tk.END, f"\n[Error displaying win streak: {e}]\n")
        # Longest unbeaten streak
        try:
            lu = stats.get('longest_unbeaten_streak', {})
            if lu and lu.get('length', 0) > 0:
                streak_games = lu.get('games', [])
                streak_str = ", ".join([f"{g['score']} vs {g['opponent']}" for g in streak_games])
                tag = f"unbeaten_streak_{lu.get('sim','?')}"
                self.team_text.insert(tk.END, f"Longest unbeaten streak: {lu['length']} (Sim {lu.get('sim','?')}, Games: {streak_str})\n", tag)
                self.team_text.tag_bind(tag, '<Button-1>', lambda e, sim=lu.get('sim'): self.show_sim_results(sim))
            else:
                self.team_text.insert(tk.END, "Longest unbeaten streak: []\n")
        except Exception as e:
            self.team_text.insert(tk.END, f"[Error displaying unbeaten streak: {e}]\n")
        # Longest losing streak
        try:
            ll = stats.get('longest_losing_streak', {})
            if ll and ll.get('length', 0) > 0:
                streak_games = ll.get('games', [])
                streak_str = ", ".join([f"{g['score']} vs {g['opponent']}" for g in streak_games])
                tag = f"losing_streak_{ll.get('sim','?')}"
                self.team_text.insert(tk.END, f"Longest losing streak: {ll['length']} (Sim {ll.get('sim','?')}, Games: {streak_str})\n", tag)
                self.team_text.tag_bind(tag, '<Button-1>', lambda e, sim=ll.get('sim'): self.show_sim_results(sim))
            else:
                self.team_text.insert(tk.END, "Longest losing streak: []\n")
        except Exception as e:
            self.team_text.insert(tk.END, f"[Error displaying losing streak: {e}]\n")
        # Clinch/elimination dates clickable
        try:
            clinch = stats.get('clinch_dates', {})
            elim = stats.get('elimination_dates', {})
            clinch_earliest_sims = [i for i, d in enumerate(clinch.get('all', [])) if d == clinch.get('earliest')]
            clinch_latest_sims = [i for i, d in enumerate(clinch.get('all', [])) if d == clinch.get('latest')]
            elim_earliest_sims = [i for i, d in enumerate(elim.get('all', [])) if d == elim.get('earliest')]
            elim_latest_sims = [i for i, d in enumerate(elim.get('all', [])) if d == elim.get('latest')]
            def insert_clickable_dates(label, date, sim_list, tag_prefix):
                if date is None:
                    self.team_text.insert(tk.END, f"{label}: None\n")
                    return
                tag = f"{tag_prefix}_{date}"
                self.team_text.insert(tk.END, f"{label}: {date} (click to view sim(s))\n", tag)
                self.team_text.tag_bind(tag, '<Button-1>', lambda e, sims=sim_list: [self.show_sim_results(sim) for sim in sims])
            insert_clickable_dates("Clinch earliest", clinch.get('earliest'), clinch_earliest_sims, "clinch_earliest")
            insert_clickable_dates("Clinch latest", clinch.get('latest'), clinch_latest_sims, "clinch_latest")
            insert_clickable_dates("Elimination earliest", elim.get('earliest'), elim_earliest_sims, "elim_earliest")
            insert_clickable_dates("Elimination latest", elim.get('latest'), elim_latest_sims, "elim_latest")
        except Exception as e:
            self.team_text.insert(tk.END, f"[Error displaying clinch/elimination dates: {e}]\n")
        # Position distribution table
        try:
            if self.all_sim_results:
                pos_counts = {}
                for sim_num, sim in enumerate(self.all_sim_results):
                    sim_results = sim['results']
                    team_pts = {}
                    for r in sim_results:
                        team_pts.setdefault(r['team_a'], 0)
                        team_pts.setdefault(r['team_b'], 0)
                        team_pts[r['team_a']] += r['points_a']
                        team_pts[r['team_b']] += r['points_b']
                    table = sorted(team_pts.items(), key=lambda x: x[1], reverse=True)
                    for pos, (t, pts) in enumerate(table, 1):
                        if t == team:
                            pos_counts[pos] = pos_counts.get(pos, 0) + 1
                total = sum(pos_counts.values())
                self.team_text.insert(tk.END, "\nPosition distribution (across all sims):\n")
                for pos in sorted(pos_counts):
                    pct = 100.0 * pos_counts[pos] / total if total else 0
                    self.team_text.insert(tk.END, f"{pos}: {pos_counts[pos]} times ({pct:.1f}%)\n")
        except Exception as e:
            self.team_text.insert(tk.END, f"[Error displaying position distribution: {e}]\n")

    def show_h2h_analysis(self):
        t1 = self.h2h_a.get()
        t2 = self.h2h_b.get()
        if not t1 or not t2 or not self.all_sim_results:
            return
        wins = draws = losses = 0
        scorelines = []
        for sim in self.all_sim_results:
            for r in sim['results']:
                if (r['team_a'] == t1 and r['team_b'] == t2) or (r['team_a'] == t2 and r['team_b'] == t1):
                    if r['team_a'] == t1:
                        ga, gb = r['goals_a'], r['goals_b']
                    else:
                        ga, gb = r['goals_b'], r['goals_a']
                    scorelines.append(f"{ga}:{gb}")
                    if ga > gb:
                        wins += 1
                    elif ga == gb:
                        draws += 1
                    else:
                        losses += 1
        from collections import Counter
        self.h2h_text.delete('1.0', tk.END)
        self.h2h_text.insert(tk.END, f"H2H over all sims: {t1} vs {t2}\n")
        self.h2h_text.insert(tk.END, f"{t1} wins: {wins}, draws: {draws}, {t2} wins: {losses}\n")
        if scorelines:
            most_common = Counter(scorelines).most_common(5)
            self.h2h_text.insert(tk.END, "Most common scorelines:\n")
            for s, c in most_common:
                self.h2h_text.insert(tk.END, f"{s} ({c}x)\n")
        # Most probable outcome if played tomorrow (1000 sims with latest Elo and rolling form)
        # Use latest Elo and rolling stats from the last completed sim
        if self.all_sim_results and self.all_sim_results[-1]['results']:
            last_sim = self.all_sim_results[-1]['results']
            # Get latest Elo for both teams
            elo_t1 = elo_t2 = 1500
            for r in reversed(last_sim):
                if r['team_a'] == t1:
                    elo_t1 = r.get('elo_a', 1500)
                    break
            for r in reversed(last_sim):
                if r['team_b'] == t2:
                    elo_t2 = r.get('elo_b', 1500)
                    break
            # Use rolling stats from last sim
            def get_rolling_stats(team, last_n=5):
                games = []
                for r in last_sim:
                    if r['team_a'] == team:
                        games.append((r['goals_a'], r['goals_b']))
                    elif r['team_b'] == team:
                        games.append((r['goals_b'], r['goals_a']))
                games = games[-last_n:]
                if not games:
                    return {"avg_goals_for": 1.5, "avg_goals_against": 1.5}
                gf = np.mean([g[0] for g in games])
                ga = np.mean([g[1] for g in games])
                return {"avg_goals_for": gf, "avg_goals_against": ga}
            home_stats = get_rolling_stats(t1)
            away_stats = get_rolling_stats(t2)
            HOME_ADV = 0.2
            FORM_STD = 0.15
            tomorrow_scores = []
            tomorrow_wins = tomorrow_draws = tomorrow_losses = 0
            for _ in range(1000):
                form_home = np.random.normal(0, FORM_STD)
                form_away = np.random.normal(0, FORM_STD)
                mu_home = expected_goals_v2(elo_t1, elo_t2, home_stats, away_stats, HOME_ADV) + form_home
                mu_away = expected_goals_v2(elo_t2, elo_t1, away_stats, home_stats, 0) + form_away
                mu_home = max(0.5, mu_home)
                mu_away = max(0.5, mu_away)
                g1, g2 = poisson_match(mu_home, mu_away)
                tomorrow_scores.append(f"{g1}:{g2}")
                if g1 > g2:
                    tomorrow_wins += 1
                elif g1 == g2:
                    tomorrow_draws += 1
                else:
                    tomorrow_losses += 1
            self.h2h_text.insert(tk.END, f"\nIf played tomorrow (1000 sims):\n{t1} wins: {tomorrow_wins}, draws: {tomorrow_draws}, {t2} wins: {tomorrow_losses}\n")
            most_common_tomorrow = Counter(tomorrow_scores).most_common(5)
            self.h2h_text.insert(tk.END, "Most common scorelines (tomorrow):\n")
            for s, c in most_common_tomorrow:
                self.h2h_text.insert(tk.END, f"{s} ({c}x)\n")

    def export_csv(self):
        if not self.all_sim_results:
            self.export_label.config(text="No simulation results to export.")
            return
        filename = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return
        with open(filename, 'w', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(['sim','team_a','team_b','goals_a','goals_b'])
            for sim_idx, sim in enumerate(self.all_sim_results):
                for r in sim.get('results', []):
                    writer.writerow([sim_idx, r.get('team_a'), r.get('team_b'), r.get('goals_a'), r.get('goals_b')])
        self.export_label.config(text=f"Exported to {filename}")

if __name__ == "__main__":
    app = EloSimGUI()
    app.mainloop()
