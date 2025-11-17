"""
Comprehensive debug - see exactly what should show on dashboard
"""
import pandas as pd

df = pd.read_csv('min_total_results_tracker.csv')

print("=" * 80)
print("COMPLETE DATA BREAKDOWN")
print("=" * 80)
print()

# Overall stats
print(f"Total predictions: {len(df)}")
print()

# By decision
print("BY DECISION:")
print("-" * 80)
for decision in ['YES', 'MAYBE', 'NO']:
    count = len(df[df['decision'] == decision])
    print(f"  {decision}: {count}")
print()

# YES bets breakdown
yes_bets = df[df['decision'] == 'YES']
print("YES BETS BREAKDOWN:")
print("-" * 80)
print(f"  Total: {len(yes_bets)}")
print(f"  WIN: {len(yes_bets[yes_bets['result'] == 'WIN'])}")
print(f"  LOSS: {len(yes_bets[yes_bets['result'] == 'LOSS'])}")
print(f"  PENDING: {len(yes_bets[yes_bets['result'] == 'PENDING'])}")
print()

# Show what SHOULD display
wins = len(yes_bets[yes_bets['result'] == 'WIN'])
losses = len(yes_bets[yes_bets['result'] == 'LOSS'])
pending = len(yes_bets[yes_bets['result'] == 'PENDING'])
win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

print("WHAT DASHBOARD SHOULD SHOW:")
print("-" * 80)
print(f"  Record: {wins}-{losses}")
print(f"  Win Rate: {win_rate:.1f}%")
print(f"  Pending: {pending}")
print()

# Confidence distribution for YES bets
print("CONFIDENCE DISTRIBUTION (YES BETS):")
print("-" * 80)
print(f"  80-85%: {len(yes_bets[(yes_bets['confidence'] >= 80) & (yes_bets['confidence'] < 85)])}")
print(f"  85-90%: {len(yes_bets[(yes_bets['confidence'] >= 85) & (yes_bets['confidence'] < 90)])}")
print(f"  90-95%: {len(yes_bets[(yes_bets['confidence'] >= 90) & (yes_bets['confidence'] < 95)])}")
print(f"  95-100%: {len(yes_bets[yes_bets['confidence'] >= 95])}")
print()

# NO bets
no_bets = df[df['decision'] == 'NO']
missed = len(no_bets[no_bets['result'] == 'WOULD_WIN'])
correct = len(no_bets[no_bets['result'] == 'CORRECT_SKIP'])

print("NO BETS:")
print("-" * 80)
print(f"  Missed opportunities: {missed}")
print(f"  Correct skips: {correct}")
print()

# Check if any games have weird data
print("CHECKING FOR DATA ISSUES:")
print("-" * 80)
weird_results = df[~df['result'].isin(['WIN', 'LOSS', 'PENDING', 'WOULD_WIN', 'CORRECT_SKIP'])]
if len(weird_results) > 0:
    print(f"  ⚠️  Found {len(weird_results)} games with unexpected result values:")
    print(weird_results[['game', 'decision', 'result']])
else:
    print("  ✓ All results are valid")