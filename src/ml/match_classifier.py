from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd

class MatchClassifier:
    def __init__(self, model='logistic'):
        if model == 'logistic':
            self.classifier = LogisticRegression()
        elif model == 'xgboost':
            self.classifier = XGBClassifier()
        else:
            raise ValueError("Model must be 'logistic' or 'xgboost'.")

    def train(self, X, y):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.classifier.fit(X_train, y_train)
        predictions = self.classifier.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        print(f"Model accuracy: {accuracy:.2f}")
        print(classification_report(y_test, predictions))

    def predict(self, X):
        return self.classifier.predict(X)

    def predict_proba(self, X):
        return self.classifier.predict_proba(X)