"""
Prospect success predictor - predicts MLB success probability based on MiLB stats.

Uses machine learning to identify which minor league statistics best predict
major league performance.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Literal
from pathlib import Path
import pickle

try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import classification_report, roc_auc_score, mean_squared_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. Install to use predictive models.")


class ProspectPredictor:
    """
    Predict prospect success using minor league statistics.

    Models include:
    - MLB arrival probability (will they make it?)
    - Expected MLB performance (how good will they be?)
    - Optimal promotion timing (are they ready?)
    """

    def __init__(self, model_dir: str = "data/models"):
        """
        Initialize the prospect predictor.

        Args:
            model_dir: Directory to save/load trained models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self.arrival_model = None
        self.performance_model = None
        self.scaler = None

        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required. Install with: pip install scikit-learn")

    def engineer_features(
        self,
        df: pd.DataFrame,
        level: str = 'AAA',
        player_type: Literal['batter', 'pitcher'] = 'batter'
    ) -> pd.DataFrame:
        """
        Engineer features from raw minor league stats.

        Key insight: Age-adjusted performance matters more than raw stats.

        Args:
            df: DataFrame with minor league stats
            level: Minor league level (AAA, AA, A+, A, Rk)
            player_type: 'batter' or 'pitcher'

        Returns:
            DataFrame with engineered features
        """
        features = df.copy()

        # Age adjustment (younger performance = more impressive)
        if 'Age' in features.columns:
            # Typical ages by level
            expected_ages = {
                'AAA': 26,
                'AA': 24,
                'A+': 23,
                'A': 22,
                'Rk': 20
            }
            expected_age = expected_ages.get(level, 24)
            features['age_differential'] = expected_age - features['Age']
            features['is_young_for_level'] = (features['age_differential'] > 1).astype(int)
            features['is_old_for_level'] = (features['age_differential'] < -2).astype(int)

        if player_type == 'batter':
            # Batter features
            if 'wRC+' in features.columns:
                features['elite_wrc'] = (features['wRC+'] >= 130).astype(int)

            if 'K%' in features.columns and 'BB%' in features.columns:
                # K/BB ratio (lower is better)
                features['k_bb_ratio'] = features['K%'] / (features['BB%'] + 0.1)  # Avoid div by 0
                features['elite_discipline'] = ((features['K%'] < 20) & (features['BB%'] > 10)).astype(int)

            if 'ISO' in features.columns:
                # Power indicator
                features['has_power'] = (features['ISO'] >= 0.200).astype(int)

            if 'BABIP' in features.columns and 'AVG' in features.columns:
                # True talent estimate (remove BABIP luck)
                features['babip_neutral_avg'] = features['AVG'] - (features['BABIP'] - 0.300)

            if 'SB' in features.columns and 'PA' in features.columns:
                # Speed score
                features['sb_per_pa'] = features['SB'] / (features['PA'] + 1)

        else:  # pitcher
            if 'FIP' in features.columns:
                features['elite_fip'] = (features['FIP'] < 3.50).astype(int)

            if 'K/9' in features.columns and 'BB/9' in features.columns:
                features['k_bb_ratio'] = features['K/9'] / (features['BB/9'] + 0.1)
                features['elite_command'] = ((features['K/9'] > 9) & (features['BB/9'] < 3)).astype(int)

            if 'K%' in features.columns:
                features['elite_k_rate'] = (features['K%'] > 25).astype(int)

            if 'SwStr%' in features.columns:
                # Swinging strike rate - strong predictor
                features['elite_stuff'] = (features['SwStr%'] > 12).astype(int)

            if 'GB%' in features.columns:
                # Ground ball rate
                features['ground_ball_pitcher'] = (features['GB%'] > 50).astype(int)

        return features

    def create_training_data(
        self,
        milb_df: pd.DataFrame,
        mlb_df: pd.DataFrame,
        player_id_col: str = 'playerid',
        success_metric: str = 'WAR',
        success_threshold: float = 2.0
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Create training data by matching prospects to MLB outcomes.

        Args:
            milb_df: Minor league player data
            mlb_df: MLB player data (with outcomes)
            player_id_col: Column to join on
            success_metric: Metric to define success (WAR, wRC+, etc.)
            success_threshold: Threshold for "success" label

        Returns:
            Tuple of (features DataFrame, labels Series)
        """
        # Merge MiLB and MLB data
        merged = milb_df.merge(
            mlb_df[[player_id_col, success_metric]],
            on=player_id_col,
            how='inner'
        )

        # Create binary success label
        merged['mlb_success'] = (merged[success_metric] >= success_threshold).astype(int)

        # Separate features and labels
        feature_cols = [col for col in merged.columns
                       if col not in [player_id_col, success_metric, 'mlb_success', 'Name', 'Team']]

        X = merged[feature_cols]
        y = merged['mlb_success']

        return X, y

    def train_arrival_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict:
        """
        Train a model to predict MLB arrival probability.

        Args:
            X: Feature DataFrame
            y: Labels (1 = made MLB, 0 = did not)
            test_size: Fraction of data for testing
            random_state: Random seed

        Returns:
            Dictionary with model performance metrics
        """
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train Random Forest
        self.arrival_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=random_state,
            class_weight='balanced'
        )

        self.arrival_model.fit(X_train_scaled, y_train)

        # Evaluate
        train_score = self.arrival_model.score(X_train_scaled, y_train)
        test_score = self.arrival_model.score(X_test_scaled, y_test)

        y_pred_proba = self.arrival_model.predict_proba(X_test_scaled)[:, 1]
        auc_score = roc_auc_score(y_test, y_pred_proba)

        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': self.arrival_model.feature_importances_
        }).sort_values('importance', ascending=False)

        return {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'auc_score': auc_score,
            'feature_importance': feature_importance,
            'n_train': len(X_train),
            'n_test': len(X_test)
        }

    def predict_arrival_probability(
        self,
        prospect_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Predict MLB arrival probability for prospects.

        Args:
            prospect_df: DataFrame with prospect features

        Returns:
            DataFrame with arrival probabilities added
        """
        if self.arrival_model is None or self.scaler is None:
            raise ValueError("Model not trained. Call train_arrival_model first.")

        result = prospect_df.copy()

        # Scale features
        X_scaled = self.scaler.transform(prospect_df)

        # Predict probabilities
        probabilities = self.arrival_model.predict_proba(X_scaled)[:, 1]

        result['mlb_arrival_probability'] = probabilities
        result['mlb_arrival_likelihood'] = pd.cut(
            probabilities,
            bins=[0, 0.25, 0.50, 0.75, 1.0],
            labels=['Low', 'Medium', 'High', 'Very High']
        )

        return result

    def get_key_predictive_features(
        self,
        player_type: Literal['batter', 'pitcher'] = 'batter',
        top_n: int = 10
    ) -> List[str]:
        """
        Get the most predictive features from the trained model.

        Args:
            player_type: 'batter' or 'pitcher'
            top_n: Number of features to return

        Returns:
            List of top feature names
        """
        if self.arrival_model is None:
            raise ValueError("Model not trained yet.")

        feature_importance = pd.DataFrame({
            'feature': self.arrival_model.feature_names_in_,
            'importance': self.arrival_model.feature_importances_
        }).sort_values('importance', ascending=False)

        return feature_importance.head(top_n)['feature'].tolist()

    def save_model(self, filename: str = 'prospect_model.pkl'):
        """
        Save trained model to disk.

        Args:
            filename: Name of file to save
        """
        if self.arrival_model is None:
            raise ValueError("No model to save. Train model first.")

        filepath = self.model_dir / filename

        model_data = {
            'arrival_model': self.arrival_model,
            'scaler': self.scaler
        }

        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

        print(f"Model saved to {filepath}")

    def load_model(self, filename: str = 'prospect_model.pkl'):
        """
        Load trained model from disk.

        Args:
            filename: Name of file to load
        """
        filepath = self.model_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")

        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)

        self.arrival_model = model_data['arrival_model']
        self.scaler = model_data['scaler']

        print(f"Model loaded from {filepath}")

    def rank_prospects(
        self,
        prospect_df: pd.DataFrame,
        level: str = 'AAA',
        player_type: Literal['batter', 'pitcher'] = 'batter',
        min_pa: int = 50
    ) -> pd.DataFrame:
        """
        Rank prospects by predicted MLB success.

        Args:
            prospect_df: DataFrame with prospect stats
            level: Minor league level
            player_type: 'batter' or 'pitcher'
            min_pa: Minimum plate appearances/innings

        Returns:
            DataFrame with ranked prospects
        """
        # Filter qualified prospects
        if player_type == 'batter':
            qualified = prospect_df[prospect_df['PA'] >= min_pa].copy()
        else:
            qualified = prospect_df[prospect_df['IP'] >= min_pa].copy()

        if len(qualified) == 0:
            return pd.DataFrame()

        # Engineer features
        featured = self.engineer_features(qualified, level, player_type)

        # Get feature columns that model expects
        if self.arrival_model is not None:
            model_features = self.arrival_model.feature_names_in_
            # Only use features that exist in both
            available_features = [f for f in model_features if f in featured.columns]

            # Predict
            predictions = self.predict_arrival_probability(featured[available_features])

            # Combine original data with predictions
            result = qualified.copy()
            result['mlb_probability'] = predictions['mlb_arrival_probability']
            result['mlb_likelihood'] = predictions['mlb_arrival_likelihood']

            # Rank
            result = result.sort_values('mlb_probability', ascending=False)

            return result

        else:
            # If no model trained, rank by traditional metrics
            if player_type == 'batter':
                if 'wRC+' in qualified.columns:
                    return qualified.sort_values('wRC+', ascending=False)
            else:
                if 'FIP' in qualified.columns:
                    return qualified.sort_values('FIP', ascending=True)

            return qualified
