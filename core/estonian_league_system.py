#!/usr/bin/env python3
"""
Estonian League System - Complete two-tier football league simulation
Handles Esiliiga and Esiliiga B with promotion/relegation mechanics
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from typing import Dict, List, Tuple, Optional
import re

class EstonianLeagueSystem:
    def __init__(self):
        self.esiliiga_teams = set()
        self.esiliiga_b_teams = set()
        self.historical_matches = []
        self.current_season_matches = []
        self.fixtures = []
        
        # League parameters
        self.teams_per_league = 10
        self.auto_promotion_spots = 2
        self.auto_relegation_spots = 2
        self.playoff_spots = 1
        
    def load_all_data(self):
        """Load and process all Estonian league data"""
        print("🇪🇪 ESTONIAN LEAGUE SYSTEM DATA PROCESSOR")
        print("=" * 60)
        
        # Process Esiliiga data
        esiliiga_data = self._process_league_data(['esiliiga2023.csv', 'esiliiga2024.csv', 'esiliiga2025.csv'], 'Esiliiga')
        
        # Process Esiliiga B data  
        esiliiga_b_data = self._process_league_data(['esiliigab2023.csv', 'esiliigab2024.csv', 'esiliigab2025.csv'], 'Esiliiga B')
        
        # Combine and analyze
        self._analyze_league_structure(esiliiga_data, esiliiga_b_data)
        
        return esiliiga_data, esiliiga_b_data
    
    def _process_league_data(self, files: List[str], league_name: str) -> Dict:
        """Process data for a specific league"""
        print(f"\n📊 Processing {league_name} data...")
        
        all_matches = []
        teams = set()
        
        for file in files:
            try:
                df = pd.read_csv(file)
                print(f"   📁 Reading {file}: {len(df)} rows")
                
                # Standardize column names
                df.columns = df.columns.str.strip()
                
                # Process each match
                for _, row in df.iterrows():
                    match_data = self._parse_match_row(row, file, league_name)
                    if match_data:
                        all_matches.append(match_data)
                        teams.add(match_data['home_team'])
                        teams.add(match_data['away_team'])
                        
            except Exception as e:
                print(f"   ❌ Error reading {file}: {e}")
        
        # Separate historical vs current season
        historical = []
        current_season = []
        fixtures = []
        
        current_year = 2025
        current_date = datetime(2025, 8, 18)  # Current date context
        
        for match in all_matches:
            match_date = datetime.strptime(match['date'], '%Y-%m-%d')
            
            if match['year'] < current_year:
                historical.append(match)
            elif match['year'] == current_year:
                if match_date <= current_date and match['result'] not in ['-:-', '', 'nan']:
                    current_season.append(match)
                else:
                    fixtures.append(match)
        
        print(f"   ✅ {league_name}: {len(teams)} teams, {len(historical)} historical, {len(current_season)} current, {len(fixtures)} fixtures")
        
        return {
            'league': league_name,
            'teams': teams,
            'historical_matches': historical,
            'current_season_matches': current_season,
            'fixtures': fixtures,
            'all_matches': all_matches
        }
    
    def _parse_match_row(self, row, filename: str, league: str) -> Optional[Dict]:
        """Parse a single match row"""
        try:
            # Handle different column formats
            if 'Date/Time' in row:
                # 2025 format
                date_time_str = str(row.get('Date/Time', ''))
                home_team = str(row.get('Home', '')).strip()
                away_team = str(row.get('Away', '')).strip()
                result = str(row.get('Result', '')).strip()
                
                # Parse combined date/time
                date_str, time_str = self._parse_datetime_combined(date_time_str)
            else:
                # 2023/2024 format
                date_str = str(row.get('Date', ''))
                time_str = str(row.get('Time', ''))
                home_team = str(row.get('Home team', '')).strip()
                away_team = str(row.get('Away team', '')).strip()
                result = str(row.get('Result', '')).strip()
            
            if pd.isna(home_team) or pd.isna(away_team) or home_team == '' or away_team == '':
                return None
            
            # Parse date
            date_obj = self._parse_date(date_str)
            if not date_obj:
                return None
            
            # Clean team names
            home_team = self._clean_team_name(home_team)
            away_team = self._clean_team_name(away_team)
            
            return {
                'date': date_obj.strftime('%Y-%m-%d'),
                'time': time_str if time_str != 'nan' else '',
                'home_team': home_team,
                'away_team': away_team,
                'result': result if result != 'nan' else '-:-',
                'league': league,
                'year': date_obj.year,
                'source_file': filename
            }
            
        except Exception as e:
            print(f"   ⚠️ Error parsing row: {e}")
            return None
    
    def _parse_datetime_combined(self, datetime_str: str) -> Tuple[str, str]:
        """Parse combined date/time string from 2025 format"""
        if not datetime_str or datetime_str == 'nan':
            return '', ''
        
        # Pattern: "Sat 3/1/25      4:00 PM"
        parts = datetime_str.strip().split()
        if len(parts) >= 3:
            # Extract date (skip day name)
            date_part = parts[1] if len(parts) > 1 else ''
            # Extract time (last parts)
            time_parts = parts[2:] if len(parts) > 2 else []
            time_part = ' '.join(time_parts) if time_parts else ''
            return date_part, time_part
        
        return datetime_str, ''
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str or date_str == 'nan':
            return None
            
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%m/%d/%y',
            '%d/%m/%y',
            'Sun %m/%d/%y',
            'Mon %m/%d/%y',
            'Tue %m/%d/%y',
            'Wed %m/%d/%y',
            'Thu %m/%d/%y',
            'Fri %m/%d/%y',
            'Sat %m/%d/%y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        
        # Try removing day names
        cleaned_date = re.sub(r'^(Sun|Mon|Tue|Wed|Thu|Fri|Sat)\s+', '', date_str)
        for fmt in ['%m/%d/%y', '%m/%d/%Y', '%d/%m/%y', '%d/%m/%Y']:
            try:
                return datetime.strptime(cleaned_date, fmt)
            except:
                continue
        
        return None
    
    def _clean_team_name(self, team_name: str) -> str:
        """Clean and standardize team names"""
        # Remove extra whitespace
        team_name = ' '.join(team_name.split())
        
        # Common standardizations
        replacements = {
            'Jalgpallikool Tammeka U21': 'Tammeka U21',
            'Läänemaa JK Haapsalu': 'Läänemaa JK',
            'JK Trans Narva U21': 'Trans Narva U21',
            'FC Kuressaare U21': 'Kuressaare U21',
            'Paide Linnameeskond U21': 'Paide U21',
            'FC Flora Tallinn U21': 'FC Flora U21',
            'Nomme United': 'FC Nomme United'
        }
        
        return replacements.get(team_name, team_name)
    
    def _analyze_league_structure(self, esiliiga_data: Dict, esiliiga_b_data: Dict):
        """Analyze the current league structure and team distribution"""
        print(f"\n🔍 LEAGUE STRUCTURE ANALYSIS")
        print("=" * 60)
        
        # Check for overlapping teams
        overlapping_teams = esiliiga_data['teams'].intersection(esiliiga_b_data['teams'])
        
        print(f"📊 Esiliiga: {len(esiliiga_data['teams'])} teams")
        print(f"📊 Esiliiga B: {len(esiliiga_b_data['teams'])} teams")
        
        if overlapping_teams:
            print(f"⚠️  Overlapping teams: {overlapping_teams}")
            print("   (This might indicate promotion/relegation between seasons)")
        
        # Current season team counts
        current_esiliiga_teams = set()
        current_esiliiga_b_teams = set()
        
        for match in esiliiga_data['current_season_matches'] + esiliiga_data['fixtures']:
            current_esiliiga_teams.add(match['home_team'])
            current_esiliiga_teams.add(match['away_team'])
            
        for match in esiliiga_b_data['current_season_matches'] + esiliiga_b_data['fixtures']:
            current_esiliiga_b_teams.add(match['home_team'])
            current_esiliiga_b_teams.add(match['away_team'])
        
        print(f"\n📅 Current Season (2025):")
        print(f"   Esiliiga: {len(current_esiliiga_teams)} teams")
        print(f"   Esiliiga B: {len(current_esiliiga_b_teams)} teams")
        
        # Store current teams for simulation
        self.current_esiliiga_teams = current_esiliiga_teams
        self.current_esiliiga_b_teams = current_esiliiga_b_teams
        
        return overlapping_teams
    
    def create_combined_datasets(self, esiliiga_data: Dict, esiliiga_b_data: Dict):
        """Create combined datasets for prediction"""
        print(f"\n💾 Creating combined datasets...")
        
        # Create historical training data (both leagues combined)
        historical_combined = []
        historical_combined.extend(esiliiga_data['historical_matches'])
        historical_combined.extend(esiliiga_b_data['historical_matches'])
        
        # Sort by date
        historical_combined.sort(key=lambda x: x['date'])
        
        # Create current season data for each league
        esiliiga_current = esiliiga_data['current_season_matches'] + esiliiga_data['fixtures']
        esiliiga_b_current = esiliiga_b_data['current_season_matches'] + esiliiga_b_data['fixtures']
        
        # Save to CSV files
        if historical_combined:
            self._save_to_csv(historical_combined, 'historical_combined.csv')
        if esiliiga_current:
            self._save_to_csv(esiliiga_current, 'esiliiga_2025.csv')
        if esiliiga_b_current:
            self._save_to_csv(esiliiga_b_current, 'esiliiga_b_2025.csv')
        
        print(f"   ✅ historical_combined.csv: {len(historical_combined)} matches")
        print(f"   ✅ esiliiga_2025.csv: {len(esiliiga_current)} matches")
        print(f"   ✅ esiliiga_b_2025.csv: {len(esiliiga_b_current)} matches")
        
        return historical_combined, esiliiga_current, esiliiga_b_current
    
    def _save_to_csv(self, matches: List[Dict], filename: str):
        """Save matches to CSV file"""
        if not matches:
            print(f"   ⚠️ No data to save for {filename}")
            return
            
        df = pd.DataFrame(matches)
        
        # Ensure we have the required columns
        required_cols = ['date', 'time', 'home_team', 'result', 'away_team']
        available_cols = []
        
        for col in required_cols:
            if col in df.columns:
                available_cols.append(col)
        
        # Add league column if available
        if 'league' in df.columns:
            available_cols.append('league')
        
        df_output = df[available_cols].copy()
        
        # Rename columns for output
        column_mapping = {
            'date': 'Date',
            'time': 'Time', 
            'home_team': 'Home Team',
            'result': 'Result',
            'away_team': 'Away Team',
            'league': 'League'
        }
        
        df_output.columns = [column_mapping.get(col, col) for col in df_output.columns]
        df_output.to_csv(filename, index=False)
    
    def simulate_promotion_relegation(self, esiliiga_table: List[Dict], esiliiga_b_table: List[Dict]) -> Dict:
        """Simulate promotion/relegation between leagues"""
        print(f"\n🔄 PROMOTION/RELEGATION SIMULATION")
        print("=" * 60)
        
        # Sort tables by points (descending for league, ascending for relegation positions)
        esiliiga_sorted = sorted(esiliiga_table, key=lambda x: (-x['points'], -x['goal_difference']))
        esiliiga_b_sorted = sorted(esiliiga_b_table, key=lambda x: (-x['points'], -x['goal_difference']))
        
        # Automatic movements
        relegated_teams = esiliiga_sorted[-self.auto_relegation_spots:]  # Bottom 2 from Esiliiga
        promoted_teams = esiliiga_b_sorted[:self.auto_promotion_spots]   # Top 2 from Esiliiga B
        
        # Playoff candidates
        playoff_relegation_candidate = esiliiga_sorted[-(self.auto_relegation_spots + 1)]  # 3rd from bottom in Esiliiga
        playoff_promotion_candidate = esiliiga_b_sorted[self.auto_promotion_spots]          # 3rd in Esiliiga B
        
        print(f"⬇️  Automatic Relegation from Esiliiga:")
        for team in relegated_teams:
            print(f"   {team['team']} ({team['points']} pts)")
        
        print(f"⬆️  Automatic Promotion from Esiliiga B:")
        for team in promoted_teams:
            print(f"   {team['team']} ({team['points']} pts)")
        
        print(f"🥊 Promotion/Relegation Playoff:")
        print(f"   Esiliiga: {playoff_relegation_candidate['team']} ({playoff_relegation_candidate['points']} pts)")
        print(f"   Esiliiga B: {playoff_promotion_candidate['team']} ({playoff_promotion_candidate['points']} pts)")
        
        # Simulate playoff (simple probability based on points difference)
        points_diff = playoff_promotion_candidate['points'] - playoff_relegation_candidate['points']
        promotion_prob = 0.5 + (points_diff * 0.05)  # Base 50% + 5% per point difference
        promotion_prob = max(0.2, min(0.8, promotion_prob))  # Clamp between 20-80%
        
        playoff_winner = playoff_promotion_candidate if np.random.random() < promotion_prob else playoff_relegation_candidate
        
        if playoff_winner == playoff_promotion_candidate:
            print(f"   🏆 Playoff Winner: {playoff_promotion_candidate['team']} (promoted to Esiliiga)")
            promoted_teams.append(playoff_promotion_candidate)
            relegated_teams.append(playoff_relegation_candidate)
        else:
            print(f"   🏆 Playoff Winner: {playoff_relegation_candidate['team']} (stays in Esiliiga)")
        
        return {
            'promoted_teams': [team['team'] for team in promoted_teams],
            'relegated_teams': [team['team'] for team in relegated_teams],
            'playoff_winner': playoff_winner['team'],
            'playoff_loser': playoff_promotion_candidate['team'] if playoff_winner == playoff_relegation_candidate else playoff_relegation_candidate['team']
        }

def main():
    """Main execution function"""
    print("🇪🇪 ESTONIAN FOOTBALL LEAGUE SYSTEM")
    print("=" * 60)
    print("Processing complete two-tier league structure with promotion/relegation")
    
    # Initialize system
    league_system = EstonianLeagueSystem()
    
    # Load all data
    esiliiga_data, esiliiga_b_data = league_system.load_all_data()
    
    # Create combined datasets
    historical_combined, esiliiga_current, esiliiga_b_current = league_system.create_combined_datasets(esiliiga_data, esiliiga_b_data)
    
    print(f"\n🎯 SUMMARY:")
    print(f"   📚 Historical matches: {len(historical_combined)}")
    print(f"   🏆 Esiliiga 2025: {len(esiliiga_current)} matches")
    print(f"   🥈 Esiliiga B 2025: {len(esiliiga_b_current)} matches")
    print(f"   ⚽ Current Esiliiga teams: {len(league_system.current_esiliiga_teams)}")
    print(f"   ⚽ Current Esiliiga B teams: {len(league_system.current_esiliiga_b_teams)}")
    
    print(f"\n✅ Data processing complete!")
    print(f"📁 Files created: historical_combined.csv, esiliiga_2025.csv, esiliiga_b_2025.csv")

if __name__ == "__main__":
    main()
