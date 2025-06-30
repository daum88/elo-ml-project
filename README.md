# Elo ML Project

## Overview
The Elo ML Project is designed to implement and enhance the Elo rating system using machine learning techniques. This project includes various modules for parameter calibration, expected goals prediction, match outcome classification, form decay modeling, and team clustering.

## Project Structure
```
elo-ml-project
├── src
│   ├── __init__.py
│   ├── elo.py
│   ├── calibration
│   │   ├── __init__.py
│   │   └── grid_search.py
│   ├── ml
│   │   ├── __init__.py
│   │   ├── poisson_regressor.py
│   │   ├── match_classifier.py
│   │   └── form_decay.py
│   ├── clustering
│   │   ├── __init__.py
│   │   └── kmeans.py
│   └── utils
│       ├── __init__.py
│       └── data_loader.py
├── data
│   └── README.md
├── requirements.txt
├── README.md
└── notebooks
    └── parameter_calibration.ipynb
```

## Installation
To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd elo-ml-project
pip install -r requirements.txt
```

## Usage
- **Elo Rating System**: The main logic for the Elo rating system can be found in `src/elo.py`. This module includes functions for processing fixtures, simulating games, and calculating expected scores.
- **Parameter Calibration**: Use the `src/calibration/grid_search.py` for optimizing parameters such as the Poisson base, K, and weights.
- **Machine Learning Models**: 
  - `src/ml/poisson_regressor.py` implements a Poisson regression model to predict expected goals.
  - `src/ml/match_classifier.py` contains a classifier for predicting match outcomes.
  - `src/ml/form_decay.py` models form decay using exponential weighting or machine learning techniques.
- **Clustering**: The `src/clustering/kmeans.py` file implements KMeans clustering to categorize teams based on performance metrics.
- **Data Loading**: Utility functions for loading and preprocessing data are located in `src/utils/data_loader.py`.

## Notebooks
The `notebooks/parameter_calibration.ipynb` provides an interactive environment for experimenting with parameter calibration techniques.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License
This project is licensed under the MIT License. See the LICENSE file for details.