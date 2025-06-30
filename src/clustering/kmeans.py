from sklearn.cluster import KMeans
import numpy as np

class TeamClustering:
    def __init__(self, n_clusters=3):
        self.n_clusters = n_clusters
        self.model = KMeans(n_clusters=self.n_clusters)

    def fit(self, performance_metrics):
        """
        Fit the KMeans model to the performance metrics of teams.

        Parameters:
        performance_metrics (np.ndarray): A 2D array where each row represents a team's performance metrics.
        """
        self.model.fit(performance_metrics)

    def predict(self, new_metrics):
        """
        Predict the cluster for new team performance metrics.

        Parameters:
        new_metrics (np.ndarray): A 2D array where each row represents new performance metrics for teams.

        Returns:
        np.ndarray: Cluster labels for each team.
        """
        return self.model.predict(new_metrics)

    def get_cluster_centers(self):
        """
        Get the coordinates of cluster centers.

        Returns:
        np.ndarray: Coordinates of cluster centers.
        """
        return self.model.cluster_centers_

    def get_labels(self):
        """
        Get the labels of the clusters for the training data.

        Returns:
        np.ndarray: Cluster labels for the training data.
        """
        return self.model.labels_