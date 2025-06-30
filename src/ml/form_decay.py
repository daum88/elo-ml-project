import numpy as np
import pandas as pd

class FormDecayModel:
    def __init__(self, decay_rate=0.9):
        self.decay_rate = decay_rate

    def apply_decay(self, performance_data):
        """
        Apply exponential decay to the performance data.
        
        Parameters:
        performance_data (list): A list of performance metrics (e.g., goals scored).
        
        Returns:
        np.array: Decayed performance metrics.
        """
        decayed_performance = np.zeros(len(performance_data))
        for i in range(len(performance_data)):
            decayed_performance[i] = performance_data[i] * (self.decay_rate ** i)
        return decayed_performance

    def fit(self, historical_data):
        """
        Fit the model to historical performance data.
        
        Parameters:
        historical_data (pd.DataFrame): A DataFrame containing historical performance metrics.
        
        Returns:
        None
        """
        # Implement fitting logic here (e.g., optimizing decay_rate based on historical data)
        pass

    def predict(self, recent_performance):
        """
        Predict future performance based on recent performance metrics.
        
        Parameters:
        recent_performance (list): A list of recent performance metrics.
        
        Returns:
        float: Predicted future performance metric.
        """
        decayed_performance = self.apply_decay(recent_performance)
        return np.sum(decayed_performance) / np.sum(self.decay_rate ** np.arange(len(recent_performance)))