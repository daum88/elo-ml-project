# Estonian Football Time Machine - Clean Version

## Overview
This is a cleaned and refactored version of the Estonian Football Time Machine project. All unnecessary development files have been removed, leaving only the essential components for realistic Estonian football predictions.

## Core Features
- **Realistic ELO Ratings**: Based on 235 actual 2025 match results (118 Esiliiga + 117 Esiliiga B)
- **Dynamic Performance Tracking**: Teams show varying attacking/defensive capabilities and form
- **Accurate League Structure**: Proper 10+10 team Estonian football hierarchy
- **Complete Simulation**: Match predictions, league tables, team analysis, season simulation

## Core Files

### Essential Application Files
- `enhanced_estonian_predictor_fixed.py` - Main prediction engine with real match data processing
- `estonian_football_time_machine_final.py` - Complete GUI application with all features
- `estonian_league_system.py` - League classification and team management
- `launch.py` - Clean application launcher

### Data Files
- `esiliiga2025.csv` - Actual Esiliiga match results (118 matches)
- `esiliigab2025.csv` - Actual Esiliiga B match results (117 matches)

### Configuration
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch Application**:
   ```bash
   python3 estonian_football_time_machine_final.py
   ```

3. **Use the GUI**:
   - **Match Prediction Tab**: Predict individual matches
   - **League Tables Tab**: View current standings
   - **Team Analysis Tab**: Analyze team performance and promotion chances
   - **Season Simulation Tab**: Run full season simulations

## Key Improvements in Clean Version

### Realistic ELO Ratings
- **Tammeka U21**: 1346.4 ELO (18/20) - Reflects actual poor performance
- **FC Nomme United**: 1698.0 ELO (1/20) - Reflects league leadership
- **Dynamic Range**: All teams show varied characteristics based on actual results

### Data Processing
- Processes 235 actual matches from 2025 season
- Real win/loss/draw statistics drive ELO calculations
- Dynamic characteristics updated based on recent performance

### Clean Architecture
- Removed 21,000+ development artifacts and dependency files
- Retained only 8 essential files
- Clear separation of prediction engine and GUI components

## Team Rankings (Based on Actual 2025 Results)

### Top Teams
1. FC Nomme United (1698.0)
2. Viimsi JK (1675.2) 
3. Tartu JK Welco (1640.1)

### Bottom Teams
18. Paide U21 (1450.0)
19. FC Nomme U21 (1450.0)
20. Jalgpallikool Tammeka U21 (1346.4)

## Technical Notes
- Built with Python 3.10+
- Uses pandas for data processing, tkinter for GUI
- ELO ratings calculated from actual match results
- League structure matches Estonian football system
