# Estonian Football League Simulator

Monte Carlo simulation of Premium Liiga, Esiliiga, and Esiliiga B using league-calibrated ELO ratings.

## Run
```
python ui_app.py
```

## Data
73 CSV files covering 1997-2025, 3 leagues, 11,000+ matches.

## Features
- League table projections with Monte Carlo simulation
- Team deep analysis with position/points distributions
- Season browser with individual game logs
- Match prediction with scoreline distributions
- What-if scenarios: replay seasons, historic matchups, custom leagues

## League Calibration
- PL-ESL gap: 690 ELO (from 8 promotion playoff matches)
- ESL-ESB gap: 53 ELO (from 8 playoff matches + 17 promotion events)
