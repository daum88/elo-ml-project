#!/usr/bin/env python3
"""Estonian Football League Table Simulator with promotion/relegation."""

import numpy as np
from datetime import datetime
from collections import defaultdict
from predictor import DataLoader, ELOEngine


class SeasonSimulator:
    def __init__(self):
        self.loader = DataLoader()
        for fn, lg in [('premium_liiga','PL'),('esiliiga','ESL'),('esiliiga_b','ESB')]:
            for yr in ['2022','2023','2024','2025']:
                self.loader.load_csv(f'data/{fn}_{yr}.csv', lg)

        self.all_matches = self.loader.sorted_matches()
        self.all_matches = [m for m in self.all_matches if m['date'].year >= 2022]

        self.team_league_map = {}
        for m in self.all_matches:
            y = m['date'].year
            if 'league' in m:
                self.team_league_map[(m['home'], y)] = m['league']
                self.team_league_map[(m['away'], y)] = m['league']

        self.cutoff = datetime(2025, 9, 1)
        self.train = [m for m in self.all_matches if m['date'] < self.cutoff]
        t2025 = [m for m in self.train if m['date'] >= datetime(2025, 1, 1)]
        dr = sum(1 for m in t2025 if m['home_goals'] == m['away_goals']) / max(1, len(t2025))
        self.elo = ELOEngine(k_factor=20, home_advantage=50, draw_rate=dr)
        self.elo.fit_with_league_awareness(self.train, self.team_league_map)

    def sim_match(self, home, away):
        hg, ag = self.elo.expected_goals(home, away)
        return min(np.random.poisson(hg), 8), min(np.random.poisson(ag), 8)

    def get_league_teams(self, year, league):
        teams = set()
        for m in self.all_matches:
            if m['date'].year != year: continue
            if self.team_league_map.get((m['home'], year)) == league:
                teams.add(m['home']); teams.add(m['away'])
        return teams

    def get_played_matches(self, year, league):
        return [m for m in self.all_matches
                if m['date'].year == year
                and m['date'] < self.cutoff
                and self.team_league_map.get((m['home'], year)) == league]

    def generate_remaining_fixtures(self, teams, played):
        """Generate random pairings for remaining round-robin matches."""
        required = {}
        tl = list(teams)
        for i, h in enumerate(tl):
            for a in tl[i+1:]:
                required[(min(h, a), max(h, a))] = 4

        for m in played:
            key = (min(m['home'], m['away']), max(m['home'], m['away']))
            if key in required:
                required[key] = max(0, required[key] - 1)

        fixtures = []
        for (t1, t2), count in required.items():
            for _ in range(count):
                fixtures.append((t1, t2) if np.random.random() < 0.5 else (t2, t1))
        np.random.shuffle(fixtures)
        return fixtures

    def build_standings(self, teams, played_matches):
        s = {t: {'pts': 0, 'gd': 0, 'gf': 0, 'ga': 0, 'gp': 0} for t in teams}
        for m in played_matches:
            h, a = m['home'], m['away']
            s[h]['gp'] += 1; s[a]['gp'] += 1
            gd = m['home_goals'] - m['away_goals']
            s[h]['gf'] += m['home_goals']; s[h]['ga'] += m['away_goals']
            s[a]['gf'] += m['away_goals']; s[a]['ga'] += m['home_goals']
            s[h]['gd'] += gd; s[a]['gd'] -= gd
            if gd > 0: s[h]['pts'] += 3
            elif gd < 0: s[a]['pts'] += 3
            else: s[h]['pts'] += 1; s[a]['pts'] += 1
        return s

    def sort_table(self, standings):
        return sorted(standings.items(),
                     key=lambda x: (-x[1]['pts'], -x[1]['gd'], -x[1]['gf']))

    def simulate_league(self, league_code, league_name, year=2025, n_sims=10000):
        teams = self.get_league_teams(year, league_code)
        played = self.get_played_matches(year, league_code)

        if len(teams) < 4:
            return None

        base = self.build_standings(teams, played)
        n_teams = len(teams)

        # Accumulators
        positions = {t: np.zeros(n_teams + 1) for t in teams}
        points = {t: [] for t in teams}
        goal_diff = {t: [] for t in teams}
        champion = {t: 0 for t in teams}
        promoted_auto = {t: 0 for t in teams}
        promoted_total = {t: 0 for t in teams}
        relegated_auto = {t: 0 for t in teams}
        relegated_total = {t: 0 for t in teams}
        playoff_spot = {t: 0 for t in teams}

        for _ in range(n_sims):
            s = {t: dict(base[t]) for t in teams}
            fixtures = self.generate_remaining_fixtures(teams, played)

            for h, a in fixtures:
                hg, ag = self.sim_match(h, a)
                s[h]['gp'] += 1; s[a]['gp'] += 1
                s[h]['gf'] += hg; s[h]['ga'] += ag
                s[a]['gf'] += ag; s[a]['ga'] += hg
                gd = hg - ag
                s[h]['gd'] += gd; s[a]['gd'] -= gd
                if hg > ag: s[h]['pts'] += 3
                elif ag > hg: s[a]['pts'] += 3
                else: s[h]['pts'] += 1; s[a]['pts'] += 1

            table = self.sort_table(s)

            for pos, (t, _) in enumerate(table, 1):
                positions[t][pos] += 1
                points[t].append(s[t]['pts'])
                goal_diff[t].append(s[t]['gd'])

                if pos == 1:
                    champion[t] += 1
                if pos <= 2:
                    promoted_auto[t] += 1
                    promoted_total[t] += 1
                if pos == 3:
                    playoff_spot[t] += 1
                if pos >= n_teams - 1:  # bottom 2 auto-relegated
                    relegated_auto[t] += 1
                    relegated_total[t] += 1
                if pos == n_teams - 2:  # relegation playoff spot
                    playoff_spot[t] += 1

        # Simulate promotion playoffs (3rd ESL vs 9th PL, 3rd ESB vs 9th ESL)
        promo_playoff_wins = {t: 0 for t in teams}
        rel_playoff_wins = {t: 0 for t in teams}

        for _ in range(n_sims):
            table = self.sort_table({t: {'pts': np.random.choice(points[t]), 'gd': np.random.choice(goal_diff[t]), 'gf': 0} for t in teams})

            third_place = table[2][0]  # 3rd place team
            ninth_place = table[n_teams - 2][0]  # 2nd-to-last

            # Simulate playoff: two-leg tie
            agg_home = 0
            agg_away = 0
            for leg in range(2):
                if leg == 0:
                    hg, ag = self.sim_match(ninth_place, third_place)
                else:
                    hg, ag = self.sim_match(third_place, ninth_place)
                    agg_home = hg
                    agg_away = ag

            # Simplified: higher league team stays up ~60% of the time
            if np.random.random() < 0.6:
                promo_playoff_wins[ninth_place] += 1
            else:
                promo_playoff_wins[third_place] += 1
                promoted_total[third_place] += 1
                relegated_total[ninth_place] += 1

        # Display
        print(f"\n{'='*100}")
        print(f"  {league_name} {year} — PROJECTED FINAL TABLE ({n_sims:,} simulations)")
        remaining = n_teams * (n_teams - 1) * 2 - sum(base[t]['gp'] for t in teams)
        print(f"  Based on {len(played)} played + ~{remaining} simulated matches")
        print(f"{'='*100}")
        print(f"  {'Pos':<4} {'Team':<28} {'AvgPts':<8} {'PtRange':<14} {'AvgGD':<8} {'Champion':<9} {'Promoted':<9} {'Relegated':<9} {'Playoff':<8}")
        print(f"  {'-'*97}")

        team_avg_pos = {t: sum(p * positions[t][p] for p in range(1, n_teams+1)) / n_sims for t in teams}

        for rank, t in enumerate(sorted(teams, key=lambda x: team_avg_pos[x]), 1):
            avg_pts = np.mean(points[t])
            mn = np.min(points[t])
            mx = np.max(points[t])
            avg_gd = np.mean(goal_diff[t])
            c_pct = champion[t] / n_sims
            p_pct = promoted_total[t] / n_sims
            r_pct = relegated_total[t] / n_sims
            po_pct = playoff_spot[t] / n_sims

            tags = ""
            if c_pct > 0.3: tags = " [CHAMPION]"
            elif p_pct > 0.3: tags = " [PROMOTED]"
            if r_pct > 0.5: tags += " [RELEGATED]"
            elif r_pct > 0.2: tags += " [danger]"

            print(f"  {rank:<4} {t[:27]:<28} {avg_pts:<8.1f} {mn:4.0f}-{mx:<7.0f} {avg_gd:+8.1f} "
                  f"{c_pct:<9.1%} {p_pct:<9.1%} {r_pct:<9.1%} {po_pct:<8.1%}{tags}")

        return {t: {'avg_pts': np.mean(points[t]), 'avg_pos': team_avg_pos[t],
                     'champion': champion[t]/n_sims, 'promoted': promoted_total[t]/n_sims,
                     'relegated': relegated_total[t]/n_sims, 'playoff': playoff_spot[t]/n_sims}
                for t in teams}


def main():
    sim = SeasonSimulator()

    pl = sim.simulate_league('PL', 'PREMIUM LIIGA')
    esl = sim.simulate_league('ESL', 'ESILIIGA')
    esb = sim.simulate_league('ESB', 'ESILIIGA B')

    if pl and esl:
        print(f"\n{'='*100}")
        print(f"  PROMOTION / RELEGATION SUMMARY")
        print(f"{'='*100}")
        # PL relegation candidates
        pl_rel = sorted([(t, d['relegated']) for t, d in pl.items()], key=lambda x: -x[1])
        esl_prom = sorted([(t, d['promoted']) for t, d in esl.items()], key=lambda x: -x[1])

        print(f"\n  PREMIUM LIIGA relegation candidates:")
        for t, pct in pl_rel[:4]:
            print(f"    {t:<30} {pct:.1%} chance of relegation")

        print(f"\n  ESILIIGA promotion candidates:")
        for t, pct in esl_prom[:4]:
            print(f"    {t:<30} {pct:.1%} chance of promotion to Premium Liiga")

        if esb:
            esb_prom = sorted([(t, d['promoted']) for t, d in esb.items()], key=lambda x: -x[1])
            print(f"\n  ESILIIGA B promotion candidates:")
            for t, pct in esb_prom[:4]:
                print(f"    {t:<30} {pct:.1%} chance of promotion to Esiliiga")


if __name__ == '__main__':
    main()
