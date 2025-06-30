from sklearn.linear_model import PoissonRegressor
import numpy as np
import pandas as pd

class PoissonModel:
    def __init__(self):
        self.model = PoissonRegressor()

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def score(self, X, y):
        return self.model.score(X, y)

    def get_params(self):
        return self.model.get_params()

    def set_params(self, **params):
        self.model.set_params(**params)