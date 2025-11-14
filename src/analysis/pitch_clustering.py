"""
Pitch Arsenal Clustering and Similarity Analysis.

This module groups pitchers by their pitch characteristics using unsupervised
learning to identify similar arsenals and stuff profiles.

Applications:
- Scouting: "Which pitchers have similar stuff to Gerrit Cole?"
- Player acquisition: Find undervalued pitchers with elite stuff
- Development: Match prospects to successful pitchers with similar arsenals
- Trade targeting: Identify pitchers who fit team needs
- Injury replacement: Find pitchers with similar profiles

Clustering Methods:
- K-Means: Partition pitchers into distinct groups
- Hierarchical: Create dendrogram of pitcher similarities
- DBSCAN: Density-based clustering for outlier detection
- Gaussian Mixture: Soft clustering with probabilistic assignments

Features Used:
- Velocity (4-seam, 2-seam, slider, curve, change)
- Spin rate and spin axis
- Movement (horizontal/vertical break)
- Usage percentage (pitch mix)
- Stuff+ metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Literal
import warnings

try:
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.mixture import GaussianMixture
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score, davies_bouldin_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn required. Install with: pip install scikit-learn")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy.cluster.hierarchy import dendrogram, linkage
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False


class PitchArsenalClusterer:
    """
    Cluster pitchers by arsenal characteristics.

    Groups pitchers with similar stuff profiles using unsupervised learning.

    Example:
        >>> clusterer = PitchArsenalClusterer()
        >>> clusters = clusterer.cluster_pitchers(
        ...     pitcher_df,
        ...     features=['avg_velocity', 'avg_spin_rate', 'whiff_rate'],
        ...     n_clusters=5,
        ...     method='kmeans'
        ... )
        >>> print(clusters.groupby('cluster')['Name'].apply(list))
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize pitch clusterer.

        Args:
            random_state: Random seed for reproducibility
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for clustering")

        self.random_state = random_state
        self.scaler = StandardScaler()
        self.cluster_model = None
        self.feature_names = None

    def cluster_pitchers(
        self,
        pitcher_df: pd.DataFrame,
        features: Optional[List[str]] = None,
        n_clusters: int = 5,
        method: Literal['kmeans', 'hierarchical', 'dbscan', 'gmm'] = 'kmeans',
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Cluster pitchers into groups by arsenal similarity.

        Args:
            pitcher_df: DataFrame with pitcher stats
            features: Features to use for clustering
            n_clusters: Number of clusters (ignored for DBSCAN)
            method: Clustering algorithm
            normalize: Whether to standardize features

        Returns:
            DataFrame with cluster assignments added
        """
        # Default features for pitcher clustering
        if features is None:
            features = [
                'avg_velocity', 'avg_spin_rate', 'whiff_rate',
                'chase_rate', 'zone_contact_rate', 'K%', 'BB%'
            ]

        # Filter to available features
        available_features = [f for f in features if f in pitcher_df.columns]
        self.feature_names = available_features

        # Extract feature matrix
        X = pitcher_df[available_features].fillna(
            pitcher_df[available_features].median()
        ).values

        # Normalize
        if normalize:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = X

        # Cluster
        if method == 'kmeans':
            self.cluster_model = KMeans(
                n_clusters=n_clusters,
                random_state=self.random_state,
                n_init=10
            )
            clusters = self.cluster_model.fit_predict(X_scaled)

        elif method == 'hierarchical':
            self.cluster_model = AgglomerativeClustering(
                n_clusters=n_clusters,
                linkage='ward'
            )
            clusters = self.cluster_model.fit_predict(X_scaled)

        elif method == 'dbscan':
            self.cluster_model = DBSCAN(
                eps=0.5,
                min_samples=5
            )
            clusters = self.cluster_model.fit_predict(X_scaled)

        elif method == 'gmm':
            self.cluster_model = GaussianMixture(
                n_components=n_clusters,
                random_state=self.random_state
            )
            clusters = self.cluster_model.fit_predict(X_scaled)

        else:
            raise ValueError(f"Unknown method: {method}")

        # Add cluster assignments
        result = pitcher_df.copy()
        result['cluster'] = clusters

        # Add cluster summary stats
        cluster_profiles = result.groupby('cluster')[available_features].mean()
        result['cluster_profile'] = result['cluster'].map(
            lambda c: cluster_profiles.loc[c].to_dict()
        )

        return result

    def find_optimal_clusters(
        self,
        pitcher_df: pd.DataFrame,
        features: Optional[List[str]] = None,
        max_clusters: int = 10,
        method: Literal['elbow', 'silhouette', 'davies_bouldin'] = 'silhouette'
    ) -> Dict:
        """
        Find optimal number of clusters using various metrics.

        Args:
            pitcher_df: Pitcher data
            features: Features for clustering
            max_clusters: Maximum clusters to try
            method: Optimization criterion

        Returns:
            Dictionary with scores and optimal k
        """
        if features is None:
            features = [
                'avg_velocity', 'avg_spin_rate', 'whiff_rate',
                'K%', 'BB%'
            ]

        available_features = [f for f in features if f in pitcher_df.columns]
        X = pitcher_df[available_features].fillna(
            pitcher_df[available_features].median()
        ).values
        X_scaled = self.scaler.fit_transform(X)

        scores = []
        k_range = range(2, max_clusters + 1)

        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = kmeans.fit_predict(X_scaled)

            if method == 'elbow':
                # Within-cluster sum of squares
                score = kmeans.inertia_
            elif method == 'silhouette':
                # Silhouette coefficient (higher is better)
                score = silhouette_score(X_scaled, labels)
            elif method == 'davies_bouldin':
                # Davies-Bouldin index (lower is better)
                score = davies_bouldin_score(X_scaled, labels)

            scores.append(score)

        # Find optimal k
        scores_array = np.array(scores)
        if method == 'silhouette':
            optimal_k = k_range[scores_array.argmax()]
        elif method in ['elbow', 'davies_bouldin']:
            # Use elbow method: find point of diminishing returns
            # Simple heuristic: largest gap in second derivative
            if len(scores) > 2:
                second_deriv = np.diff(np.diff(scores_array))
                optimal_k = k_range[np.argmax(np.abs(second_deriv)) + 2]
            else:
                optimal_k = k_range[scores_array.argmin()]

        return {
            'k_range': list(k_range),
            'scores': scores,
            'optimal_k': optimal_k,
            'method': method
        }

    def describe_clusters(
        self,
        clustered_df: pd.DataFrame,
        features: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Generate summary statistics for each cluster.

        Args:
            clustered_df: DataFrame with cluster assignments
            features: Features to summarize

        Returns:
            DataFrame with cluster profiles
        """
        if 'cluster' not in clustered_df.columns:
            raise ValueError("DataFrame must have 'cluster' column")

        if features is None:
            features = self.feature_names or []

        available_features = [f for f in features if f in clustered_df.columns]

        # Summary stats per cluster
        cluster_summary = clustered_df.groupby('cluster')[available_features].agg([
            'mean', 'std', 'count'
        ])

        return cluster_summary

    def find_similar_pitchers(
        self,
        pitcher_name: str,
        clustered_df: pd.DataFrame,
        n_similar: int = 10
    ) -> pd.DataFrame:
        """
        Find pitchers in the same cluster as target pitcher.

        Args:
            pitcher_name: Target pitcher name
            clustered_df: DataFrame with cluster assignments
            n_similar: Number of similar pitchers to return

        Returns:
            DataFrame with similar pitchers
        """
        if 'cluster' not in clustered_df.columns:
            raise ValueError("DataFrame must have cluster assignments")

        # Find target pitcher
        target = clustered_df[
            clustered_df['Name'].str.contains(pitcher_name, case=False, na=False)
        ]

        if len(target) == 0:
            raise ValueError(f"Pitcher '{pitcher_name}' not found")

        target_cluster = target['cluster'].iloc[0]

        # Get pitchers in same cluster
        same_cluster = clustered_df[
            clustered_df['cluster'] == target_cluster
        ].copy()

        # Exclude target
        same_cluster = same_cluster[
            ~same_cluster['Name'].str.contains(pitcher_name, case=False, na=False)
        ]

        # Return top N
        return same_cluster.head(n_similar)

    def plot_cluster_dendrogram(
        self,
        pitcher_df: pd.DataFrame,
        features: Optional[List[str]] = None,
        save_path: Optional[str] = None
    ):
        """
        Create hierarchical clustering dendrogram.

        Args:
            pitcher_df: Pitcher data
            features: Features for clustering
            save_path: Path to save figure
        """
        if not PLOTTING_AVAILABLE:
            raise ImportError("matplotlib required for plotting")

        if features is None:
            features = [
                'avg_velocity', 'avg_spin_rate', 'whiff_rate',
                'K%', 'BB%'
            ]

        available_features = [f for f in features if f in pitcher_df.columns]
        X = pitcher_df[available_features].fillna(
            pitcher_df[available_features].median()
        ).values
        X_scaled = self.scaler.fit_transform(X)

        # Compute linkage
        Z = linkage(X_scaled, method='ward')

        # Plot
        fig, ax = plt.subplots(figsize=(15, 8))
        dendrogram(
            Z,
            labels=pitcher_df['Name'].values if 'Name' in pitcher_df.columns else None,
            leaf_rotation=90,
            leaf_font_size=8,
            ax=ax
        )
        ax.set_title('Hierarchical Clustering Dendrogram\n(Ward Linkage)',
                     fontsize=14, fontweight='bold')
        ax.set_xlabel('Pitcher', fontsize=12)
        ax.set_ylabel('Distance', fontsize=12)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.tight_layout()
        return fig, ax

    def plot_cluster_scatter(
        self,
        clustered_df: pd.DataFrame,
        x_feature: str,
        y_feature: str,
        save_path: Optional[str] = None
    ):
        """
        Scatter plot of clusters in 2D feature space.

        Args:
            clustered_df: DataFrame with cluster assignments
            x_feature: Feature for x-axis
            y_feature: Feature for y-axis
            save_path: Path to save figure
        """
        if not PLOTTING_AVAILABLE:
            raise ImportError("matplotlib required for plotting")

        if 'cluster' not in clustered_df.columns:
            raise ValueError("DataFrame must have cluster assignments")

        fig, ax = plt.subplots(figsize=(10, 8))

        for cluster in sorted(clustered_df['cluster'].unique()):
            cluster_data = clustered_df[clustered_df['cluster'] == cluster]
            ax.scatter(
                cluster_data[x_feature],
                cluster_data[y_feature],
                label=f'Cluster {cluster}',
                alpha=0.6,
                s=100
            )

        ax.set_xlabel(x_feature, fontsize=12)
        ax.set_ylabel(y_feature, fontsize=12)
        ax.set_title(f'Pitcher Clusters: {x_feature} vs {y_feature}',
                     fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.tight_layout()
        return fig, ax

    def plot_cluster_pca(
        self,
        clustered_df: pd.DataFrame,
        features: Optional[List[str]] = None,
        save_path: Optional[str] = None
    ):
        """
        Plot clusters in 2D PCA space.

        Args:
            clustered_df: DataFrame with cluster assignments
            features: Features used for clustering
            save_path: Path to save figure
        """
        if not PLOTTING_AVAILABLE:
            raise ImportError("matplotlib required for plotting")

        if features is None:
            features = self.feature_names or []

        available_features = [f for f in features if f in clustered_df.columns]
        X = clustered_df[available_features].fillna(
            clustered_df[available_features].median()
        ).values
        X_scaled = self.scaler.fit_transform(X)

        # PCA to 2D
        pca = PCA(n_components=2, random_state=self.random_state)
        X_pca = pca.fit_transform(X_scaled)

        # Plot
        fig, ax = plt.subplots(figsize=(10, 8))

        for cluster in sorted(clustered_df['cluster'].unique()):
            cluster_mask = clustered_df['cluster'] == cluster
            ax.scatter(
                X_pca[cluster_mask, 0],
                X_pca[cluster_mask, 1],
                label=f'Cluster {cluster}',
                alpha=0.6,
                s=100
            )

        ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)',
                     fontsize=12)
        ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)',
                     fontsize=12)
        ax.set_title('Pitcher Clusters in PCA Space',
                     fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(alpha=0.3)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.tight_layout()
        return fig, ax
