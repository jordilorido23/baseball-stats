"""
Reliever Contract Market Value Model

Predicts market AAV for free agent relievers based on historical contracts (2020-2024).

Uses regression model:
    AAV ~ WAR + Saves + K/9 + Age + IsCloser + Year

Also provides:
- Historical comps (3-5 similar players)
- Market value confidence intervals
- Contract length recommendations
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from scipy import stats

from ..data.reliever_contract_database import get_contract_database, add_market_features


class RelieverContractMarketModel:
    """
    Model reliever free agent market values.

    Features:
    - Regression model for AAV prediction
    - Historical comp matching
    - Contract length recommendations
    """

    def __init__(self):
        """Initialize model with historical contract database."""
        self.contracts_df = get_contract_database()
        self.contracts_df = add_market_features(self.contracts_df)

        # Train regression model
        self.model = None
        self.scaler = None
        self._train_model()

    def _train_model(self):
        """Train AAV regression model."""

        # Features for regression
        features = ['WAR_Prev', 'Saves_Prev', 'K9_Prev', 'Age', 'Is_Closer', 'Is_High_K', 'Year_Signed']

        X = self.contracts_df[features].copy()
        y = self.contracts_df['AAV_$M'].copy()

        # Standardize features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Fit model
        self.model = LinearRegression()
        self.model.fit(X_scaled, y)

        # Calculate R^2
        r2 = self.model.score(X_scaled, y)
        print(f"Contract Market Model R^2: {r2:.3f}")

        # Show feature importance
        feature_importance = pd.DataFrame({
            'Feature': features,
            'Coefficient': self.model.coef_
        }).sort_values('Coefficient', ascending=False)

        print("\nFeature Importance (sorted by coefficient):")
        print(feature_importance.to_string(index=False))

    def predict_aav(
        self,
        war: float,
        saves: int,
        k9: float,
        age: int,
        is_closer: bool = False,
        contract_year: int = 2025
    ) -> Tuple[float, float, float]:
        """
        Predict market AAV for a free agent reliever.

        Args:
            war: WAR in most recent season
            saves: Saves in most recent season
            k9: K/9 in most recent season
            age: Age as of free agency
            is_closer: Whether player is a proven closer
            contract_year: Year of contract signing

        Returns:
            (predicted_aav, lower_ci, upper_ci) in millions
        """

        # Build feature vector
        is_high_k = 1 if k9 >= 12.0 else 0
        is_closer_int = 1 if is_closer else 0

        features = np.array([[war, saves, k9, age, is_closer_int, is_high_k, contract_year]])

        # Scale features
        features_scaled = self.scaler.transform(features)

        # Predict
        predicted_aav = self.model.predict(features_scaled)[0]

        # Confidence interval (±1 std error of estimate)
        # Use residual standard error from training
        residuals = self.contracts_df['AAV_$M'] - self.model.predict(
            self.scaler.transform(self.contracts_df[['WAR_Prev', 'Saves_Prev', 'K9_Prev', 'Age', 'Is_Closer', 'Is_High_K', 'Year_Signed']])
        )
        std_error = residuals.std()

        lower_ci = max(0, predicted_aav - 1.5 * std_error)
        upper_ci = predicted_aav + 1.5 * std_error

        return predicted_aav, lower_ci, upper_ci

    def find_comps(
        self,
        war: float,
        saves: int,
        k9: float,
        age: int,
        is_closer: bool = False,
        n_comps: int = 5
    ) -> pd.DataFrame:
        """
        Find historical comps (similar players).

        Uses distance metric:
            distance = |WAR - WAR_comp| + |Saves - Saves_comp|/30 + |K9 - K9_comp| + |Age - Age_comp|

        Args:
            war, saves, k9, age: Player stats
            is_closer: Whether player is closer
            n_comps: Number of comps to return

        Returns:
            DataFrame of historical comps sorted by similarity
        """

        # Filter to same role (closer vs setup)
        role_pool = self.contracts_df.copy()
        if is_closer:
            role_pool = role_pool[role_pool['Is_Closer'] == 1]
        else:
            role_pool = role_pool[role_pool['Is_Closer'] == 0]

        # Calculate distance
        def calculate_distance(row):
            war_dist = abs(row['WAR_Prev'] - war)
            saves_dist = abs(row['Saves_Prev'] - saves) / 30.0  # Normalize saves
            k9_dist = abs(row['K9_Prev'] - k9)
            age_dist = abs(row['Age'] - age)

            # Weighted distance (WAR most important)
            return 2.0 * war_dist + 0.5 * saves_dist + 1.0 * k9_dist + 0.5 * age_dist

        role_pool['Distance'] = role_pool.apply(calculate_distance, axis=1)

        # Sort by distance
        comps = role_pool.nsmallest(n_comps, 'Distance')[
            ['Name', 'Year_Signed', 'Age', 'Years', 'AAV_$M', 'WAR_Prev', 'Saves_Prev', 'K9_Prev', 'Role', 'Distance']
        ]

        return comps

    def recommend_contract_length(
        self,
        age: int,
        war: float,
        health_risk_score: int = 50
    ) -> Tuple[int, str]:
        """
        Recommend contract length based on age and health risk.

        Args:
            age: Player age
            war: Recent WAR
            health_risk_score: 0-100 (higher = more risk)

        Returns:
            (recommended_years, reasoning)
        """

        # Age-based recommendation
        if age <= 28:
            base_years = 4
            reasoning = "Young age supports multi-year deal"
        elif age <= 31:
            base_years = 3
            reasoning = "Prime age supports 3-year deal"
        elif age <= 34:
            base_years = 2
            reasoning = "Decline phase, shorter deal recommended"
        else:
            base_years = 1
            reasoning = "Age 35+, 1-year deals safer"

        # Adjust for health risk
        if health_risk_score >= 60:
            base_years = min(base_years, 1)
            reasoning += " (health risk mandates 1-year)"
        elif health_risk_score >= 40:
            base_years = min(base_years, 2)
            reasoning += " (health risk caps at 2-year)"

        # Adjust for WAR (elite players can command longer deals)
        if war >= 2.0 and age <= 32:
            base_years = min(base_years + 1, 5)
            reasoning += " (+1 year for elite production)"

        return base_years, reasoning

    def generate_market_report(
        self,
        name: str,
        war: float,
        saves: int,
        k9: float,
        age: int,
        is_closer: bool = False,
        health_risk_score: int = 50
    ) -> Dict:
        """
        Generate comprehensive market value report for a FA reliever.

        Returns:
            Dictionary with predicted AAV, comps, contract recommendation
        """

        # Predict AAV
        pred_aav, lower_ci, upper_ci = self.predict_aav(war, saves, k9, age, is_closer)

        # Find comps
        comps = self.find_comps(war, saves, k9, age, is_closer, n_comps=5)

        # Recommend contract length
        rec_years, reasoning = self.recommend_contract_length(age, war, health_risk_score)

        # Calculate total value
        total_value_low = lower_ci * rec_years
        total_value_mid = pred_aav * rec_years
        total_value_high = upper_ci * rec_years

        return {
            'Name': name,
            'Predicted_AAV_$M': pred_aav,
            'AAV_Range_Low_$M': lower_ci,
            'AAV_Range_High_$M': upper_ci,
            'Recommended_Years': rec_years,
            'Contract_Reasoning': reasoning,
            'Total_Value_Low_$M': total_value_low,
            'Total_Value_Mid_$M': total_value_mid,
            'Total_Value_High_$M': total_value_high,
            'Historical_Comps': comps
        }


if __name__ == "__main__":
    # Test the model
    print("="*80)
    print("RELIEVER CONTRACT MARKET MODEL - TEST")
    print("="*80)

    model = RelieverContractMarketModel()

    # Test case 1: Elite closer (Edwin Díaz-like)
    print("\n\nTest Case 1: Elite Closer (3.1 WAR, 32 saves, 13.3 K/9, age 32)")
    report = model.generate_market_report(
        name="Elite Closer Example",
        war=3.1,
        saves=32,
        k9=13.3,
        age=32,
        is_closer=True,
        health_risk_score=20
    )

    print(f"\nPredicted AAV: ${report['Predicted_AAV_$M']:.1f}M (${report['AAV_Range_Low_$M']:.1f}M - ${report['AAV_Range_High_$M']:.1f}M)")
    print(f"Recommended Contract: {report['Recommended_Years']} years")
    print(f"Total Value: ${report['Total_Value_Mid_$M']:.1f}M (${report['Total_Value_Low_$M']:.1f}M - ${report['Total_Value_High_$M']:.1f}M)")
    print(f"Reasoning: {report['Contract_Reasoning']}")
    print(f"\nHistorical Comps:")
    print(report['Historical_Comps'].to_string(index=False))

    # Test case 2: Setup man (1.5 WAR, 5 saves, 11.9 K/9, age 32)
    print("\n\n" + "="*80)
    print("Test Case 2: Elite Setup Man (1.5 WAR, 5 saves, 11.9 K/9, age 32)")
    report2 = model.generate_market_report(
        name="Elite Setup Example",
        war=1.5,
        saves=5,
        k9=11.9,
        age=32,
        is_closer=False,
        health_risk_score=25
    )

    print(f"\nPredicted AAV: ${report2['Predicted_AAV_$M']:.1f}M (${report2['AAV_Range_Low_$M']:.1f}M - ${report2['AAV_Range_High_$M']:.1f}M)")
    print(f"Recommended Contract: {report2['Recommended_Years']} years")
    print(f"Total Value: ${report2['Total_Value_Mid_$M']:.1f}M (${report2['Total_Value_Low_$M']:.1f}M - ${report2['Total_Value_High_$M']:.1f}M)")
    print(f"Reasoning: {report2['Contract_Reasoning']}")
    print(f"\nHistorical Comps:")
    print(report2['Historical_Comps'].to_string(index=False))
