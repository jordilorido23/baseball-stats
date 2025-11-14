"""
Contract Structure Optimization for MLB Free Agents.

This module provides tools to analyze and optimize MLB contract structures beyond
simple $/WAR calculations. It models:

1. Net Present Value (NPV) of deferred money contracts
2. Opt-out clause valuation via Monte Carlo simulation
3. Performance bonus optimization (PA/IP thresholds)
4. Risk-adjusted contract valuations

Created: November 13, 2025
Author: Baseball Analytics Portfolio
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


@dataclass
class ContractStructure:
    """Represents a contract structure with various terms."""
    total_value: float  # Total stated value in millions
    years: int
    aav: float  # Average annual value
    deferred_pct: float = 0.0  # Percentage deferred
    deferral_years: int = 0  # Years until deferrals start paying
    opt_outs: List[int] = None  # Years when player can opt out
    incentives_total: float = 0.0  # Total possible incentive money

    def __post_init__(self):
        """Calculate AAV if not provided."""
        if self.aav == 0:
            self.aav = self.total_value / self.years if self.years > 0 else 0
        if self.opt_outs is None:
            self.opt_outs = []


class ContractStructureOptimizer:
    """
    Optimize MLB contract structures using financial modeling.

    Key Features:
    - NPV calculation for deferred money contracts
    - Monte Carlo simulation for opt-out valuations
    - Performance bonus optimization
    - Risk-adjusted contract analysis
    """

    def __init__(self, discount_rate: float = 0.05):
        """
        Initialize contract optimizer.

        Args:
            discount_rate: Annual discount rate for NPV (default 5%)
        """
        self.discount_rate = discount_rate

        # Position-specific aging curves (annual WAR decline rate)
        self.aging_curves = {
            'SP': 0.92,   # Starting pitchers decline ~8% per year
            'RP': 0.90,   # Relievers decline ~10% per year
            'C': 0.93,    # Catchers decline ~7% per year
            '1B': 0.95,   # First basemen
            '2B': 0.94,   # Second basemen
            '3B': 0.94,   # Third basemen
            'SS': 0.94,   # Shortstops
            'OF': 0.95,   # Outfielders
            'CF': 0.95,   # Center fielders
            'RF': 0.95,   # Right fielders
            'LF': 0.95,   # Left fielders
            'DH': 0.96    # Designated hitters
        }

    def calculate_npv(
        self,
        contract: ContractStructure,
        discount_rate: Optional[float] = None
    ) -> Dict:
        """
        Calculate Net Present Value of a contract.

        This accounts for time value of money, especially critical for
        deferred compensation contracts (e.g., Ohtani, Betts).

        Args:
            contract: Contract structure to evaluate
            discount_rate: Override default discount rate

        Returns:
            Dictionary with NPV analysis
        """
        # Validate inputs
        if contract.total_value < 0:
            raise ValueError("Contract total_value must be non-negative")

        if contract.years <= 0:
            return {
                'stated_value': contract.total_value,
                'npv': 0.0,
                'deferral_discount': 0.0,
                'discount_from_stated': 0.0,
                'discount_pct': 0.0,
                'stated_aav': 0.0,
                'effective_aav': 0.0,
                'cbt_aav': 0.0,
                'cbt_savings_per_year': 0.0,
                'discount_rate_used': discount_rate if discount_rate is not None else self.discount_rate,
                'pv_breakdown': {'non_deferred': 0.0, 'deferred': 0.0}
            }

        rate = discount_rate if discount_rate is not None else self.discount_rate

        # Annual salary without deferrals
        annual_salary = contract.total_value / contract.years

        # Calculate present value of non-deferred portion
        non_deferred_value = contract.total_value * (1 - contract.deferred_pct)
        deferred_value = contract.total_value * contract.deferred_pct

        # PV of non-deferred payments (paid during contract)
        pv_non_deferred = 0.0
        for year in range(contract.years):
            payment = annual_salary * (1 - contract.deferred_pct)
            pv_non_deferred += payment / ((1 + rate) ** year)

        # PV of deferred payments (paid after contract ends)
        pv_deferred = 0.0
        if contract.deferred_pct > 0 and contract.deferral_years > 0:
            # Deferred amount split equally over deferral period
            annual_deferred = deferred_value / contract.deferral_years

            for year in range(contract.deferral_years):
                # Start paying after contract ends
                discount_year = contract.years + year
                pv_deferred += annual_deferred / ((1 + rate) ** discount_year)
        elif contract.deferred_pct > 0:
            # If no deferral structure specified, assume paid over same period
            # but starting after contract ends
            annual_deferred = deferred_value / contract.years
            for year in range(contract.years):
                discount_year = contract.years + year
                pv_deferred += annual_deferred / ((1 + rate) ** discount_year)

        total_npv = pv_non_deferred + pv_deferred

        # Calculate luxury tax value (CBT = NPV for deferred contracts)
        cbt_aav = total_npv / contract.years

        # Calculate effective AAV (NPV-based AAV)
        effective_aav = total_npv / contract.years

        # Deferral discount is the difference between stated and NPV
        deferral_discount = contract.total_value - total_npv

        return {
            'stated_value': contract.total_value,
            'npv': round(total_npv, 2),
            'deferral_discount': round(deferral_discount, 2),
            'discount_from_stated': round(deferral_discount, 2),  # Keep for backward compat
            'discount_pct': round((1 - total_npv / contract.total_value) * 100, 1) if contract.total_value > 0 else 0,
            'stated_aav': round(contract.aav, 2),
            'effective_aav': round(effective_aav, 2),
            'cbt_aav': round(cbt_aav, 2),
            'cbt_savings_per_year': round(contract.aav - cbt_aav, 2),
            'discount_rate_used': rate,
            'pv_breakdown': {
                'non_deferred': round(pv_non_deferred, 2),
                'deferred': round(pv_deferred, 2)
            }
        }

    def value_opt_out_clause(
        self,
        contract: ContractStructure,
        current_war: float,
        position: str,
        current_age: int,
        dollars_per_war: float = 8.0,
        n_simulations: int = 10000,
        war_std: float = 1.5,
        market_inflation: float = 0.05,
        injury_rate: float = 0.15
    ) -> Dict:
        """
        Value opt-out clause (wrapper for simulate_opt_out_value with test-friendly interface).

        Args:
            contract: Contract structure
            current_war: Current WAR
            position: Position code
            current_age: Current age
            dollars_per_war: Market $/WAR rate
            n_simulations: Number of simulations
            war_std: WAR standard deviation
            market_inflation: Market inflation rate
            injury_rate: Injury probability

        Returns:
            Dictionary with opt-out analysis including expected_value_to_team
        """
        result = self.simulate_opt_out_value(
            contract, current_war, current_age, position,
            dollars_per_war, n_simulations, war_std, market_inflation, injury_rate
        )

        # Add expected_value_to_team and expected_years_played for test compatibility
        if 'error' not in result:
            # Expected value to team = years controlled * AAV
            result['expected_value_to_team'] = round(
                result['expected_years_controlled'] * contract.aav, 2
            )
            # Alias for test compatibility
            result['expected_years_played'] = result['expected_years_controlled']

        return result

    def simulate_opt_out_value(
        self,
        contract: ContractStructure,
        current_war: float,
        age: int,
        position: str,
        dollars_per_war: float = 8.0,
        n_simulations: int = 10000,
        war_std: float = 1.5,
        market_inflation: float = 0.05,
        injury_rate: float = 0.15
    ) -> Dict:
        """
        Monte Carlo simulation to value opt-out clauses.

        Simulates player performance and market conditions to estimate:
        1. Probability player exercises opt-out
        2. Expected years of team control
        3. Value to team vs value to player

        Args:
            contract: Contract structure (must include opt_outs)
            current_war: Player's current WAR
            age: Current age
            position: Position code
            dollars_per_war: Current $/WAR market rate
            n_simulations: Number of Monte Carlo iterations
            war_std: Standard deviation for WAR projections
            market_inflation: Annual market $/WAR inflation rate
            injury_rate: Annual probability of significant injury

        Returns:
            Dictionary with opt-out analysis
        """
        if not contract.opt_outs or len(contract.opt_outs) == 0:
            return {'error': 'Contract has no opt-out clauses'}

        # Get aging curve for position
        decline_rate = self.aging_curves.get(position, 0.94)

        results = []

        for _ in range(n_simulations):
            sim_result = {
                'years_played': contract.years,
                'opted_out': False,
                'opt_out_year': None,
                'war_path': [],
                'had_injury': False
            }

            cumulative_war = 0.0
            war_projection = current_war

            for year in range(contract.years):
                # Age player
                player_age = age + year

                # Apply aging curve with randomness
                expected_war = war_projection * (decline_rate ** year)

                # Add random variation
                actual_war = np.random.normal(expected_war, war_std)
                actual_war = max(0, actual_war)  # Can't be negative

                # Injury check
                if np.random.random() < injury_rate:
                    actual_war *= 0.5  # Injured season = 50% production
                    sim_result['had_injury'] = True

                sim_result['war_path'].append(actual_war)
                cumulative_war += actual_war

                # Check if player opts out this year
                if (year + 1) in contract.opt_outs:
                    # Calculate remaining contract value
                    years_remaining = contract.years - (year + 1)
                    remaining_value = contract.aav * years_remaining

                    # Project market value if player opts out
                    # Use recent performance (last 2-3 years avg)
                    recent_war = np.mean(sim_result['war_path'][-min(3, len(sim_result['war_path'])):])

                    # Project new contract (assume 5-7 years at market rate)
                    new_contract_years = max(3, min(7, 35 - player_age))

                    # Market $/WAR inflates each year
                    future_dollars_per_war = dollars_per_war * ((1 + market_inflation) ** year)

                    # Estimate new contract value
                    # Simplified: recent WAR * years * $/WAR with aging
                    projected_value = 0
                    for future_year in range(new_contract_years):
                        year_war = recent_war * (decline_rate ** future_year)
                        projected_value += year_war * future_dollars_per_war

                    # Opt out if new deal > remaining guarantee
                    if projected_value > remaining_value * 1.1:  # Need 10% premium to take risk
                        sim_result['opted_out'] = True
                        sim_result['opt_out_year'] = year + 1
                        sim_result['years_played'] = year + 1
                        sim_result['projected_new_value'] = projected_value
                        sim_result['remaining_old_value'] = remaining_value
                        break

            results.append(sim_result)

        # Analyze results
        opt_out_count = sum(1 for r in results if r['opted_out'])
        opt_out_prob = opt_out_count / n_simulations

        avg_years_controlled = np.mean([r['years_played'] for r in results])

        # Break down by opt-out year
        opt_out_year_breakdown = {}
        for opt_year in contract.opt_outs:
            count = sum(1 for r in results if r.get('opt_out_year') == opt_year)
            opt_out_year_breakdown[f'year_{opt_year}'] = {
                'count': count,
                'probability': count / n_simulations
            }

        # Calculate value implications
        # Team's perspective: prefer more years at below-market rate
        full_contract_years = contract.years
        expected_years = avg_years_controlled
        team_risk = opt_out_prob  # Higher = more risk of losing player early

        # Player's perspective: value of flexibility
        opted_out_sims = [r for r in results if r['opted_out']]
        if opted_out_sims:
            avg_gain_from_opt_out = np.mean([
                r.get('projected_new_value', 0) - r.get('remaining_old_value', 0)
                for r in opted_out_sims
            ])
        else:
            avg_gain_from_opt_out = 0

        return {
            'opt_out_probability': round(opt_out_prob, 3),
            'expected_years_controlled': round(avg_years_controlled, 2),
            'full_contract_years': full_contract_years,
            'years_at_risk': round(full_contract_years - avg_years_controlled, 2),
            'team_risk_score': round(team_risk * 100, 1),  # 0-100 scale
            'opt_out_year_breakdown': opt_out_year_breakdown,
            'player_flexibility_value': round(avg_gain_from_opt_out, 2) if avg_gain_from_opt_out > 0 else 0,
            'simulations_run': n_simulations,
            'parameters': {
                'war_std': war_std,
                'market_inflation': market_inflation,
                'injury_rate': injury_rate,
                'decline_rate': decline_rate
            }
        }

    def optimize_performance_bonuses(
        self,
        position: str,
        expected_pa_or_ip: float,
        pa_or_ip_std: float,
        bonus_pool: float,
        is_pitcher: bool = False
    ) -> Dict:
        """
        Optimize performance bonus thresholds (PA for batters, IP for pitchers).

        Finds optimal thresholds that:
        - Minimize overpay risk for teams (bonuses for below-expectation performance)
        - Provide meaningful upside for players
        - Account for injury probability

        Args:
            position: Position code
            expected_pa_or_ip: Expected plate appearances or innings pitched
            pa_or_ip_std: Standard deviation
            bonus_pool: Total bonus money available (millions)
            is_pitcher: True if pitcher, False if batter

        Returns:
            Dictionary with optimal bonus structure
        """
        metric_name = "IP" if is_pitcher else "PA"

        # Define potential thresholds
        if is_pitcher:
            # Pitcher thresholds: 140, 160, 180, 200, 220 IP
            base_thresholds = [140, 160, 180, 200, 220, 240]
        else:
            # Batter thresholds: 400, 500, 550, 600, 650 PA
            base_thresholds = [400, 500, 550, 600, 650, 700]

        # Filter to relevant thresholds based on expectation
        relevant_thresholds = [
            t for t in base_thresholds
            if expected_pa_or_ip * 0.7 <= t <= expected_pa_or_ip * 1.3
        ]

        if len(relevant_thresholds) < 3:
            # Add more if needed
            relevant_thresholds = base_thresholds

        # Calculate probability of hitting each threshold
        threshold_probs = []
        for threshold in relevant_thresholds:
            # Z-score
            z = (threshold - expected_pa_or_ip) / pa_or_ip_std
            # Probability of exceeding threshold (normal CDF)
            from scipy import stats
            prob = 1 - stats.norm.cdf(z)
            threshold_probs.append(prob)

        # Distribute bonus pool across thresholds
        # Use diminishing increments
        n_tiers = min(4, len(relevant_thresholds))
        selected_thresholds = relevant_thresholds[-n_tiers:]  # Take highest N
        selected_probs = threshold_probs[-n_tiers:]

        # Allocate bonus money: higher tiers = smaller increments
        bonus_increments = []
        remaining_pool = bonus_pool

        for i in range(n_tiers):
            if i == 0:
                increment = bonus_pool * 0.4  # 40% for first tier
            elif i == 1:
                increment = bonus_pool * 0.3  # 30% for second
            elif i == 2:
                increment = bonus_pool * 0.2  # 20% for third
            else:
                increment = bonus_pool * 0.1  # 10% for fourth

            bonus_increments.append(increment)

        # Calculate expected value to team
        expected_payout = sum(
            bonus * prob
            for bonus, prob in zip(bonus_increments, selected_probs)
        )

        # Build structure
        bonus_structure = []
        cumulative_bonus = 0
        for i, (threshold, increment, prob) in enumerate(
            zip(selected_thresholds, bonus_increments, selected_probs)
        ):
            cumulative_bonus += increment
            bonus_structure.append({
                'tier': i + 1,
                f'{metric_name}_threshold': threshold,
                'bonus_earned': round(increment, 2),
                'cumulative_bonus': round(cumulative_bonus, 2),
                'probability': round(prob, 3),
                'expected_value': round(increment * prob, 2)
            })

        return {
            'position': position,
            'metric': metric_name,
            'expected_baseline': round(expected_pa_or_ip, 0),
            'bonus_structure': bonus_structure,
            'total_bonus_pool': bonus_pool,
            'expected_payout': round(expected_payout, 2),
            'team_savings_expected': round(bonus_pool - expected_payout, 2),
            'overpay_risk': round(expected_payout / bonus_pool, 3)
        }

    def compare_contract_structures(
        self,
        player_name: str,
        structures: List[Tuple[str, ContractStructure]],
        current_war: float,
        age: int,
        position: str
    ) -> pd.DataFrame:
        """
        Compare multiple contract structures side-by-side.

        Args:
            player_name: Player name
            structures: List of (name, ContractStructure) tuples
            current_war: Current WAR
            age: Current age
            position: Position

        Returns:
            DataFrame comparing all structures
        """
        comparison_data = []

        for name, contract in structures:
            # Calculate NPV
            npv_analysis = self.calculate_npv(contract)

            # Simulate opt-outs if present
            if contract.opt_outs and len(contract.opt_outs) > 0:
                opt_out_analysis = self.simulate_opt_out_value(
                    contract, current_war, age, position, n_simulations=5000
                )
                opt_out_prob = opt_out_analysis['opt_out_probability']
                expected_years = opt_out_analysis['expected_years_controlled']
                team_risk = opt_out_analysis['team_risk_score']
            else:
                opt_out_prob = 0.0
                expected_years = contract.years
                team_risk = 0.0

            comparison_data.append({
                'player': player_name,
                'structure_name': name,
                'years': contract.years,
                'stated_value': contract.total_value,
                'stated_aav': contract.aav,
                'npv': npv_analysis['npv'],
                'npv_discount_pct': npv_analysis['discount_pct'],
                'cbt_aav': npv_analysis['cbt_aav'],
                'cbt_savings': npv_analysis['cbt_savings_per_year'],
                'deferred_pct': contract.deferred_pct * 100,
                'has_opt_outs': len(contract.opt_outs) > 0,
                'opt_out_probability': round(opt_out_prob, 3),
                'expected_years': round(expected_years, 1),
                'team_risk_score': round(team_risk, 1),
                'total_incentives': contract.incentives_total
            })

        return pd.DataFrame(comparison_data)

    def value_incentives(
        self,
        base_salary: float,
        incentive_structure: Dict,
        historical_achievement_rate: float = 0.5
    ) -> Dict:
        """
        Calculate expected value of performance incentives.

        Args:
            base_salary: Base salary in millions
            incentive_structure: Dict of incentive types and bonuses
            historical_achievement_rate: Historical probability of achieving bonuses

        Returns:
            Dictionary with incentive valuation
        """
        total_possible_incentives = 0.0
        expected_incentive_value = 0.0

        for incentive_type, details in incentive_structure.items():
            bonus = details.get('bonus', 0.0)
            # Use threshold-based probability if available, otherwise use historical rate
            prob = details.get('probability', historical_achievement_rate)

            total_possible_incentives += bonus
            expected_incentive_value += bonus * prob

        return {
            'base_salary': base_salary,
            'total_possible_incentives': round(total_possible_incentives, 2),
            'expected_incentive_value': round(expected_incentive_value, 2),
            'total_expected_value': round(base_salary + expected_incentive_value, 2),
            'incentive_achievement_rate': historical_achievement_rate
        }

    def calculate_risk_adjusted_value(
        self,
        contract: ContractStructure,
        injury_risk_score: float,
        performance_volatility: float = 0.10
    ) -> Dict:
        """
        Calculate risk-adjusted contract value based on injury and performance risk.

        Args:
            contract: Contract structure
            injury_risk_score: Injury risk score (0-100)
            performance_volatility: Performance volatility (0-1)

        Returns:
            Dictionary with risk-adjusted valuations
        """
        # Calculate injury risk discount
        if injury_risk_score < 20:  # Low risk
            injury_discount_pct = 0.0
        elif injury_risk_score < 40:  # Moderate risk
            injury_discount_pct = 0.10
        elif injury_risk_score < 60:  # High risk
            injury_discount_pct = 0.25
        else:  # Very high risk (60+)
            injury_discount_pct = 0.40

        # Calculate performance volatility discount
        # Higher volatility = more risk = larger discount
        volatility_discount_pct = min(performance_volatility * 0.5, 0.20)  # Cap at 20%

        # Combined risk discount (multiplicative)
        total_discount_pct = injury_discount_pct + volatility_discount_pct
        total_discount_pct = min(total_discount_pct, 0.50)  # Cap at 50%

        risk_discount = contract.total_value * total_discount_pct
        adjusted_value = contract.total_value * (1 - total_discount_pct)

        return {
            'stated_value': contract.total_value,
            'injury_risk_score': injury_risk_score,
            'injury_discount_pct': round(injury_discount_pct * 100, 1),
            'performance_volatility': performance_volatility,
            'volatility_discount_pct': round(volatility_discount_pct * 100, 1),
            'total_risk_discount_pct': round(total_discount_pct * 100, 1),
            'risk_discount': round(risk_discount, 2),
            'adjusted_value': round(adjusted_value, 2),
            'adjusted_aav': round(adjusted_value / contract.years, 2)
        }

    def compare_structures(
        self,
        structures,
        player_name: str = "Player",
        current_war: float = 3.0,
        age: int = 30,
        position: str = 'OF'
    ) -> pd.DataFrame:
        """
        Compare multiple contract structures (wrapper for compare_contract_structures).

        Args:
            structures: List of ContractStructure objects or List of (name, ContractStructure) tuples
            player_name: Player name
            current_war: Current WAR
            age: Current age
            position: Position

        Returns:
            DataFrame comparing all structures
        """
        # Handle both list of contracts and list of tuples
        if structures and not isinstance(structures[0], tuple):
            # Convert to tuples if just a list of ContractStructure objects
            structures = [(f"Structure {i+1}", s) for i, s in enumerate(structures)]

        return self.compare_contract_structures(
            player_name, structures, current_war, age, position
        )

    def generate_ohtani_style_contract(
        self,
        total_value: float,
        years: int,
        deferred_pct: float = 0.97,
        deferral_years: int = 10
    ) -> Tuple[ContractStructure, Dict]:
        """
        Generate an Ohtani-style heavily deferred contract.

        Args:
            total_value: Total contract value (millions)
            years: Contract years
            deferred_pct: Percentage to defer (default 97% like Ohtani)
            deferral_years: Years to pay out deferrals

        Returns:
            Tuple of (ContractStructure, NPV analysis)
        """
        contract = ContractStructure(
            total_value=total_value,
            years=years,
            aav=total_value / years,
            deferred_pct=deferred_pct,
            deferral_years=deferral_years
        )

        npv_analysis = self.calculate_npv(contract)

        return contract, npv_analysis
