#!/usr/bin/env python3
"""
Advanced Reliever Market Intelligence Analysis

Main orchestration script that combines all analysis phases:
1. Pitch Physics (VAA, SSW, Tunneling)
2. Arsenal Synergy (Gyro/Sweeper, Effective Velocity, Cognitive Load)
3. Biomechanics (Release Point, Fatigue Units, Extension)
4. Diamond Detector (Composite scoring)
5. Advanced Reporting (Pitcher profiles, executive summary)

Usage:
    python analyze_reliever_market_intelligence.py
"""

import pandas as pd
import numpy as np
import pybaseball as pyb
from typing import List, Dict
import sys
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analysis.pitch_physics_analyzer import PitchPhysicsAnalyzer
from analysis.arsenal_synergy_analyzer import ArsenalSynergyAnalyzer
from analysis.biomechanics_analyzer import BiomechanicsAnalyzer
from analysis.diamond_detector import DiamondDetector, analyze_reliever_complete, rank_free_agents
from analysis.advanced_reporting import AdvancedReporter


class RelieverMarketIntelligence:
    """Main orchestrator for advanced reliever market analysis."""

    def __init__(self, season: int = 2024):
        """
        Initialize the market intelligence analyzer.

        Args:
            season: Season to analyze (use 2024 since 2025 data not yet available)
        """
        self.season = season
        self.physics_analyzer = PitchPhysicsAnalyzer()
        self.arsenal_analyzer = ArsenalSynergyAnalyzer()
        self.biomech_analyzer = BiomechanicsAnalyzer()
        self.diamond_detector = DiamondDetector()
        self.reporter = AdvancedReporter()

        self.all_results = []

    def load_free_agent_list(self, csv_path: str = None) -> pd.DataFrame:
        """
        Load free agent reliever list.

        Args:
            csv_path: Path to CSV with free agent data

        Returns:
            DataFrame with free agent information
        """
        if csv_path and os.path.exists(csv_path):
            print(f"Loading free agents from {csv_path}...")
            return pd.read_csv(csv_path)
        else:
            # Use sample list for testing
            print("Using sample free agent list...")
            return self._get_sample_free_agents()

    def _get_sample_free_agents(self) -> pd.DataFrame:
        """
        Get sample free agent list for testing.

        Returns:
            DataFrame with sample free agents
        """
        # Sample of notable 2024-2025 FA relievers
        sample_fas = [
            {'player_name': 'Hunter Harvey', 'player_id': 663961, 'Projected_AAV': 4.0, 'Age': 29},
            {'player_name': 'Tanner Scott', 'player_id': 605463, 'Projected_AAV': 12.0, 'Age': 30},
            {'player_name': 'Jeff Hoffman', 'player_id': 656546, 'Projected_AAV': 8.0, 'Age': 31},
            {'player_name': 'Carlos Estévez', 'player_id': 608032, 'Projected_AAV': 10.0, 'Age': 32},
            {'player_name': 'Clay Holmes', 'player_id': 605280, 'Projected_AAV': 9.0, 'Age': 31},
            {'player_name': 'Kenley Jansen', 'player_id': 445276, 'Projected_AAV': 10.0, 'Age': 37},
            {'player_name': 'Paul Sewald', 'player_id': 623149, 'Projected_AAV': 7.0, 'Age': 34},
            {'player_name': 'A.J. Minter', 'player_id': 621345, 'Projected_AAV': 6.0, 'Age': 31},
            {'player_name': 'Kirby Yates', 'player_id': 489446, 'Projected_AAV': 8.0, 'Age': 37},
            {'player_name': 'Yimi García', 'player_id': 554340, 'Projected_AAV': 5.0, 'Age': 34},
        ]

        return pd.DataFrame(sample_fas)

    def fetch_traditional_stats(self, player_id: int, season: int) -> Dict:
        """
        Fetch traditional stats for a pitcher.

        Args:
            player_id: MLB player ID
            season: Season to fetch

        Returns:
            Dictionary with traditional stats
        """
        try:
            # Fetch pitching stats
            stats = pyb.playerid_reverse_lookup([player_id], key_type='mlbam')

            if stats.empty:
                return {}

            # Get basic stats from FanGraphs or Baseball Reference
            # For now, use simplified stats from Statcast
            start_date = f"{season}-03-01"
            end_date = f"{season}-11-01"

            pitch_data = pyb.statcast_pitcher(start_date, end_date, player_id)

            if pitch_data.empty:
                return {}

            # Calculate basic stats
            total_pitches = len(pitch_data)
            whiffs = len(pitch_data[pitch_data['description'] == 'swinging_strike'])
            strikeouts = len(pitch_data[pitch_data['events'] == 'strikeout'])

            # Estimate appearances from game dates
            appearances = pitch_data['game_date'].nunique()

            # Estimate innings (rough)
            batters_faced = pitch_data['at_bat_number'].nunique()
            innings = batters_faced / 3  # Very rough estimate

            return {
                'Appearances': appearances,
                'Innings': innings,
                'K_pct': (strikeouts / batters_faced * 100) if batters_faced > 0 else 0,
                'Whiff_pct': (whiffs / total_pitches * 100) if total_pitches > 0 else 0,
                'Saves': 0,  # Not available in Statcast easily
                'Stuff_plus': 100,  # Placeholder - would need Stuff+ model
                'Location_plus': 100,  # Placeholder
                'gmLI': 1.0,  # Placeholder - would need leverage data
            }

        except Exception as e:
            print(f"Error fetching traditional stats: {e}")
            return {}

    def analyze_pitcher(self, player_id: int, player_name: str,
                       projected_aav: float, age: int) -> Dict:
        """
        Perform complete analysis for a single pitcher.

        Combines all analysis phases.

        Args:
            player_id: MLB player ID
            player_name: Player name
            projected_aav: Projected AAV in millions
            age: Player age

        Returns:
            Complete analysis dictionary
        """
        print(f"\n{'='*80}")
        print(f"Analyzing {player_name} (ID: {player_id})...")
        print(f"{'='*80}")

        start_date = f"{self.season}-03-01"
        end_date = f"{self.season}-11-01"

        # Fetch pitch-level data
        try:
            print("  Fetching Statcast data...")
            pitch_data = pyb.statcast_pitcher(start_date, end_date, player_id)

            if pitch_data.empty:
                print(f"  ⚠️  No Statcast data available for {player_name}")
                return None

            print(f"  ✓ Loaded {len(pitch_data)} pitches")

        except Exception as e:
            print(f"  ✗ Error fetching data: {e}")
            return None

        # Phase 1: Pitch Physics
        print("  Phase 1: Analyzing pitch physics (VAA, SSW, Tunneling)...")
        physics_results = self.physics_analyzer.analyze_pitcher(
            player_id, start_date, end_date
        )

        # Phase 2: Arsenal Synergy
        print("  Phase 2: Analyzing arsenal synergy...")
        arsenal_results = self.arsenal_analyzer.analyze_pitcher_arsenal(
            pitch_data, player_name
        )

        # Phase 3: Biomechanics
        print("  Phase 3: Analyzing biomechanics...")
        biomech_results = self.biomech_analyzer.analyze_pitcher_biomechanics(
            pitch_data, player_name
        )

        # Fetch traditional stats
        print("  Fetching traditional stats...")
        traditional_stats = self.fetch_traditional_stats(player_id, self.season)

        # Add metadata
        traditional_stats.update({
            'player_name': player_name,
            'player_id': player_id,
            'Projected_AAV': projected_aav,
            'Age': age,
            'season': self.season,
        })

        # Phase 4: Diamond Detector - Combine all data
        print("  Phase 4: Calculating Diamond Score...")
        complete_analysis = analyze_reliever_complete(
            physics_results,
            arsenal_results,
            biomech_results,
            traditional_stats
        )

        print(f"  ✓ Diamond Score: {complete_analysis.get('Diamond_Score', 0):.1f}/100")
        print(f"  ✓ Value Score: {complete_analysis.get('Value_Score', 0):.1f}/100")
        print(f"  ✓ Bust Risk: {complete_analysis.get('Bust_Risk_Score', 0):.1f}/100")

        return complete_analysis

    def analyze_all_free_agents(self, free_agents: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze all free agent relievers.

        Args:
            free_agents: DataFrame with free agent information

        Returns:
            DataFrame with complete analysis results
        """
        print(f"\n{'='*80}")
        print(f"ANALYZING {len(free_agents)} FREE AGENT RELIEVERS")
        print(f"{'='*80}\n")

        results = []

        for idx, fa in free_agents.iterrows():
            result = self.analyze_pitcher(
                fa['player_id'],
                fa['player_name'],
                fa.get('Projected_AAV', 5.0),
                fa.get('Age', 30)
            )

            if result:
                results.append(result)

            # Rate limiting - be nice to the API
            import time
            time.sleep(1)

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        # Rank free agents
        if not results_df.empty:
            results_df = rank_free_agents(results)

        return results_df

    def generate_reports(self, all_pitchers: pd.DataFrame, output_dir: str = "."):
        """
        Generate all reports and outputs.

        Args:
            all_pitchers: DataFrame with all analyzed pitchers
            output_dir: Directory for output files
        """
        print(f"\n{'='*80}")
        print("GENERATING REPORTS")
        print(f"{'='*80}\n")

        # Identify hidden gems
        hidden_gems = self.diamond_detector.identify_hidden_gems(all_pitchers)

        print(f"Hidden Gems Identified: {len(hidden_gems)}")

        # Categorize pitchers
        categories = self.diamond_detector.categorize_pitchers(all_pitchers)

        print("\nCategory Breakdown:")
        for category, df in categories.items():
            print(f"  {category.replace('_', ' ')}: {len(df)}")

        # Generate executive summary
        print("\nGenerating executive summary...")
        executive_summary = self.reporter.generate_executive_summary(
            all_pitchers, hidden_gems, categories
        )

        # Save executive summary
        summary_path = os.path.join(output_dir, "RELIEVER_MARKET_INTELLIGENCE_EXECUTIVE_SUMMARY.md")
        with open(summary_path, 'w') as f:
            f.write(executive_summary)
        print(f"  ✓ Saved to {summary_path}")

        # Generate individual pitcher profiles (top 10)
        print("\nGenerating pitcher profiles...")
        profiles_path = os.path.join(output_dir, "PITCHER_PROFILES_DEEP_DIVE.md")

        with open(profiles_path, 'w') as f:
            f.write("# INDIVIDUAL PITCHER PROFILES - DEEP DIVE\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write("---\n\n")

            # Top 10 by Diamond Score
            top_pitchers = all_pitchers.nlargest(10, 'Diamond_Score')

            for _, pitcher in top_pitchers.iterrows():
                profile = self.reporter.generate_pitcher_profile(pitcher.to_dict())
                f.write(profile)

        print(f"  ✓ Saved to {profiles_path}")

        # Export detailed rankings CSV
        print("\nExporting detailed rankings...")
        rankings_path = os.path.join(output_dir, "reliever_market_intelligence_rankings.csv")
        self.reporter.export_detailed_rankings(all_pitchers, rankings_path)

        # Export hidden gems CSV
        if not hidden_gems.empty:
            gems_path = os.path.join(output_dir, "hidden_gems_targets.csv")
            hidden_gems.to_csv(gems_path, index=False)
            print(f"  ✓ Hidden gems saved to {gems_path}")

        # Generate summary statistics
        summary_stats = self.diamond_detector.generate_summary_stats(all_pitchers)

        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        print(f"\nSummary Statistics:")
        for key, value in summary_stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")


def main():
    """Main entry point."""
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  ADVANCED RELIEVER MARKET INTELLIGENCE                        ║
    ║  Physics-Based Analysis & Diamond Detection                   ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    # Initialize analyzer
    # Use 2024 season since 2025 data not yet available
    analyzer = RelieverMarketIntelligence(season=2024)

    # Load free agent list
    free_agents = analyzer.load_free_agent_list()

    print(f"Loaded {len(free_agents)} free agents for analysis\n")

    # Analyze all free agents
    results = analyzer.analyze_all_free_agents(free_agents)

    if results.empty:
        print("No results to analyze. Exiting.")
        return

    # Generate reports
    analyzer.generate_reports(results)

    print("\n✓ Analysis pipeline complete!")
    print("\nOutput files:")
    print("  - RELIEVER_MARKET_INTELLIGENCE_EXECUTIVE_SUMMARY.md")
    print("  - PITCHER_PROFILES_DEEP_DIVE.md")
    print("  - reliever_market_intelligence_rankings.csv")
    print("  - hidden_gems_targets.csv")


if __name__ == "__main__":
    # Enable pybaseball cache
    pyb.cache.enable()

    main()
