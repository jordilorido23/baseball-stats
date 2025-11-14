"""
Player Similarity and Comparable Analysis.

This module finds similar players based on statistical profiles using:
- Cosine similarity (direction of statistical vectors)
- Euclidean distance (magnitude differences)
- K-Nearest Neighbors (configurable distance metrics)
- Weighted similarity (prioritize certain stats)

Applications:
- Scouting: "Find me AAA players similar to Yordan Alvarez"
- Trade targeting: "Who in the market plays like our needs?"
- Free agent comps: "What did similar players sign for?"
- Development: "Which successful players had similar minor league profiles?"
- Projection: "Similar players' career arcs"

Key Features:
- Multiple distance metrics (cosine, euclidean, mahalanobis)
- Feature weighting and normalization
- Age-adjusted comparisons
- Position filtering
- Min/max constraints (PA, IP thresholds)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Literal
import warnings

try:
    from sklearn.neighbors import NearestNeighbors
    from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn required. Install with: pip install scikit-learn")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False


class PlayerSimilarityFinder:
    """
    Find similar players based on statistical profiles.

    Uses distance-based similarity in multi-dimensional stat space.
    Can weight features, filter by position/age, and adjust for context.

    Example:
        >>> finder = PlayerSimilarityFinder()
        >>>
        >>> # Find AAA players similar to Yordan Alvarez
        >>> similar = finder.find_similar_players(
        ...     player_name="Yordan Alvarez",
        ...     player_df=mlb_stats,
        ...     candidate_df=aaa_stats,
        ...     features=['wRC+', 'K%', 'BB%', 'ISO', 'BABIP'],
        ...     n_matches=10,
        ...     metric='cosine'
        ... )
        >>>
        >>> print(similar[['player_name', 'similarity_score', 'wRC+', 'Age']])
    """

    def __init__(self, random_state: int = 42):
        """
        Initialize similarity finder.

        Args:
            random_state: Random seed for reproducibility
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for similarity analysis")

        self.random_state = random_state
        self.scaler = None
        self.feature_weights = None

    def find_similar_players(
        self,
        player_name: str,
        player_df: pd.DataFrame,
        candidate_df: Optional[pd.DataFrame] = None,
        features: Optional[List[str]] = None,
        n_matches: int = 10,
        metric: Literal['cosine', 'euclidean', 'manhattan'] = 'cosine',
        normalize: bool = True,
        feature_weights: Optional[Dict[str, float]] = None,
        position_filter: Optional[List[str]] = None,
        age_window: Optional[Tuple[int, int]] = None,
        exclude_self: bool = True
    ) -> pd.DataFrame:
        """
        Find players most similar to a target player.

        Args:
            player_name: Name of target player
            player_df: DataFrame containing target player
            candidate_df: DataFrame to search for similar players
                         (if None, searches within player_df)
            features: List of stat columns to use for similarity
            n_matches: Number of similar players to return
            metric: Distance metric ('cosine', 'euclidean', 'manhattan')
            normalize: Whether to standardize features
            feature_weights: Dictionary of feature weights (e.g., {'wRC+': 2.0, 'K%': 1.0})
            position_filter: Only consider these positions
            age_window: (min_age, max_age) to filter candidates
            exclude_self: Exclude target player from results

        Returns:
            DataFrame with similar players and similarity scores
        """
        # Default features for batters
        if features is None:
            features = ['wRC+', 'K%', 'BB%', 'ISO', 'BABIP', 'Spd']

        # Use same dataframe if no candidates provided
        if candidate_df is None:
            candidate_df = player_df.copy()

        # Find target player
        target_row = player_df[
            player_df['Name'].str.contains(player_name, case=False, na=False)
        ]

        if len(target_row) == 0:
            raise ValueError(f"Player '{player_name}' not found in player_df")

        if len(target_row) > 1:
            warnings.warn(f"Multiple matches for '{player_name}'. Using first match.")
            target_row = target_row.head(1)

        # Extract target feature vector
        available_features = [f for f in features if f in player_df.columns]
        target_vector = target_row[available_features].values[0]

        # Prepare candidate pool
        candidates = candidate_df.copy()

        # Apply filters
        if position_filter:
            candidates = candidates[candidates['Pos'].isin(position_filter)]

        if age_window:
            min_age, max_age = age_window
            candidates = candidates[
                (candidates['Age'] >= min_age) & (candidates['Age'] <= max_age)
            ]

        # Exclude target player if needed
        if exclude_self:
            candidates = candidates[
                ~candidates['Name'].str.contains(player_name, case=False, na=False)
            ]

        # Extract candidate feature matrix
        candidate_matrix = candidates[available_features].fillna(
            candidates[available_features].median()
        ).values

        # Normalize features
        if normalize:
            self.scaler = StandardScaler()
            # Fit on combined data for consistent scaling
            combined = np.vstack([target_vector.reshape(1, -1), candidate_matrix])
            self.scaler.fit(combined)

            target_vector_scaled = self.scaler.transform(target_vector.reshape(1, -1))[0]
            candidate_matrix_scaled = self.scaler.transform(candidate_matrix)
        else:
            target_vector_scaled = target_vector
            candidate_matrix_scaled = candidate_matrix

        # Apply feature weights if provided
        if feature_weights:
            self.feature_weights = np.array([
                feature_weights.get(f, 1.0) for f in available_features
            ])
            target_vector_scaled = target_vector_scaled * self.feature_weights
            candidate_matrix_scaled = candidate_matrix_scaled * self.feature_weights

        # Compute similarity scores
        if metric == 'cosine':
            # Cosine similarity: dot product of normalized vectors
            similarities = cosine_similarity(
                target_vector_scaled.reshape(1, -1),
                candidate_matrix_scaled
            )[0]
            # Convert to 0-100 scale (cosine is -1 to 1, usually 0 to 1 for positive features)
            similarity_scores = similarities * 100

        elif metric == 'euclidean':
            # Euclidean distance: convert to similarity (smaller distance = more similar)
            distances = euclidean_distances(
                target_vector_scaled.reshape(1, -1),
                candidate_matrix_scaled
            )[0]
            # Convert to similarity score (invert and scale)
            max_distance = distances.max()
            similarity_scores = (1 - distances / max_distance) * 100

        elif metric == 'manhattan':
            # Manhattan (L1) distance
            distances = np.sum(
                np.abs(target_vector_scaled - candidate_matrix_scaled),
                axis=1
            )
            max_distance = distances.max()
            similarity_scores = (1 - distances / max_distance) * 100

        else:
            raise ValueError(f"Unknown metric: {metric}")

        # Add similarity scores to candidates
        candidates = candidates.copy()
        candidates['similarity_score'] = similarity_scores

        # Sort by similarity
        similar_players = candidates.sort_values(
            'similarity_score', ascending=False
        ).head(n_matches)

        return similar_players.reset_index(drop=True)

    def find_comps_knn(
        self,
        player_name: str,
        player_df: pd.DataFrame,
        candidate_df: Optional[pd.DataFrame] = None,
        features: Optional[List[str]] = None,
        n_neighbors: int = 10,
        algorithm: Literal['auto', 'ball_tree', 'kd_tree', 'brute'] = 'auto',
        metric: str = 'minkowski'
    ) -> pd.DataFrame:
        """
        Find comps using K-Nearest Neighbors algorithm.

        More efficient for large datasets than pairwise similarity.

        Args:
            player_name: Target player name
            player_df: DataFrame with target player
            candidate_df: Candidate pool (if None, uses player_df)
            features: Features for comparison
            n_neighbors: Number of neighbors to find
            algorithm: KNN algorithm variant
            metric: Distance metric

        Returns:
            DataFrame with nearest neighbors
        """
        # Default features
        if features is None:
            features = ['wRC+', 'K%', 'BB%', 'ISO', 'BABIP']

        if candidate_df is None:
            candidate_df = player_df.copy()

        # Find target
        target_row = player_df[
            player_df['Name'].str.contains(player_name, case=False, na=False)
        ]

        if len(target_row) == 0:
            raise ValueError(f"Player '{player_name}' not found")

        target_vector = target_row[[f for f in features if f in player_df.columns]].values

        # Prepare candidates
        candidate_matrix = candidate_df[
            [f for f in features if f in candidate_df.columns]
        ].fillna(candidate_df[[f for f in features if f in candidate_df.columns]].median()).values

        # Standardize
        scaler = StandardScaler()
        candidate_matrix_scaled = scaler.fit_transform(candidate_matrix)
        target_vector_scaled = scaler.transform(target_vector)

        # Fit KNN
        knn = NearestNeighbors(
            n_neighbors=n_neighbors + 1,  # +1 to potentially include self
            algorithm=algorithm,
            metric=metric
        )
        knn.fit(candidate_matrix_scaled)

        # Find neighbors
        distances, indices = knn.kneighbors(target_vector_scaled)

        # Get similar players
        similar_indices = indices[0][1:]  # Exclude first (likely self)
        similar_distances = distances[0][1:]

        similar_players = candidate_df.iloc[similar_indices].copy()
        similar_players['distance'] = similar_distances
        similar_players['similarity_score'] = (
            1 - similar_distances / similar_distances.max()
        ) * 100

        return similar_players.reset_index(drop=True)

    def compare_player_profiles(
        self,
        player1_name: str,
        player2_name: str,
        player_df: pd.DataFrame,
        features: Optional[List[str]] = None
    ) -> Dict:
        """
        Direct comparison of two specific players.

        Args:
            player1_name: First player
            player2_name: Second player
            player_df: DataFrame with both players
            features: Features to compare

        Returns:
            Dictionary with comparison metrics
        """
        if features is None:
            features = ['wRC+', 'K%', 'BB%', 'ISO', 'BABIP']

        # Find players
        player1 = player_df[
            player_df['Name'].str.contains(player1_name, case=False, na=False)
        ].head(1)

        player2 = player_df[
            player_df['Name'].str.contains(player2_name, case=False, na=False)
        ].head(1)

        if len(player1) == 0 or len(player2) == 0:
            raise ValueError("One or both players not found")

        # Extract vectors
        available_features = [f for f in features if f in player_df.columns]
        vec1 = player1[available_features].values[0]
        vec2 = player2[available_features].values[0]

        # Compute similarities
        cosine_sim = cosine_similarity(vec1.reshape(1, -1), vec2.reshape(1, -1))[0, 0]
        euclidean_dist = np.linalg.norm(vec1 - vec2)

        # Percent differences
        pct_diffs = {}
        for i, feat in enumerate(available_features):
            if vec1[i] != 0:
                pct_diffs[feat] = ((vec2[i] - vec1[i]) / vec1[i]) * 100
            else:
                pct_diffs[feat] = np.nan

        return {
            'player1': player1_name,
            'player2': player2_name,
            'cosine_similarity': float(cosine_sim),
            'euclidean_distance': float(euclidean_dist),
            'percent_differences': pct_diffs,
            'player1_stats': dict(zip(available_features, vec1)),
            'player2_stats': dict(zip(available_features, vec2))
        }

    def find_historical_comps(
        self,
        player_stats: Dict[str, float],
        historical_df: pd.DataFrame,
        age: int,
        features: Optional[List[str]] = None,
        n_matches: int = 10,
        age_tolerance: int = 2
    ) -> pd.DataFrame:
        """
        Find historical comparables at a specific age.

        Useful for projections: "Which players had similar stats at age 24?"

        Args:
            player_stats: Dictionary of current player stats
            historical_df: Historical player-season data
            age: Age to match on
            features: Stats to compare
            n_matches: Number of comps to return
            age_tolerance: +/- age window

        Returns:
            DataFrame with historical comps
        """
        if features is None:
            features = list(player_stats.keys())

        # Filter to similar age
        age_filtered = historical_df[
            (historical_df['Age'] >= age - age_tolerance) &
            (historical_df['Age'] <= age + age_tolerance)
        ].copy()

        # Create target vector from player_stats
        target_vector = np.array([player_stats[f] for f in features if f in player_stats])

        # Extract candidate matrix
        candidate_matrix = age_filtered[
            [f for f in features if f in age_filtered.columns]
        ].fillna(age_filtered[[f for f in features if f in age_filtered.columns]].median()).values

        # Standardize
        scaler = StandardScaler()
        combined = np.vstack([target_vector.reshape(1, -1), candidate_matrix])
        scaler.fit(combined)

        target_scaled = scaler.transform(target_vector.reshape(1, -1))
        candidate_scaled = scaler.transform(candidate_matrix)

        # Compute cosine similarity
        similarities = cosine_similarity(target_scaled, candidate_scaled)[0]

        age_filtered['similarity_score'] = similarities * 100

        return age_filtered.sort_values('similarity_score', ascending=False).head(n_matches)

    def plot_similarity_radar(
        self,
        player_name: str,
        comp_names: List[str],
        player_df: pd.DataFrame,
        features: List[str],
        save_path: Optional[str] = None
    ):
        """
        Create radar chart comparing player to comps.

        Args:
            player_name: Target player
            comp_names: List of comparable player names
            player_df: DataFrame with all players
            features: Features to plot
            save_path: Path to save figure
        """
        if not PLOTTING_AVAILABLE:
            raise ImportError("matplotlib required for plotting")

        # Get player data
        players = [player_name] + comp_names
        player_data = []

        for name in players:
            row = player_df[
                player_df['Name'].str.contains(name, case=False, na=False)
            ].head(1)
            if len(row) > 0:
                player_data.append(row[features].values[0])

        if len(player_data) == 0:
            raise ValueError("No players found")

        # Normalize to 0-100 percentile ranks
        player_matrix = np.array(player_data)
        normalized = np.zeros_like(player_matrix)

        for i in range(player_matrix.shape[1]):
            # Percentile rank (0-100)
            from scipy import stats
            normalized[:, i] = stats.rankdata(player_matrix[:, i]) / len(player_matrix) * 100

        # Radar chart
        angles = np.linspace(0, 2 * np.pi, len(features), endpoint=False).tolist()
        angles += angles[:1]  # Complete the circle

        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

        for i, name in enumerate(players):
            values = normalized[i].tolist()
            values += values[:1]  # Complete the circle

            ax.plot(angles, values, 'o-', linewidth=2, label=name)
            ax.fill(angles, values, alpha=0.15)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(features, size=11)
        ax.set_ylim(0, 100)
        ax.set_title(f"Player Comparison: {player_name} vs Comps",
                    size=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        ax.grid(True)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.tight_layout()
        return fig, ax
