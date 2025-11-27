"""
Generate Dashboard - Monte Carlo Enhanced
==========================================
Creates an HTML dashboard showing:
- YES/MAYBE bet records
- Monte Carlo probabilities
- Tonight's picks with MC analysis
- Parlay recommendations
"""

import pandas as pd
import os
from datetime import datetime
import glob


def generate_dashboard():
    """Generate HTML dashboard with MC metrics"""
    
    # Load tracker data
    if not os.path.exists('min_total_results_tracker.csv'):
        print("No tracker file found. Run track_minimum_results.py first.")
        return
    
    df = pd.read_csv('min_total_results_tracker.csv')
    
    # Calculate stats
    yes_bets = df[df['decision'] == 'YES']
    maybe_bets = df[df['decision'] == 'MAYBE']
    
    yes_wins = len(yes_bets[yes_bets['result'] == 'WIN'])
    yes_losses = len(yes_bets[yes_bets['result'] == 'LOSS'])
    yes_pending = len(yes_bets[yes_bets['result'] == 'PENDING'])
    yes_total = yes_wins + yes_losses
    yes_rate = (yes_wins / yes_total * 100) if yes_total > 0 else 0
    
    maybe_wins = len(maybe_bets[maybe_bets['result'] == 'WIN'])
    maybe_losses = len(maybe_bets[maybe_bets['result'] == 'LOSS'])
    maybe_pending = len(maybe_bets[maybe_bets['result'] == 'PENDING'])
    maybe_total = maybe_wins + maybe_losses
    maybe_rate = (maybe_wins / maybe_total * 100) if maybe_total > 0 else 0
    
    total_wins = yes_wins + maybe_wins
    total_losses = yes_losses + maybe_losses
    total_games = total_wins + total_losses
    overall_rate = (total_wins / total_games * 100) if total_games > 0 else 0
    
    # Load tonight's MC predictions if available
    mc_files = glob.glob('output_archive/decisions/*_mc_decisions.csv')
    tonight_picks = None
    if mc_files:
        latest_mc = max(mc_files, key=os.path.getctime)
        tonight_picks = pd.read_csv(latest_mc)
    
    # Generate HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>NBA Minimum System - MC Enhanced</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="300">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ 
            text-align: center; 
            margin-bottom: 30px;
            font-size: 2em;
            background: linear-gradient(90deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
        }}
        .stat-card.yes {{ border-left: 4px solid #22c55e; }}
        .stat-card.maybe {{ border-left: 4px solid #f59e0b; }}
        .stat-card.total {{ border-left: 4px solid #3b82f6; }}
        .stat-card.mc {{ border-left: 4px solid #8b5cf6; }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{ color: #94a3b8; font-size: 0.9em; }}
        .win-rate {{ color: #22c55e; }}
        
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .section h2 {{
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{ color: #94a3b8; font-weight: 500; }}
        
        .win {{ color: #22c55e; }}
        .loss {{ color: #ef4444; }}
        .pending {{ color: #f59e0b; }}
        
        .mc-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .mc-strong {{ background: #22c55e; color: #000; }}
        .mc-yes {{ background: #84cc16; color: #000; }}
        .mc-maybe {{ background: #f59e0b; color: #000; }}
        .mc-no {{ background: #ef4444; color: #fff; }}
        
        .parlay-card {{
            background: linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        .parlay-prob {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        .timestamp {{
            text-align: center;
            color: #64748b;
            margin-top: 20px;
            font-size: 0.85em;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .stat-value {{ font-size: 1.8em; }}
            table {{ font-size: 0.85em; }}
            th, td {{ padding: 8px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏀 NBA Minimum System - MC Enhanced</h1>
        
        <div class="stats-grid">
            <div class="stat-card yes">
                <div class="stat-label">YES BETS (85%+ MC)</div>
                <div class="stat-value">{yes_wins}-{yes_losses}</div>
                <div class="stat-label win-rate">{yes_rate:.1f}% Win Rate</div>
                {f'<div class="stat-label pending">{yes_pending} pending</div>' if yes_pending > 0 else ''}
            </div>
            
            <div class="stat-card maybe">
                <div class="stat-label">MAYBE BETS (78-85% MC)</div>
                <div class="stat-value">{maybe_wins}-{maybe_losses}</div>
                <div class="stat-label win-rate">{maybe_rate:.1f}% Win Rate</div>
                {f'<div class="stat-label pending">{maybe_pending} pending</div>' if maybe_pending > 0 else ''}
            </div>
            
            <div class="stat-card total">
                <div class="stat-label">OVERALL</div>
                <div class="stat-value">{total_wins}-{total_losses}</div>
                <div class="stat-label win-rate">{overall_rate:.1f}% Win Rate</div>
            </div>
            
            <div class="stat-card mc">
                <div class="stat-label">ROI (Est.)</div>
                <div class="stat-value">+{(yes_wins * 0.22 - yes_losses) / max(yes_total, 1) * 100:.0f}%</div>
                <div class="stat-label">At -450 avg odds</div>
            </div>
        </div>
'''
    
    # Tonight's MC Picks Section
    if tonight_picks is not None and len(tonight_picks) > 0:
        # Filter to bettable games
        strong_yes = tonight_picks[tonight_picks['mc_decision'] == 'STRONG_YES']
        yes_games = tonight_picks[tonight_picks['mc_decision'] == 'YES']
        maybe_games = tonight_picks[tonight_picks['mc_decision'] == 'MAYBE']
        
        html += '''
        <div class="section">
            <h2>🎯 Tonight's MC Picks</h2>
'''
        
        if len(strong_yes) > 0:
            html += '<h3 style="color: #22c55e; margin: 15px 0 10px;">🟢 STRONG YES (92%+)</h3>'
            html += '<table><tr><th>Game</th><th>Line</th><th>MC Prob</th><th>Orig</th></tr>'
            for _, row in strong_yes.iterrows():
                html += f'''<tr>
                    <td>{row['game']}</td>
                    <td>{row['minimum_total']}</td>
                    <td><span class="mc-badge mc-strong">{row['mc_probability']}%</span></td>
                    <td>{row['original_confidence']}%</td>
                </tr>'''
            html += '</table>'
        
        if len(yes_games) > 0:
            html += '<h3 style="color: #84cc16; margin: 15px 0 10px;">🟡 YES (85-92%)</h3>'
            html += '<table><tr><th>Game</th><th>Line</th><th>MC Prob</th><th>Orig</th></tr>'
            for _, row in yes_games.iterrows():
                html += f'''<tr>
                    <td>{row['game']}</td>
                    <td>{row['minimum_total']}</td>
                    <td><span class="mc-badge mc-yes">{row['mc_probability']}%</span></td>
                    <td>{row['original_confidence']}%</td>
                </tr>'''
            html += '</table>'
        
        if len(maybe_games) > 0:
            html += '<h3 style="color: #f59e0b; margin: 15px 0 10px;">⚠️ MAYBE (78-85%)</h3>'
            html += '<table><tr><th>Game</th><th>Line</th><th>MC Prob</th><th>Risk</th></tr>'
            for _, row in maybe_games.iterrows():
                risk = row.get('risk_factors', '')
                if isinstance(risk, list):
                    risk = ', '.join(risk[:1]) if risk else ''
                html += f'''<tr>
                    <td>{row['game']}</td>
                    <td>{row['minimum_total']}</td>
                    <td><span class="mc-badge mc-maybe">{row['mc_probability']}%</span></td>
                    <td style="font-size: 0.85em; color: #f59e0b;">{risk[:50]}...</td>
                </tr>'''
            html += '</table>'
        
        # Parlay recommendation
        bettable = list(strong_yes['mc_probability']) + list(yes_games['mc_probability'])
        if len(bettable) >= 2:
            bettable.sort(reverse=True)
            two_leg = bettable[:2]
            combined = (two_leg[0]/100) * (two_leg[1]/100) * 100
            
            html += f'''
            <div class="parlay-card">
                <h3>✅ Recommended Parlay (2-leg)</h3>
                <div class="parlay-prob">{combined:.1f}% Combined</div>
                <p style="margin-top: 10px; opacity: 0.9;">Top 2 picks: {two_leg[0]}% × {two_leg[1]}%</p>
            </div>
'''
        
        html += '</div>'
    
    # Completed Games Table
    completed_yes = yes_bets[yes_bets['result'].isin(['WIN', 'LOSS'])].sort_values('game_date', ascending=False).head(15)
    
    if len(completed_yes) > 0:
        html += '''
        <div class="section">
            <h2>✅ Recent YES Bets</h2>
            <table>
                <tr><th>Date</th><th>Game</th><th>Line</th><th>Actual</th><th>Result</th></tr>
'''
        for _, row in completed_yes.iterrows():
            result_class = 'win' if row['result'] == 'WIN' else 'loss'
            actual = row.get('actual_total', '-')
            html += f'''<tr>
                <td>{row['game_date']}</td>
                <td>{row['game']}</td>
                <td>{row['minimum_total']}</td>
                <td>{actual}</td>
                <td class="{result_class}">{row['result']}</td>
            </tr>'''
        html += '</table></div>'
    
    # Footer
    html += f'''
        <div class="timestamp">
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            <br>Monte Carlo Enhanced Dashboard
        </div>
    </div>
</body>
</html>'''
    
    # Save dashboard
    with open('min_total_dashboard.html', 'w') as f:
        f.write(html)
    
    # Also save timestamped version
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    with open(f'min_total_dashboard_{timestamp}.html', 'w') as f:
        f.write(html)
    
    print(f"✓ Dashboard generated: min_total_dashboard.html")
    print(f"✓ Timestamped version: min_total_dashboard_{timestamp}.html")
    
    return html


if __name__ == "__main__":
    generate_dashboard()
