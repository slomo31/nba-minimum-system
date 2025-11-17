"""
YES/NO Decider
==============
Converts prediction scores into clear YES or NO decisions

Threshold:
- 90-100 points → YES (bet it)
- 75-89 points  → MAYBE (review manually)
- Below 75      → NO (skip)
"""

import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.season_config import CONFIDENCE_THRESHOLD_YES, CONFIDENCE_THRESHOLD_MAYBE


class YesNoDecider:
    """Make final YES/NO decisions"""
    
    def __init__(self, yes_threshold=CONFIDENCE_THRESHOLD_YES, maybe_threshold=CONFIDENCE_THRESHOLD_MAYBE):
        self.yes_threshold = yes_threshold
        self.maybe_threshold = maybe_threshold
    
    def make_decision(self, prediction):
        """
        Convert prediction into YES/NO decision
        
        Args:
            prediction: Dict from predictor with score and reasoning
        
        Returns:
            Dict with decision, action, stake recommendation
        """
        score = prediction['total_score']
        confidence = prediction['confidence']
        
        # Decision logic
        if score >= self.yes_threshold:
            decision = "YES"
            action = "BET IT"
            stake = "3% bankroll"
            confidence_level = "HIGH"
        elif score >= self.maybe_threshold:
            decision = "MAYBE"
            action = "REVIEW MANUALLY"
            stake = "2% bankroll (if you bet)"
            confidence_level = "MEDIUM"
        else:
            decision = "NO"
            action = "SKIP"
            stake = "0%"
            confidence_level = "LOW"
        
        # Build summary reasoning (top 3 factors)
        top_reasons = prediction['reasoning'][:3] if len(prediction['reasoning']) >= 3 else prediction['reasoning']
        summary_reasoning = ' | '.join(top_reasons)
        
        return {
            'game_time': prediction['game_time'],
            'away_team': prediction['away_team'],
            'home_team': prediction['home_team'],
            'game': f"{prediction['away_team']} @ {prediction['home_team']}",
            'minimum_total': prediction['minimum_total'],
            'minimum_odds': prediction['minimum_odds'],
            'decision': decision,
            'confidence': confidence,
            'score': score,
            'confidence_level': confidence_level,
            'action': action,
            'stake': stake,
            'reasoning': summary_reasoning,
            'full_factors': prediction['factors']
        }
    
    def process_all_predictions(self, predictions_list):
        """
        Process all predictions and make decisions
        
        Returns:
            DataFrame with all decisions
        """
        decisions = []
        
        for prediction in predictions_list:
            decision = self.make_decision(prediction)
            decisions.append(decision)
        
        df = pd.DataFrame(decisions)
        
        # Sort by confidence (highest first)
        df = df.sort_values('confidence', ascending=False)
        
        return df
    
    def print_summary(self, decisions_df):
        """Print summary of decisions"""
        total = len(decisions_df)
        yes_count = len(decisions_df[decisions_df['decision'] == 'YES'])
        maybe_count = len(decisions_df[decisions_df['decision'] == 'MAYBE'])
        no_count = len(decisions_df[decisions_df['decision'] == 'NO'])
        
        print("\n" + "=" * 70)
        print("DECISION SUMMARY")
        print("=" * 70)
        print(f"\nTotal games analyzed: {total}")
        print(f"  ✅ YES decisions: {yes_count}")
        print(f"  ⚠️ MAYBE decisions: {maybe_count}")
        print(f"  ❌ NO decisions: {no_count}")
        print()
        
        # Show YES bets
        if yes_count > 0:
            print("✅ YES BETS (90%+ confidence):")
            print("-" * 70)
            for _, game in decisions_df[decisions_df['decision'] == 'YES'].iterrows():
                print(f"\n{game['game']}")
                print(f"  Minimum: Over {game['minimum_total']} at {game['minimum_odds']:+d}")
                print(f"  Confidence: {game['confidence']}%")
                print(f"  Reasoning: {game['reasoning']}")
                print(f"  Action: {game['action']} ({game['stake']})")
        
        # Show MAYBE
        if maybe_count > 0:
            print("\n\n⚠️ MAYBE BETS (75-89% confidence):")
            print("-" * 70)
            for _, game in decisions_df[decisions_df['decision'] == 'MAYBE'].iterrows():
                print(f"\n{game['game']}")
                print(f"  Minimum: Over {game['minimum_total']} at {game['minimum_odds']:+d}")
                print(f"  Confidence: {game['confidence']}%")
                print(f"  Note: Review manually, borderline confidence")
        
        # Show NO
        if no_count > 0:
            print("\n\n❌ NO BETS (below 75% confidence):")
            print("-" * 70)
            for _, game in decisions_df[decisions_df['decision'] == 'NO'].iterrows():
                print(f"\n{game['game']}")
                print(f"  Minimum: Over {game['minimum_total']}")
                print(f"  Confidence: {game['confidence']}%")
                print(f"  Reasoning: {game['reasoning']}")
        
        print("\n" + "=" * 70)


def main():
    """Test the decider"""
    print("YES/NO Decider - Ready")
    print("Converts predictions to clear YES or NO decisions")


if __name__ == "__main__":
    main()
