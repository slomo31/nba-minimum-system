"""
PARLAY OPTIMIZER - STANDALONE
==============================
Analyzes YES decisions and recommends best parlay combinations

IMPORTANT: This is INDEPENDENT of the main system
- Does NOT modify existing files
- Reads from master_workflow output
- Provides additional parlay analysis
- Use AFTER running master_workflow.py

Usage:
    python parlay_optimizer.py

This will:
1. Load today's YES decisions
2. Analyze correlations between games
3. Calculate parlay probabilities
4. Recommend best 2-leg, 3-leg, and 4-leg parlays
"""

import pandas as pd
import numpy as np
from datetime import datetime
from itertools import combinations
import os
import sys


class ParlayOptimizer:
    """Analyzes and recommends parlay combinations"""
    
    def __init__(self, min_confidence=80):
        """
        Args:
            min_confidence: Only consider YES bets with this confidence or higher
        """
        self.min_confidence = min_confidence
        self.decisions_df = None
        self.yes_bets = None
    
    def load_latest_decisions(self):
        """Load most recent decisions from output_archive"""
        decisions_dir = 'output_archive/decisions'
        
        if not os.path.exists(decisions_dir):
            print("❌ No decisions found. Run master_workflow.py first!")
            return False
        
        # Get all decision files
        files = [f for f in os.listdir(decisions_dir) if f.endswith('_decisions.csv')]
        
        if not files:
            print("❌ No decision files found. Run master_workflow.py first!")
            return False
        
        # Get most recent
        latest_file = max(files)
        filepath = os.path.join(decisions_dir, latest_file)
        
        print(f"\n📁 Loading: {latest_file}")
        self.decisions_df = pd.read_csv(filepath)
        
        # Filter to YES decisions only
        self.yes_bets = self.decisions_df[
            (self.decisions_df['decision'] == 'YES') &
            (self.decisions_df['confidence'] >= self.min_confidence)
        ].copy()
        
        print(f"✅ Found {len(self.yes_bets)} YES bets (≥{self.min_confidence}% confidence)")
        
        return len(self.yes_bets) > 0
    
    def calculate_correlation_score(self, game1, game2):
        """
        Calculate how correlated two games are
        
        Lower correlation = better for parlays (more independent)
        
        Factors:
        - Same team playing? (high correlation)
        - Similar game times? (lower correlation)
        - Similar offensive styles? (moderate correlation)
        
        Returns: 0-100 (0 = no correlation, 100 = highly correlated)
        """
        teams1 = {game1['away_team'], game1['home_team']}
        teams2 = {game2['away_team'], game2['home_team']}
        
        # Same team = high correlation (both games can't hit if team underperforms)
        if teams1 & teams2:  # Any overlap
            return 80  # High correlation
        
        # Check game times (if available)
        # Games at same time = lower correlation (independent events)
        # We'll consider this neutral for now
        
        # For now, if no team overlap = low correlation
        return 20  # Low correlation = good for parlay
    
    def calculate_parlay_probability(self, games):
        """
        Calculate combined probability for a parlay
        
        Formula: P(all win) = P(game1) × P(game2) × ... × P(gameN)
        
        But we adjust for correlation:
        - If games are correlated, reduce combined probability
        """
        # Base probabilities (confidence / 100)
        probs = [g['confidence'] / 100 for g in games]
        
        # Calculate base combined probability
        combined_prob = np.prod(probs)
        
        # Adjust for correlations
        if len(games) > 1:
            # Calculate average correlation
            correlations = []
            for i in range(len(games)):
                for j in range(i + 1, len(games)):
                    corr = self.calculate_correlation_score(games[i], games[j])
                    correlations.append(corr)
            
            avg_correlation = np.mean(correlations)
            
            # Reduce probability based on correlation
            # High correlation = lower true probability
            correlation_penalty = 1 - (avg_correlation / 200)  # Max 50% reduction
            combined_prob *= correlation_penalty
        
        return combined_prob * 100  # Return as percentage
    
    def calculate_parlay_odds(self, games):
        """
        Calculate parlay payout odds
        
        Formula: Multiply individual odds
        
        Note: These are American odds (negative numbers)
        """
        total_decimal_odds = 1.0
        
        for game in games:
            american_odds = game['minimum_odds']
            
            # Convert American to Decimal
            if american_odds < 0:
                decimal = 1 + (100 / abs(american_odds))
            else:
                decimal = 1 + (american_odds / 100)
            
            total_decimal_odds *= decimal
        
        # Convert back to American
        if total_decimal_odds >= 2:
            parlay_odds = int((total_decimal_odds - 1) * 100)
        else:
            parlay_odds = int(-100 / (total_decimal_odds - 1))
        
        return parlay_odds
    
    def find_best_parlays(self, num_legs):
        """
        Find best N-leg parlays
        
        Args:
            num_legs: Number of games in parlay (2, 3, or 4)
        
        Returns:
            List of best parlays with analysis
        """
        if len(self.yes_bets) < num_legs:
            return []
        
        parlays = []
        
        # Generate all combinations
        for combo in combinations(self.yes_bets.to_dict('records'), num_legs):
            games = list(combo)
            
            # Calculate metrics
            combined_prob = self.calculate_parlay_probability(games)
            parlay_odds = self.calculate_parlay_odds(games)
            
            # Calculate expected value
            # EV = (probability × payout) - (1 - probability) × stake
            if parlay_odds > 0:
                payout_multiplier = parlay_odds / 100 + 1
            else:
                payout_multiplier = 100 / abs(parlay_odds) + 1
            
            ev = (combined_prob / 100) * payout_multiplier - (1 - combined_prob / 100)
            
            parlays.append({
                'games': games,
                'num_legs': num_legs,
                'combined_probability': round(combined_prob, 1),
                'parlay_odds': parlay_odds,
                'expected_value': round(ev, 3),
                'payout_multiplier': round(payout_multiplier, 2)
            })
        
        # Sort by expected value (best first)
        parlays.sort(key=lambda x: x['expected_value'], reverse=True)
        
        return parlays
    
    def format_parlay_display(self, parlay):
        """Format parlay for display"""
        output = []
        output.append(f"\n{'='*70}")
        output.append(f"{parlay['num_legs']}-LEG PARLAY")
        output.append(f"{'='*70}")
        output.append(f"\nCombined Probability: {parlay['combined_probability']}%")
        output.append(f"Parlay Odds: {parlay['parlay_odds']:+d}")
        output.append(f"Payout: ${parlay['payout_multiplier']:.2f} per $1")
        output.append(f"Expected Value: {parlay['expected_value']:+.3f}")
        output.append(f"\nGAMES:")
        
        for i, game in enumerate(parlay['games'], 1):
            output.append(f"\n  {i}. {game['away_team']} @ {game['home_team']}")
            output.append(f"     Over {game['minimum_total']} at {game['minimum_odds']:+d}")
            output.append(f"     Confidence: {game['confidence']}%")
            output.append(f"     Reasoning: {game['reasoning']}")
        
        return '\n'.join(output)
    
    def recommend_best_parlays(self):
        """Generate best parlay recommendations"""
        print("\n" + "="*70)
        print("🎯 PARLAY OPTIMIZER - RECOMMENDATIONS")
        print("="*70)
        
        if len(self.yes_bets) < 2:
            print("\n⚠️  Need at least 2 YES bets to create parlays")
            return
        
        recommendations = {}
        
        # Find best 2-leg parlay
        if len(self.yes_bets) >= 2:
            two_leg = self.find_best_parlays(2)
            if two_leg:
                recommendations['2-leg'] = two_leg[0]
        
        # Find best 3-leg parlay
        if len(self.yes_bets) >= 3:
            three_leg = self.find_best_parlays(3)
            if three_leg:
                recommendations['3-leg'] = three_leg[0]
        
        # Find best 4-leg parlay
        if len(self.yes_bets) >= 4:
            four_leg = self.find_best_parlays(4)
            if four_leg:
                recommendations['4-leg'] = four_leg[0]
        
        # Display recommendations
        for parlay_type, parlay in recommendations.items():
            print(self.format_parlay_display(parlay))
        
        # Summary
        print("\n" + "="*70)
        print("📊 RECOMMENDATION SUMMARY")
        print("="*70)
        
        for parlay_type, parlay in recommendations.items():
            print(f"\n{parlay_type.upper()}:")
            print(f"  Expected Value: {parlay['expected_value']:+.3f}")
            print(f"  Win Probability: {parlay['combined_probability']}%")
            print(f"  Risk/Reward: ${parlay['payout_multiplier']:.2f} per $1")
        
        # Best recommendation
        best = max(recommendations.items(), key=lambda x: x[1]['expected_value'])
        print(f"\n🏆 BEST PARLAY: {best[0]} (EV: {best[1]['expected_value']:+.3f})")
        
        return recommendations
    
    def save_recommendations(self, recommendations):
        """Save parlay recommendations to file"""
        if not recommendations:
            return
        
        output_dir = 'output_archive/parlays'
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filepath = os.path.join(output_dir, f'{timestamp}_parlays.txt')
        
        with open(filepath, 'w') as f:
            f.write("PARLAY RECOMMENDATIONS\n")
            f.write("="*70 + "\n\n")
            
            for parlay_type, parlay in recommendations.items():
                f.write(self.format_parlay_display(parlay))
                f.write("\n\n")
        
        print(f"\n💾 Saved to: {filepath}")


def main():
    """Run parlay optimizer"""
    print("\n" + "="*70)
    print("🎰 NBA MINIMUM SYSTEM - PARLAY OPTIMIZER")
    print("="*70)
    print("\nThis tool analyzes your YES decisions and recommends")
    print("the best 2-leg, 3-leg, and 4-leg parlay combinations.")
    print("\nIMPORTANT: Run master_workflow.py first to generate picks!")
    
    # Initialize optimizer
    optimizer = ParlayOptimizer(min_confidence=80)
    
    # Load decisions
    if not optimizer.load_latest_decisions():
        return
    
    # Show individual bets
    print("\n" + "="*70)
    print("TODAY'S YES BETS (Individual)")
    print("="*70)
    
    for idx, bet in optimizer.yes_bets.iterrows():
        print(f"\n{bet['game']}")
        print(f"  Over {bet['minimum_total']} at {bet['minimum_odds']:+d}")
        print(f"  Confidence: {bet['confidence']}%")
    
    # Generate recommendations
    recommendations = optimizer.recommend_best_parlays()
    
    # Save recommendations
    if recommendations:
        optimizer.save_recommendations(recommendations)
    
    # Final guidance
    print("\n" + "="*70)
    print("💡 PARLAY BETTING TIPS")
    print("="*70)
    print("""
1. Parlays are RISKIER than individual bets
   - All legs must hit to win
   - One miss = entire bet loses

2. Use smaller stakes for parlays
   - Individual bets: 3% bankroll
   - 2-leg parlay: 2% bankroll
   - 3-leg parlay: 1% bankroll
   - 4-leg parlay: 0.5% bankroll

3. Focus on Expected Value (EV)
   - Positive EV = good long-term bet
   - Higher EV = better parlay choice

4. Consider the probability
   - 2-leg at 85% = solid parlay
   - 3-leg at 75% = borderline
   - 4-leg below 70% = avoid

5. Diversify your action
   - Don't put ALL bets in one parlay
   - Keep some individual bets too
   - Parlays are for extra value, not main strategy
""")
    
    print("\n✅ PARLAY ANALYSIS COMPLETE!")
    print("="*70)
    print()


if __name__ == "__main__":
    main()