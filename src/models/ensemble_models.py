"""
Ensemble Machine Learning Models for Prospect Prediction.

This module implements model stacking and ensemble methods that combine
multiple base models for improved prediction accuracy and robustness.

Ensemble Approaches:
- Stacking: Meta-learner trains on base model predictions
- Voting: Aggregate predictions from multiple models (hard/soft)
- Bagging: Bootstrap aggregating for variance reduction
- Boosting: Sequential error correction (XGBoost, LightGBM)

Key Advantages:
- Better than any single model (bias-variance tradeoff)
- Captures different aspects of data (diverse models)
- More robust to overfitting
- Industry-standard practice in ML competitions

This is what modern ML teams actually use in production, not just single models.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Literal
import warnings

try:
    from sklearn.ensemble import (
        RandomForestClassifier,
        GradientBoostingClassifier,
        VotingClassifier,
        StackingClassifier
    )
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import (
        train_test_split,
        cross_val_score,
        StratifiedKFold
    )
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import (
        accuracy_score,
        roc_auc_score,
        classification_report,
        confusion_matrix,
        log_loss
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn required. Install with: pip install scikit-learn")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    warnings.warn("XGBoost optional. Install with: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    warnings.warn("LightGBM optional. Install with: pip install lightgbm")


class EnsembleProspectPredictor:
    """
    Ensemble model for prospect MLB success prediction.

    Combines multiple base models (Random Forest, XGBoost, Logistic Regression)
    using stacking or voting to improve prediction accuracy.

    Example:
        >>> ensemble = EnsembleProspectPredictor(ensemble_type='stacking')
        >>> ensemble.train(X_train, y_train)
        >>> predictions = ensemble.predict_proba(X_test)
        >>> print(f"ROC-AUC: {ensemble.evaluate(X_test, y_test)['roc_auc']:.3f}")
    """

    def __init__(
        self,
        ensemble_type: Literal['stacking', 'voting', 'weighted'] = 'stacking',
        random_state: int = 42
    ):
        """
        Initialize ensemble predictor.

        Args:
            ensemble_type: Type of ensemble
                - 'stacking': Meta-learner on base model predictions
                - 'voting': Soft voting across base models
                - 'weighted': Weighted average based on validation performance
            random_state: Random seed
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for ensemble models")

        self.ensemble_type = ensemble_type
        self.random_state = random_state
        self.ensemble_model = None
        self.base_models = {}
        self.scaler = StandardScaler()
        self.feature_names = None
        self.model_weights = None

    def _create_base_models(self) -> List[Tuple[str, object]]:
        """
        Create base models for ensemble.

        Returns:
            List of (name, model) tuples
        """
        base_models = []

        # 1. Random Forest (good for capturing non-linear interactions)
        base_models.append((
            'rf',
            RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                min_samples_split=20,
                min_samples_leaf=10,
                class_weight='balanced',
                random_state=self.random_state,
                n_jobs=-1
            )
        ))

        # 2. Gradient Boosting (sequential error correction)
        base_models.append((
            'gb',
            GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=self.random_state
            )
        ))

        # 3. XGBoost (if available - industry standard)
        if XGBOOST_AVAILABLE:
            base_models.append((
                'xgb',
                xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.random_state,
                    eval_metric='logloss'
                )
            ))

        # 4. LightGBM (if available - faster than XGBoost)
        if LIGHTGBM_AVAILABLE:
            base_models.append((
                'lgbm',
                lgb.LGBMClassifier(
                    n_estimators=100,
                    max_depth=5,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.random_state,
                    verbose=-1
                )
            ))

        # 5. Logistic Regression (linear baseline)
        base_models.append((
            'lr',
            LogisticRegression(
                penalty='l2',
                C=1.0,
                class_weight='balanced',
                max_iter=1000,
                random_state=self.random_state
            )
        ))

        return base_models

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        validation_split: float = 0.2,
        cv_folds: int = 5
    ) -> Dict:
        """
        Train ensemble model.

        Args:
            X: Feature matrix
            y: Target labels
            validation_split: Validation set size for weighted ensemble
            cv_folds: Cross-validation folds for model evaluation

        Returns:
            Dictionary with training results
        """
        self.feature_names = X.columns.tolist()

        # Standardize features (helps linear models)
        X_scaled = self.scaler.fit_transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=X.columns)

        # Create base models
        base_models = self._create_base_models()

        if self.ensemble_type == 'stacking':
            # Stacking: Meta-learner trained on base model predictions
            # Meta-learner is Logistic Regression on cross-validated predictions
            self.ensemble_model = StackingClassifier(
                estimators=base_models,
                final_estimator=LogisticRegression(
                    random_state=self.random_state,
                    max_iter=1000
                ),
                cv=cv_folds,
                n_jobs=-1
            )
            self.ensemble_model.fit(X_scaled_df, y)

        elif self.ensemble_type == 'voting':
            # Soft voting: Average predicted probabilities
            self.ensemble_model = VotingClassifier(
                estimators=base_models,
                voting='soft',
                n_jobs=-1
            )
            self.ensemble_model.fit(X_scaled_df, y)

        elif self.ensemble_type == 'weighted':
            # Weighted average based on validation performance
            X_train, X_val, y_train, y_val = train_test_split(
                X_scaled_df, y,
                test_size=validation_split,
                random_state=self.random_state,
                stratify=y
            )

            # Train each base model and compute validation AUC
            model_scores = []
            for name, model in base_models:
                model.fit(X_train, y_train)
                self.base_models[name] = model

                # Validation performance
                val_proba = model.predict_proba(X_val)[:, 1]
                val_auc = roc_auc_score(y_val, val_proba)
                model_scores.append(val_auc)

            # Convert to weights (softmax)
            model_scores = np.array(model_scores)
            exp_scores = np.exp(model_scores - model_scores.max())
            self.model_weights = exp_scores / exp_scores.sum()

        # Evaluate with cross-validation
        cv_scores = cross_val_score(
            self.ensemble_model if self.ensemble_type != 'weighted' else base_models[0][1],
            X_scaled_df,
            y,
            cv=cv_folds,
            scoring='roc_auc'
        )

        results = {
            'ensemble_type': self.ensemble_type,
            'n_base_models': len(base_models),
            'cv_mean_auc': cv_scores.mean(),
            'cv_std_auc': cv_scores.std(),
            'base_models': [name for name, _ in base_models]
        }

        if self.ensemble_type == 'weighted':
            results['model_weights'] = dict(zip(
                [name for name, _ in base_models],
                self.model_weights
            ))

        return results

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class probabilities.

        Args:
            X: Feature matrix

        Returns:
            Array of shape (n_samples, 2) with class probabilities
        """
        if self.ensemble_model is None and not self.base_models:
            raise ValueError("Model not trained. Call train() first.")

        # Standardize
        X_scaled = self.scaler.transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=self.feature_names)

        if self.ensemble_type in ['stacking', 'voting']:
            return self.ensemble_model.predict_proba(X_scaled_df)

        elif self.ensemble_type == 'weighted':
            # Weighted average of base model predictions
            predictions = []
            for name, model in self.base_models.items():
                pred_proba = model.predict_proba(X_scaled_df)[:, 1]
                predictions.append(pred_proba)

            predictions = np.array(predictions)  # (n_models, n_samples)
            weighted_pred = (predictions.T @ self.model_weights)  # (n_samples,)

            # Return in (n_samples, 2) format
            return np.column_stack([1 - weighted_pred, weighted_pred])

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class labels.

        Args:
            X: Feature matrix

        Returns:
            Array of predicted labels (0 or 1)
        """
        proba = self.predict_proba(X)
        return (proba[:, 1] >= 0.5).astype(int)

    def evaluate(
        self,
        X: pd.DataFrame,
        y: pd.Series
    ) -> Dict[str, float]:
        """
        Evaluate model on test data.

        Args:
            X: Test features
            y: Test labels

        Returns:
            Dictionary with evaluation metrics
        """
        y_pred = self.predict(X)
        y_proba = self.predict_proba(X)[:, 1]

        return {
            'accuracy': accuracy_score(y, y_pred),
            'roc_auc': roc_auc_score(y, y_proba),
            'log_loss': log_loss(y, y_proba)
        }

    def get_feature_importance(
        self,
        method: Literal['mean', 'voting_weight'] = 'mean'
    ) -> pd.DataFrame:
        """
        Extract feature importance from ensemble.

        Args:
            method: How to aggregate importance across models
                - 'mean': Average importance across base models
                - 'voting_weight': Weighted by model performance

        Returns:
            DataFrame with feature importance scores
        """
        if self.ensemble_type == 'weighted':
            # Get importance from each base model
            importances = []
            for name, model in self.base_models.items():
                if hasattr(model, 'feature_importances_'):
                    imp = model.feature_importances_
                    importances.append(imp)

            if len(importances) == 0:
                raise ValueError("No base models have feature_importances_")

            importances = np.array(importances)

            if method == 'mean':
                avg_importance = importances.mean(axis=0)
            elif method == 'voting_weight':
                # Weighted average by model performance
                weights = self.model_weights[:len(importances)]
                avg_importance = (importances.T @ weights) / weights.sum()

            importance_df = pd.DataFrame({
                'feature': self.feature_names,
                'importance': avg_importance
            }).sort_values('importance', ascending=False)

            return importance_df

        elif self.ensemble_type in ['stacking', 'voting']:
            # Get from first base estimator that has feature_importances_
            for estimator in self.ensemble_model.estimators_:
                if hasattr(estimator, 'feature_importances_'):
                    importance_df = pd.DataFrame({
                        'feature': self.feature_names,
                        'importance': estimator.feature_importances_
                    }).sort_values('importance', ascending=False)
                    return importance_df

            raise ValueError("No estimators have feature_importances_")

    def compare_base_models(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> pd.DataFrame:
        """
        Compare performance of individual base models.

        Args:
            X_test: Test features
            y_test: Test labels

        Returns:
            DataFrame with model comparison
        """
        if self.ensemble_type != 'weighted':
            raise ValueError("Base model comparison only available for weighted ensemble")

        X_scaled = self.scaler.transform(X_test)
        X_scaled_df = pd.DataFrame(X_scaled, columns=self.feature_names)

        results = []
        for name, model in self.base_models.items():
            y_pred = model.predict(X_scaled_df)
            y_proba = model.predict_proba(X_scaled_df)[:, 1]

            results.append({
                'model': name,
                'accuracy': accuracy_score(y_test, y_pred),
                'roc_auc': roc_auc_score(y_test, y_proba),
                'log_loss': log_loss(y_test, y_proba),
                'weight': self.model_weights[list(self.base_models.keys()).index(name)]
            })

        # Add ensemble performance
        y_pred_ens = self.predict(X_test)
        y_proba_ens = self.predict_proba(X_test)[:, 1]

        results.append({
            'model': 'ensemble',
            'accuracy': accuracy_score(y_test, y_pred_ens),
            'roc_auc': roc_auc_score(y_test, y_proba_ens),
            'log_loss': log_loss(y_test, y_proba_ens),
            'weight': 1.0
        })

        return pd.DataFrame(results).sort_values('roc_auc', ascending=False)


class ModelCalibrator:
    """
    Calibrate probability predictions to match observed frequencies.

    Ensures that when model predicts 70% probability, 70% of those cases
    are actually positive (calibration).

    Uses isotonic regression or Platt scaling.
    """

    def __init__(self, method: Literal['isotonic', 'sigmoid'] = 'isotonic'):
        """
        Initialize calibrator.

        Args:
            method: Calibration method
                - 'isotonic': Non-parametric, monotonic
                - 'sigmoid': Parametric (Platt scaling)
        """
        from sklearn.calibration import CalibratedClassifierCV
        self.method = method
        self.calibrator = None

    def calibrate(
        self,
        model: object,
        X_cal: pd.DataFrame,
        y_cal: pd.Series
    ):
        """
        Calibrate model on calibration set.

        Args:
            model: Trained model with predict_proba method
            X_cal: Calibration features
            y_cal: Calibration labels
        """
        from sklearn.calibration import CalibratedClassifierCV

        self.calibrator = CalibratedClassifierCV(
            model,
            method=self.method,
            cv='prefit'  # Model already trained
        )
        self.calibrator.fit(X_cal, y_cal)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict calibrated probabilities.

        Args:
            X: Features

        Returns:
            Calibrated probabilities
        """
        return self.calibrator.predict_proba(X)
