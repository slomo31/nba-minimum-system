"""
Generate HTML Dashboard for Minimum Total System Results
"""

import pandas as pd
import json
from datetime import datetime


def load_tracker_results():
    """Load the results tracker CSV"""
    try:
        df = pd.read_csv('min_total_results_tracker.csv')
        return df
    except FileNotFoundError:
        print("Error: Run track_minimum_results.py first to generate results")
        return None


def generate_dashboard(df):
    """Generate HTML dashboard"""
    
    # Calculate stats
    yes_bets = df[df['decision'] == 'YES'].copy()
    maybe_bets = df[df['decision'] == 'MAYBE'].copy()
    no_bets = df[df['decision'] == 'NO'].copy()
    
    # YES bet stats
    wins = len(yes_bets[yes_bets['result'] == 'WIN'])
    losses = len(yes_bets[yes_bets['result'] == 'LOSS'])
    pending = len(yes_bets[yes_bets['result'] == 'PENDING'])
    completed_yes = yes_bets[yes_bets['result'].isin(['WIN', 'LOSS'])]
    
    win_rate = (wins / len(completed_yes) * 100) if len(completed_yes) > 0 else 0
    
    # MAYBE bet stats
    maybe_wins = len(maybe_bets[maybe_bets['result'] == 'WIN'])
    maybe_losses = len(maybe_bets[maybe_bets['result'] == 'LOSS'])
    maybe_pending = len(maybe_bets[maybe_bets['result'] == 'PENDING'])
    completed_maybe = maybe_bets[maybe_bets['result'].isin(['WIN', 'LOSS'])]
    
    maybe_win_rate = (maybe_wins / len(completed_maybe) * 100) if len(completed_maybe) > 0 else 0
    
    # NO bet stats
    completed_no = no_bets[no_bets['result'].isin(['WOULD_WIN', 'CORRECT_SKIP'])]
    missed = len(completed_no[completed_no['result'] == 'WOULD_WIN'])
    correct_skips = len(completed_no[completed_no['result'] == 'CORRECT_SKIP'])
    
    # ROI calculation
    avg_odds = -450
    profit_per_win = 3 * (100 / abs(avg_odds))  # 3% stake at -450 odds
    total_profit = wins * profit_per_win
    total_risked = (wins + losses) * 3
    roi = (total_profit / total_risked * 100) if total_risked > 0 else 0
    
    # Prepare data for charts
    completed_yes_sorted = completed_yes.sort_values('game_date')
    
    # Win/Loss by date
    wins_by_date = []
    for _, game in completed_yes_sorted.iterrows():
        wins_by_date.append({
            'date': str(game['game_date']),
            'result': game['result'],
            'game': game['game'],
            'confidence': game['confidence'],
            'actual': game.get('actual_total', 0),
            'line': game['minimum_total']
        })
    
    # Confidence distribution
    confidence_ranges = [
        ('80-85%', len(yes_bets[(yes_bets['confidence'] >= 80) & (yes_bets['confidence'] < 85)])),
        ('85-90%', len(yes_bets[(yes_bets['confidence'] >= 85) & (yes_bets['confidence'] < 90)])),
        ('90-95%', len(yes_bets[(yes_bets['confidence'] >= 90) & (yes_bets['confidence'] < 95)])),
        ('95-100%', len(yes_bets[yes_bets['confidence'] >= 95]))
    ]
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Minimum Total System - Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #333;
        }}
        
        .stat-value.green {{
            color: #10b981;
        }}
        
        .stat-value.red {{
            color: #ef4444;
        }}
        
        .stat-value.blue {{
            color: #3b82f6;
        }}
        
        .stat-value.orange {{
            color: #f59e0b;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .chart-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .chart-card h3 {{
            margin-bottom: 20px;
            color: #333;
        }}
        
        .table-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }}
        
        .table-card h3 {{
            margin-bottom: 20px;
            color: #333;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #374151;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
            color: #4b5563;
        }}
        
        tr:hover {{
            background: #f9fafb;
        }}
        
        .win {{
            color: #10b981;
            font-weight: bold;
        }}
        
        .loss {{
            color: #ef4444;
            font-weight: bold;
        }}
        
        .pending {{
            color: #f59e0b;
            font-weight: bold;
        }}
        
        .missed {{
            color: #f59e0b;
        }}
        
        @media (max-width: 768px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 1.8rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏀 NBA Minimum Total System</h1>
            <p>Performance Dashboard - 2025-2026 Season</p>
            <p style="font-size: 0.9rem; opacity: 0.8;">Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">YES Bets (80%+)</div>
                <div class="stat-value green">{wins}-{losses}</div>
                <div style="margin-top: 10px; color: #666;">{pending} pending | {win_rate:.1f}% win rate</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">MAYBE Bets (75-79%)</div>
                <div class="stat-value blue">{maybe_wins}-{maybe_losses}</div>
                <div style="margin-top: 10px; color: #666;">{maybe_pending} pending | {maybe_win_rate:.1f}% win rate</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Combined Record</div>
                <div class="stat-value green">{wins + maybe_wins}-{losses + maybe_losses}</div>
                <div style="margin-top: 10px; color: #666;">{((wins + maybe_wins) / (wins + losses + maybe_wins + maybe_losses) * 100) if (wins + losses + maybe_wins + maybe_losses) > 0 else 0:.1f}% overall</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">ROI</div>
                <div class="stat-value green">+{roi:.1f}%</div>
                <div style="margin-top: 10px; color: #666;">At -450 avg odds</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Missed Opportunities</div>
                <div class="stat-value orange">{missed}</div>
                <div style="margin-top: 10px; color: #666;">{correct_skips} correct skips</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>📊 Confidence Distribution</h3>
                <canvas id="confidenceChart"></canvas>
            </div>
            
            <div class="chart-card">
                <h3>📈 Results Overview</h3>
                <canvas id="resultsChart"></canvas>
            </div>
        </div>
        
        <div class="table-card">
            <h3>✅ YES BETS - Completed Games</h3>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Game</th>
                        <th>Line</th>
                        <th>Actual</th>
                        <th>Buffer</th>
                        <th>Conf</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # Add completed YES bets
    for _, game in completed_yes_sorted.iterrows():
        result_class = 'win' if game['result'] == 'WIN' else 'loss'
        buffer = game.get('actual_total', 0) - game['minimum_total']
        html += f"""
                    <tr>
                        <td>{game['game_date']}</td>
                        <td>{game['game']}</td>
                        <td>{game['minimum_total']:.1f}</td>
                        <td>{game.get('actual_total', 0):.1f}</td>
                        <td>+{buffer:.1f}</td>
                        <td>{game['confidence']}%</td>
                        <td class="{result_class}">{game['result']}</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
"""
    
    # Add MAYBE BETS table
    completed_maybe_sorted = completed_maybe.sort_values('game_date')
    if len(maybe_bets) > 0:
        html += """
        <div class="table-card">
            <h3>📊 MAYBE BETS (75-79% Confidence) - Completed Games</h3>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Game</th>
                        <th>Line</th>
                        <th>Actual</th>
                        <th>Buffer</th>
                        <th>Conf</th>
                        <th>Result</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # Add completed MAYBE bets
        if len(completed_maybe_sorted) > 0:
            for _, game in completed_maybe_sorted.iterrows():
                result_class = 'win' if game['result'] == 'WIN' else 'loss'
                buffer = game.get('actual_total', 0) - game['minimum_total']
                html += f"""
                    <tr>
                        <td>{game['game_date']}</td>
                        <td>{game['game']}</td>
                        <td>{game['minimum_total']:.1f}</td>
                        <td>{game.get('actual_total', 0):.1f}</td>
                        <td>+{buffer:.1f}</td>
                        <td>{game['confidence']}%</td>
                        <td class="{result_class}">{game['result']}</td>
                    </tr>
"""
        else:
            html += """
                    <tr>
                        <td colspan="7" style="text-align: center; color: #999;">No completed MAYBE bets yet</td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
"""
    
    # Add pending MAYBE games if any
    pending_maybe = maybe_bets[maybe_bets['result'] == 'PENDING'].sort_values('game_date')
    if len(pending_maybe) > 0:
        html += """
        <div class="table-card">
            <h3>⏳ PENDING MAYBE BETS</h3>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Game</th>
                        <th>Line</th>
                        <th>Conf</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
        for _, game in pending_maybe.iterrows():
            html += f"""
                    <tr>
                        <td>{game['game_date']}</td>
                        <td>{game['game']}</td>
                        <td>{game['minimum_total']:.1f}</td>
                        <td>{game['confidence']}%</td>
                        <td class="pending">PENDING</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""
    
    # Add pending games if any
    pending_yes = yes_bets[yes_bets['result'] == 'PENDING'].sort_values('game_date')
    if len(pending_yes) > 0:
        html += """
        <div class="table-card">
            <h3>⏳ PENDING GAMES</h3>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Game</th>
                        <th>Line</th>
                        <th>Conf</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
        for _, game in pending_yes.iterrows():
            html += f"""
                    <tr>
                        <td>{game['game_date']}</td>
                        <td>{game['game']}</td>
                        <td>{game['minimum_total']:.1f}</td>
                        <td>{game['confidence']}%</td>
                        <td class="pending">PENDING</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""
    
    # Add NO bets (missed opportunities)
    if len(completed_no) > 0:
        html += """
        <div class="table-card">
            <h3>⚠️ NO BETS - Missed Opportunities</h3>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Game</th>
                        <th>Line</th>
                        <th>Actual</th>
                        <th>Conf</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
        for _, game in completed_no.sort_values('game_date').iterrows():
            if game['result'] == 'WOULD_WIN':
                html += f"""
                    <tr>
                        <td>{game['game_date']}</td>
                        <td>{game['game']}</td>
                        <td>{game['minimum_total']:.1f}</td>
                        <td>{game.get('actual_total', 0):.1f}</td>
                        <td>{game['confidence']}%</td>
                        <td class="missed">MISSED WIN</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""
    
    # Add JavaScript for charts
    html += f"""
    </div>
    
    <script>
        // Confidence Distribution Chart
        const confidenceCtx = document.getElementById('confidenceChart').getContext('2d');
        new Chart(confidenceCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([r[0] for r in confidence_ranges])},
                datasets: [{{
                    label: 'Number of Bets',
                    data: {json.dumps([r[1] for r in confidence_ranges])},
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    borderColor: [
                        'rgb(59, 130, 246)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)',
                        'rgb(239, 68, 68)'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }}
            }}
        }});
        
        // Results Overview Pie Chart
        const resultsCtx = document.getElementById('resultsChart').getContext('2d');
        new Chart(resultsCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['YES Wins', 'YES Losses', 'MAYBE Wins', 'MAYBE Losses', 'Pending', 'Missed Opps', 'Correct Skips'],
                datasets: [{{
                    data: [{wins}, {losses}, {maybe_wins}, {maybe_losses}, {pending + maybe_pending}, {missed}, {correct_skips}],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(156, 163, 175, 0.8)',
                        'rgba(251, 191, 36, 0.8)',
                        'rgba(34, 197, 94, 0.8)'
                    ],
                    borderColor: [
                        'rgb(16, 185, 129)',
                        'rgb(239, 68, 68)',
                        'rgb(59, 130, 246)',
                        'rgb(245, 158, 11)',
                        'rgb(156, 163, 175)',
                        'rgb(251, 191, 36)',
                        'rgb(34, 197, 94)'
                    ],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html


def main():
    """Generate and save dashboard"""
    print("Generating dashboard...")
    
    df = load_tracker_results()
    if df is None:
        return
    
    html = generate_dashboard(df)
    
    # Save dashboard with timestamp to avoid browser caching
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'min_total_dashboard_{timestamp}.html'
    with open(output_file, 'w') as f:
        f.write(html)
    
    # Also save as main dashboard (overwrite old one)
    main_file = 'min_total_dashboard.html'
    with open(main_file, 'w') as f:
        f.write(html)
    
    print(f"\n✓ Dashboard generated:")
    print(f"  {output_file} (timestamped)")
    print(f"  {main_file} (main)")
    print(f"\n  Open the timestamped file to ensure fresh data:")
    print(f"  open {output_file}")
    print()


if __name__ == "__main__":
    main()