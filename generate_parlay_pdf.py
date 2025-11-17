"""
PARLAY REPORT PDF GENERATOR
============================
Generates a professional PDF report of your parlay backtest results

Usage:
    python generate_parlay_pdf.py
"""

import pandas as pd
import os
from datetime import datetime


def generate_html_report(backtest_results_df):
    """Generate HTML report that can be converted to PDF"""
    
    # Analyze parlay performance
    yes_bets = backtest_results_df[backtest_results_df['prediction'] == 'YES'].copy()
    yes_bets['date'] = pd.to_datetime(yes_bets['date'])
    yes_bets['date_only'] = yes_bets['date'].dt.date
    
    by_date = yes_bets.groupby('date_only')
    
    parlay_nights = []
    for date, games in by_date:
        total_games = len(games)
        wins = len(games[games['result'] == 'WIN'])
        losses = len(games[games['result'] == 'LOSS'])
        parlay_result = 'WIN' if losses == 0 else 'LOSS'
        
        games_list = []
        for _, game in games.iterrows():
            games_list.append({
                'name': game['game'],
                'minimum': game['minimum'],
                'actual': game['actual_total'],
                'confidence': game['confidence'],
                'result': game['result']
            })
        
        parlay_nights.append({
            'date': date,
            'games_bet': total_games,
            'wins': wins,
            'losses': losses,
            'parlay_result': parlay_result,
            'games': games_list
        })
    
    parlay_df = pd.DataFrame(parlay_nights)
    
    # Calculate stats
    total_nights = len(parlay_df)
    parlay_wins = len(parlay_df[parlay_df['parlay_result'] == 'WIN'])
    parlay_losses = total_nights - parlay_wins
    parlay_win_rate = (parlay_wins / total_nights * 100) if total_nights > 0 else 0
    
    # Breakdown by size
    size_stats = {}
    for num_games in sorted(parlay_df['games_bet'].unique()):
        subset = parlay_df[parlay_df['games_bet'] == num_games]
        subset_wins = len(subset[subset['parlay_result'] == 'WIN'])
        subset_total = len(subset)
        subset_win_rate = (subset_wins / subset_total * 100) if subset_total > 0 else 0
        size_stats[num_games] = {
            'nights': subset_total,
            'wins': subset_wins,
            'win_rate': subset_win_rate
        }
    
    # False negatives
    no_bets = backtest_results_df[backtest_results_df['prediction'] == 'NO']
    false_negatives = no_bets[no_bets['went_over'] == True]
    fn_rate = (len(false_negatives) / len(no_bets) * 100) if len(no_bets) > 0 else 0
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>NBA Parlay Backtest Report</title>
    <style>
        @page {{
            size: letter;
            margin: 0.75in;
        }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 8.5in;
            margin: 0 auto;
        }}
        h1 {{
            color: #1a1a1a;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
            margin-top: 30px;
        }}
        h3 {{
            color: #34495e;
            margin-top: 20px;
        }}
        .summary-box {{
            background: #f8f9fa;
            border-left: 4px solid #4CAF50;
            padding: 15px;
            margin: 20px 0;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        th {{
            background: #2c3e50;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .win {{
            color: #27ae60;
            font-weight: bold;
        }}
        .loss {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .game-card {{
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 12px;
            margin: 10px 0;
            page-break-inside: avoid;
        }}
        .game-header {{
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .game-detail {{
            font-size: 13px;
            color: #555;
            margin: 3px 0;
        }}
        .recommendation {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
        }}
        .page-break {{
            page-break-after: always;
        }}
        .footer {{
            text-align: center;
            color: #7f8c8d;
            font-size: 12px;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <h1>🏀 NBA Minimum Alternate Parlay System</h1>
    <h2>Backtest Performance Report</h2>
    
    <div class="summary-box">
        <strong>Report Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br>
        <strong>Analysis Period:</strong> 2025-2026 NBA Season<br>
        <strong>Total Games Analyzed:</strong> {len(backtest_results_df)}<br>
        <strong>Strategy:</strong> Parlay all YES predictions per night
    </div>
    
    <h2>Executive Summary</h2>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{total_nights}</div>
            <div class="stat-label">Betting Nights</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{parlay_wins}</div>
            <div class="stat-label">Perfect Nights</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{parlay_losses}</div>
            <div class="stat-label">Losing Nights</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{parlay_win_rate:.1f}%</div>
            <div class="stat-label">Win Rate</div>
        </div>
    </div>
    
    <h2>Performance by Parlay Size</h2>
    
    <table>
        <thead>
            <tr>
                <th>Parlay Size</th>
                <th>Nights</th>
                <th>Wins</th>
                <th>Losses</th>
                <th>Win Rate</th>
            </tr>
        </thead>
        <tbody>
"""
    
    for size in sorted(size_stats.keys()):
        stats = size_stats[size]
        html += f"""
            <tr>
                <td>{size}-Game Parlay</td>
                <td>{stats['nights']}</td>
                <td class="win">{stats['wins']}</td>
                <td class="loss">{stats['nights'] - stats['wins']}</td>
                <td><strong>{stats['win_rate']:.1f}%</strong></td>
            </tr>
"""
    
    html += """
        </tbody>
    </table>
    
    <h2>Profitability Analysis</h2>
    
    <table>
        <thead>
            <tr>
                <th>Parlay Type</th>
                <th>Typical Odds</th>
                <th>Your Win Rate</th>
                <th>Expected Value</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
"""
    
    # Calculate EV for each parlay size
    parlay_odds = {
        2: [('+260', 2.6), ('+280', 2.8)],
        3: [('+600', 6.0), ('+650', 6.5)]
    }
    
    for size, odds_list in parlay_odds.items():
        if size in size_stats:
            win_rate = size_stats[size]['win_rate'] / 100
            for odds_str, decimal in odds_list:
                win_amount = (decimal - 1) * 100
                ev = (win_rate * win_amount) - ((1 - win_rate) * 100)
                status = "✅ PROFITABLE" if ev > 0 else "❌ NOT PROFITABLE"
                
                html += f"""
            <tr>
                <td>{size}-Leg Parlay</td>
                <td>{odds_str}</td>
                <td><strong>{win_rate * 100:.1f}%</strong></td>
                <td>${ev:+.2f} per $100</td>
                <td>{status}</td>
            </tr>
"""
    
    html += """
        </tbody>
    </table>
    
    <div class="page-break"></div>
    
    <h2>Detailed Night-by-Night Results</h2>
"""
    
    # Show all parlay nights
    for _, night in parlay_df.iterrows():
        result_class = "win" if night['parlay_result'] == 'WIN' else "loss"
        result_icon = "✅" if night['parlay_result'] == 'WIN' else "❌"
        
        html += f"""
    <div class="game-card">
        <div class="game-header">
            {result_icon} {night['date'].strftime('%B %d, %Y')} - {night['games_bet']}-Game Parlay
        </div>
        <div class="game-detail">
            <strong>Result:</strong> <span class="{result_class}">{night['parlay_result']}</span> 
            ({night['wins']}W - {night['losses']}L)
        </div>
"""
        
        for game in night['games']:
            game_result = "✅" if game['result'] == 'WIN' else "❌"
            html += f"""
        <div class="game-detail">
            {game_result} {game['name']} - 
            Min: {game['minimum']} | Actual: {game['actual']} | 
            Conf: {game['confidence']}%
        </div>
"""
        
        html += """
    </div>
"""
    
    html += f"""
    
    <div class="page-break"></div>
    
    <h2>System Optimization Insights</h2>
    
    <h3>False Negatives (Missed Opportunities)</h3>
    <p>
        Your system said NO to {len(no_bets)} games, but <strong>{len(false_negatives)} of them went over</strong> ({fn_rate:.1f}%).
        This suggests your 80% confidence threshold may be too conservative.
    </p>
    
    <div class="recommendation">
        <h3>💡 Recommendations</h3>
        <ul>
            <li><strong>2-Leg Parlays:</strong> Your {size_stats.get(2, {}).get('win_rate', 0):.1f}% win rate is excellent. 
                Focus your strategy here.</li>
            <li><strong>3-Leg Parlays:</strong> Win rate of {size_stats.get(3, {}).get('win_rate', 0):.1f}% on limited sample. 
                Be selective - only bet when all games are 90%+ confidence.</li>
"""
    
    if 4 in size_stats:
        html += f"""
            <li><strong>4+ Leg Parlays:</strong> Win rate of {size_stats[4]['win_rate']:.1f}%. 
                High correlation risk - consider avoiding.</li>
"""
    
    html += f"""
            <li><strong>Threshold Optimization:</strong> With {fn_rate:.1f}% false negative rate, 
                consider testing 75% threshold to capture more opportunities.</li>
        </ul>
    </div>
    
    <h3>Key Takeaways</h3>
    <ul>
        <li>Overall parlay win rate: <strong>{parlay_win_rate:.1f}%</strong></li>
        <li>Perfect nights: <strong>{parlay_wins} of {total_nights}</strong></li>
        <li>Losing nights: <strong>{parlay_losses}</strong></li>
        <li>Best performing parlay size: <strong>{max(size_stats.keys(), key=lambda k: size_stats[k]['win_rate'])}-game parlays</strong> 
            at {size_stats[max(size_stats.keys(), key=lambda k: size_stats[k]['win_rate'])]['win_rate']:.1f}%</li>
    </ul>
    
    <div class="footer">
        <p>NBA Minimum Alternate Totals System | Backtest Report | {datetime.now().year}</p>
        <p>This report analyzes historical performance and does not guarantee future results.</p>
    </div>
    
</body>
</html>
"""
    
    return html


def main():
    """Generate PDF report"""
    print("\n" + "=" * 70)
    print("📄 PARLAY REPORT PDF GENERATOR")
    print("=" * 70)
    print()
    
    # Load backtest results
    backtest_files = []
    if os.path.exists('output_archive/backtests'):
        backtest_files = [f for f in os.listdir('output_archive/backtests') if f.endswith('.csv')]
    
    if not backtest_files:
        print("❌ No backtest results found!")
        print("   Run: python run_backtest.py first")
        return False
    
    # Use most recent
    latest_file = sorted(backtest_files)[-1]
    filepath = os.path.join('output_archive/backtests', latest_file)
    
    print(f"📂 Loading: {filepath}\n")
    
    results = pd.read_csv(filepath)
    
    print(f"✓ Loaded {len(results)} games")
    print(f"  YES predictions: {len(results[results['prediction'] == 'YES'])}")
    print(f"  NO predictions: {len(results[results['prediction'] == 'NO'])}")
    
    # Generate HTML report
    print("\n📝 Generating report...")
    html_content = generate_html_report(results)
    
    # Save HTML
    os.makedirs('output_archive/reports', exist_ok=True)
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    html_file = os.path.join('output_archive/reports', f'{timestamp}_parlay_report.html')
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ HTML report saved: {html_file}")
    
    # Instructions for PDF conversion
    print("\n" + "=" * 70)
    print("📄 TO CREATE PDF:")
    print("=" * 70)
    print(f"""
1. Open the HTML file in your browser:
   {html_file}

2. Print to PDF:
   - Press Cmd+P (Mac) or Ctrl+P (Windows)
   - Select "Save as PDF" as printer
   - Click "Save"
   - Choose location and filename

3. Or use online converter:
   - Upload HTML to: https://www.sejda.com/html-to-pdf
   - Download PDF

The HTML file is styled for professional PDF output!
""")
    
    print("=" * 70)
    print("✅ REPORT GENERATED!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
