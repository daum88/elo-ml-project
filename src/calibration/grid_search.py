from sklearn.model_selection import GridSearchCV
from sklearn.metrics import make_scorer
import numpy as np

def optimize_poisson_params(model, param_grid, X, y, scoring='neg_mean_squared_error', cv=5):
    scorer = make_scorer(scoring)
    grid_search = GridSearchCV(estimator=model, param_grid=param_grid, scoring=scorer, cv=cv)
    grid_search.fit(X, y)
    return grid_search.best_params_, grid_search.best_score_

def optimize_k_params(model, param_grid, X, y, scoring='neg_mean_squared_error', cv=5):
    scorer = make_scorer(scoring)
    grid_search = GridSearchCV(estimator=model, param_grid=param_grid, scoring=scorer, cv=cv)
    grid_search.fit(X, y)
    return grid_search.best_params_, grid_search.best_score_

def optimize_weights(model, param_grid, X, y, scoring='neg_mean_squared_error', cv=5):
    scorer = make_scorer(scoring)
    grid_search = GridSearchCV(estimator=model, param_grid=param_grid, scoring=scorer, cv=cv)
    grid_search.fit(X, y)
    return grid_search.best_params_, grid_search.best_score_