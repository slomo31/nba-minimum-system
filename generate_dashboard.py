"""
NBA Minimum Totals Dashboard Generator - V3.1
==============================================
Creates a modern dashboard with Monte Carlo V3.1 and Legacy tabs
Shows flag counts and only recommends 0-flag games

V3.1 Backtest: 62-0 (100%) on 0-flag games
"""

import pandas as pd
import os
import glob
from datetime import datetime
import json


def load_mc_predictions():
    """Load the latest MC predictions"""
    mc_files = glob.glob('output_archive/decisions/*_mc_decisions.csv')
    if not mc_files:
        return None
    
    latest = max(mc_files, key=os.path.getctime)
    return pd.read_csv(latest)


def load_legacy_predictions():
    """Load legacy (original) predictions from tracker"""
    if os.path.exists('min_total_results_tracker.csv'):
        return pd.read_csv('min_total_results_tracker.csv')
    return None


def load_mc_results():
    """Load MC results tracker if exists"""
    if os.path.exists('mc_results_tracker.csv'):
        return pd.read_csv('mc_results_tracker.csv')
    return None


def generate_dashboard():
    """Generate the full dashboard HTML with V3.1 features"""
    
    # Load data
    mc_predictions = load_mc_predictions()
    legacy_data = load_legacy_predictions()
    mc_results = load_mc_results()
    
    # Calculate MC stats
    mc_record = "0-0"
    mc_win_rate = "0.0"
    mc_pending = 0
    mc_avg_hit_rate = "0.0"
    mc_picks = []
    zero_flag_count = 0
    
    if mc_predictions is not None:
        # Get 0-flag picks (the only bettable ones in V3.1)
        if 'flag_count' in mc_predictions.columns:
            zero_flag_picks = mc_predictions[mc_predictions['flag_count'] == 0]
            zero_flag_count = len(zero_flag_picks)
        else:
            zero_flag_picks = mc_predictions[mc_predictions['mc_decision'].isin(['STRONG_YES', 'YES'])]
        
        mc_pending = len(zero_flag_picks)
        mc_avg_hit_rate = f"{zero_flag_picks['mc_probability'].mean():.1f}" if len(zero_flag_picks) > 0 else "0.0"
        
        for _, row in mc_predictions.iterrows():
            flag_count = row.get('flag_count', 0) if 'flag_count' in row else 0
            mc_picks.append({
                'game': row.get('game', f"{row.get('away_team', '')} @ {row.get('home_team', '')}"),
                'line': row.get('minimum_line', row.get('minimum_total', 0)),
                'mc_prob': row.get('mc_probability', 0),
                'decision': row.get('mc_decision', 'NO'),
                'avg_sim': row.get('avg_simulated_total', 0),
                'total_expected': row.get('total_expected', 0),
                'flag_count': flag_count,
                'risk_flags': row.get('risk_flags', ''),
                'percentile_10': row.get('percentile_10', 0),
                'percentile_90': row.get('percentile_90', 0)
            })
    
    if mc_results is not None:
        wins = len(mc_results[mc_results['result'] == 'WIN'])
        losses = len(mc_results[mc_results['result'] == 'LOSS'])
        mc_record = f"{wins}-{losses}"
        mc_win_rate = f"{wins/(wins+losses)*100:.1f}" if (wins+losses) > 0 else "0.0"
    
    # Calculate Legacy stats
    legacy_record = "0-0"
    legacy_win_rate = "0.0"
    legacy_pending = 0
    legacy_picks = []
    
    if legacy_data is not None:
        completed = legacy_data[legacy_data['result'].isin(['WIN', 'LOSS'])]
        wins = len(completed[completed['result'] == 'WIN'])
        losses = len(completed[completed['result'] == 'LOSS'])
        legacy_record = f"{wins}-{losses}"
        legacy_win_rate = f"{wins/(wins+losses)*100:.1f}" if (wins+losses) > 0 else "0.0"
        legacy_pending = len(legacy_data[legacy_data['result'] == 'PENDING'])
        
        for _, row in legacy_data.tail(20).iterrows():
            legacy_picks.append({
                'game': row.get('game', ''),
                'line': row.get('minimum_total', 0),
                'confidence': row.get('confidence', 0),
                'decision': row.get('decision', ''),
                'result': row.get('result', 'PENDING')
            })
    
    # Sort MC picks by flags then probability
    mc_picks.sort(key=lambda x: (x['flag_count'], -x['mc_prob']))
    
    # Categorize MC picks by flags
    zero_flag_bets = [p for p in mc_picks if p['flag_count'] == 0 and p['mc_prob'] >= 88]
    flagged_games = [p for p in mc_picks if p['flag_count'] > 0]
    
    # Generate HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Minimum Totals V3.1</title>
    <meta http-equiv="refresh" content="300">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #ffffff;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        /* Header */
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }}
        
        .header h1 .emoji {{
            font-size: 2.5rem;
        }}
        
        .badge {{
            background: linear-gradient(135deg, #00d4aa 0%, #00b894 100%);
            color: #000;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-left: 15px;
        }}
        
        .subtitle {{
            color: #94a3b8;
            margin-top: 8px;
            font-size: 1rem;
        }}
        
        .last-updated {{
            color: #64748b;
            font-size: 0.85rem;
            margin-top: 5px;
        }}
        
        /* Tab Navigation */
        .tab-nav {{
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
            justify-content: center;
        }}
        
        .tab-btn {{
            background: rgba(255, 255, 255, 0.1);
            border: none;
            color: #fff;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .tab-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
        }}
        
        .tab-btn.active {{
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        }}
        
        .tab-btn .count {{
            background: rgba(255, 255, 255, 0.2);
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
        }}
        
        .tab-btn.active .count {{
            background: rgba(255, 255, 255, 0.3);
        }}
        
        /* Tab Content */
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
        }}
        
        .stat-label {{
            color: #94a3b8;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        
        .stat-value {{
            font-size: 2.2rem;
            font-weight: 700;
            color: #fff;
        }}
        
        .stat-value.green {{
            color: #22c55e;
        }}
        
        /* Refresh Button */
        .refresh-btn {{
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            border: none;
            color: #fff;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 0.95rem;
            font-weight: 500;
            margin-bottom: 25px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: transform 0.2s ease;
        }}
        
        .refresh-btn:hover {{
            transform: scale(1.02);
        }}
        
        /* Section Headers */
        .section-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 25px 0 15px;
            font-size: 1.1rem;
            font-weight: 600;
        }}
        
        .section-header .dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        .section-header .dot.green {{ background: #22c55e; }}
        .section-header .dot.yellow {{ background: #eab308; }}
        .section-header .dot.orange {{ background: #f97316; }}
        .section-header .dot.red {{ background: #ef4444; }}
        .section-header .dot.gray {{ background: #6b7280; }}
        
        .section-subtext {{
            color: #6b7280;
            font-size: 0.85rem;
            margin-left: 10px;
            font-weight: 400;
        }}
        
        /* Pick Cards */
        .pick-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid transparent;
            transition: all 0.2s ease;
        }}
        
        .pick-card:hover {{
            background: rgba(255, 255, 255, 0.08);
        }}
        
        .pick-card.strong-yes {{ border-left-color: #22c55e; }}
        .pick-card.yes {{ border-left-color: #84cc16; }}
        .pick-card.maybe {{ border-left-color: #f97316; }}
        .pick-card.skip {{ border-left-color: #6b7280; }}
        .pick-card.win {{ border-left-color: #22c55e; }}
        .pick-card.loss {{ border-left-color: #ef4444; }}
        .pick-card.pending {{ border-left-color: #eab308; }}
        
        .pick-info h3 {{
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        
        .pick-info .details {{
            color: #94a3b8;
            font-size: 0.85rem;
        }}
        
        .pick-prob {{
            text-align: right;
        }}
        
        .pick-prob .value {{
            font-size: 1.4rem;
            font-weight: 700;
        }}
        
        .pick-prob .value.green {{ color: #22c55e; }}
        .pick-prob .value.lime {{ color: #84cc16; }}
        .pick-prob .value.orange {{ color: #f97316; }}
        .pick-prob .value.gray {{ color: #6b7280; }}
        
        .pick-prob .label {{
            font-size: 0.7rem;
            padding: 3px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: 600;
        }}
        
        .pick-prob .label.yes {{ background: #22c55e; color: #000; }}
        .pick-prob .label.maybe {{ background: #f97316; color: #000; }}
        .pick-prob .label.skip {{ background: #6b7280; color: #fff; }}
        .pick-prob .label.win {{ background: #22c55e; color: #000; }}
        .pick-prob .label.loss {{ background: #ef4444; color: #fff; }}
        .pick-prob .label.pending {{ background: #eab308; color: #000; }}
        
        /* Parlay Section */
        .parlay-section {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.2) 100%);
            border-radius: 16px;
            padding: 20px;
            margin-top: 25px;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }}
        
        .parlay-section h3 {{
            font-size: 1.1rem;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .parlay-legs {{
            margin-bottom: 15px;
        }}
        
        .parlay-leg {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .parlay-leg:last-child {{
            border-bottom: none;
        }}
        
        .parlay-combined {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 12px 16px;
            border-radius: 8px;
            margin-top: 10px;
        }}
        
        .parlay-combined .label {{
            font-weight: 600;
        }}
        
        .parlay-combined .value {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #22c55e;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            color: #64748b;
            font-size: 0.8rem;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>
                <span class="emoji">🏀</span>
                NBA Minimum Totals
                <span class="badge">V3.1 • 100%</span>
            </h1>
            <p class="subtitle">Monte Carlo V3.1 • 62-0 backtest on 0-flag games</p>
            <p class="last-updated">Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
        
        <!-- Tab Navigation -->
        <div class="tab-nav">
            <button class="tab-btn active" onclick="showTab('mc')">
                🎲 V3.1 Picks
                <span class="count">{len(zero_flag_bets)}</span>
            </button>
            <button class="tab-btn" onclick="showTab('legacy')">
                📊 Legacy
                <span class="count">{legacy_pending}</span>
            </button>
        </div>
        
        <!-- Monte Carlo Tab -->
        <div id="mc-tab" class="tab-content active">
            <!-- Stats Grid -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Record</div>
                    <div class="stat-value">{mc_record}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Win Rate</div>
                    <div class="stat-value green">{mc_win_rate}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">0-Flag Picks</div>
                    <div class="stat-value">{len(zero_flag_bets)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg MC Prob</div>
                    <div class="stat-value green">{mc_avg_hit_rate}%</div>
                </div>
            </div>
            
            <div style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(22, 163, 74, 0.2) 100%); border-radius: 12px; padding: 12px 16px; margin-bottom: 20px; border: 1px solid rgba(34, 197, 94, 0.3);">
                <div style="font-size: 0.9rem; color: #22c55e; font-weight: 600;">✅ V3.1 STRICT MODE</div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px;">Backtest: 62-0 (100%) • Only betting 0-flag games</div>
            </div>
            
            <button class="refresh-btn" onclick="location.reload()">
                🔄 Refresh Data
            </button>
            
            <!-- ZERO FLAG BETS Section -->
            <div class="section-header">
                <span class="dot green"></span>
                ✅ BET THESE - Zero Flags ({len(zero_flag_bets)})
                <span class="section-subtext">100% backtest win rate</span>
            </div>
'''
    
    # Add zero-flag bettable picks
    for pick in zero_flag_bets:
        prob_class = 'green' if pick['mc_prob'] >= 95 else 'lime'
        card_class = 'strong-yes' if pick['mc_prob'] >= 95 else 'yes'
        
        # Format details with expected and range
        details = f"Line: {pick['line']} • Expected: {pick['total_expected']:.0f}"
        if pick['percentile_10'] and pick['percentile_90']:
            details += f" • Range: {pick['percentile_10']:.0f}-{pick['percentile_90']:.0f}"
        
        html += f'''
            <div class="pick-card {card_class}">
                <div class="pick-info">
                    <h3>{pick['game']}</h3>
                    <div class="details">{details}</div>
                </div>
                <div class="pick-prob">
                    <div class="value {prob_class}">{pick['mc_prob']}%</div>
                    <span class="label yes">0 FLAGS</span>
                </div>
            </div>
'''
    
    if not zero_flag_bets:
        html += '''
            <div class="pick-card">
                <div class="pick-info">
                    <h3>No safe picks today</h3>
                    <div class="details">All games have risk flags - consider sitting out</div>
                </div>
            </div>
'''
    
    # FLAGGED GAMES Section (Skip these)
    html += f'''
            <!-- FLAGGED Section -->
            <div class="section-header">
                <span class="dot orange"></span>
                ⚠️ SKIP - Has Flags ({len(flagged_games)})
                <span class="section-subtext">Risk factors detected</span>
            </div>
'''
    
    for pick in flagged_games[:10]:  # Show first 10 flagged games
        flag_text = pick['risk_flags'][:50] + '...' if len(str(pick['risk_flags'])) > 50 else pick['risk_flags']
        html += f'''
            <div class="pick-card skip">
                <div class="pick-info">
                    <h3>{pick['game']}</h3>
                    <div class="details">Line: {pick['line']} • {flag_text}</div>
                </div>
                <div class="pick-prob">
                    <div class="value gray">{pick['mc_prob']}%</div>
                    <span class="label skip">{pick['flag_count']} FLAGS</span>
                </div>
            </div>
'''
    
    if len(flagged_games) > 10:
        html += f'''
            <div class="pick-card">
                <div class="pick-info">
                    <h3>... and {len(flagged_games) - 10} more flagged games</h3>
                    <div class="details">All skipped due to risk factors</div>
                </div>
            </div>
'''
    
    # Parlay Section for V3.1 (only 0-flag picks)
    if len(zero_flag_bets) >= 2:
        top_picks = zero_flag_bets[:3]
        
        combined_prob = 1.0
        for p in top_picks[:2]:
            combined_prob *= (p['mc_prob'] / 100)
        combined_2leg = combined_prob * 100
        
        combined_prob_3 = 1.0
        for p in top_picks[:3]:
            combined_prob_3 *= (p['mc_prob'] / 100)
        combined_3leg = combined_prob_3 * 100
        
        html += f'''
            <!-- Parlay Recommendation -->
            <div class="parlay-section">
                <h3>🎯 Recommended Parlay (0-Flag Picks Only)</h3>
                <div class="parlay-legs">
'''
        for i, p in enumerate(top_picks[:2]):
            html += f'''
                    <div class="parlay-leg">
                        <span>{p['game']}</span>
                        <span>{p['mc_prob']}%</span>
                    </div>
'''
        html += f'''
                </div>
                <div class="parlay-combined">
                    <span class="label">Combined Probability (2-leg)</span>
                    <span class="value">{combined_2leg:.1f}%</span>
                </div>
            </div>
'''
    else:
        html += '''
            <div class="parlay-section" style="background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%); border-color: rgba(239, 68, 68, 0.3);">
                <h3>⚠️ No Parlays Today</h3>
                <div style="color: #94a3b8; font-size: 0.9rem;">Need at least 2 zero-flag picks for a parlay. Consider sitting today out.</div>
            </div>
'''
    
    # Close MC Tab, Start Legacy Tab
    html += f'''
        </div>
        
        <!-- Legacy Tab -->
        <div id="legacy-tab" class="tab-content">
            <!-- Stats Grid -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Record</div>
                    <div class="stat-value">{legacy_record}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Win Rate</div>
                    <div class="stat-value green">{legacy_win_rate}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Pending</div>
                    <div class="stat-value">{legacy_pending}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">System</div>
                    <div class="stat-value" style="font-size: 1rem;">Original</div>
                </div>
            </div>
            
            <button class="refresh-btn" onclick="location.reload()">
                🔄 Refresh Data
            </button>
            
            <div class="section-header">
                <span class="dot green"></span>
                Recent Picks
            </div>
'''
    
    # Add legacy picks
    for pick in reversed(legacy_picks[-10:]):
        result_class = pick['result'].lower()
        label_class = result_class
        
        html += f'''
            <div class="pick-card {result_class}">
                <div class="pick-info">
                    <h3>{pick['game']}</h3>
                    <div class="details">OVER {pick['line']} • {pick['decision']}</div>
                </div>
                <div class="pick-prob">
                    <div class="value">{pick['confidence']}%</div>
                    <span class="label {label_class}">{pick['result']}</span>
                </div>
            </div>
'''
    
    if not legacy_picks:
        html += '''
            <div class="pick-card">
                <div class="pick-info">
                    <h3>No legacy picks loaded</h3>
                    <div class="details">Run the tracker to see historical data</div>
                </div>
            </div>
'''
    
    # Close HTML
    html += '''
        </div>
        
        <!-- Footer -->
        <div class="footer">
            NBA Minimum Totals System • Monte Carlo Enhanced<br>
            Built for consistent, data-driven betting
        </div>
    </div>
    
    <script>
        function showTab(tab) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(el => {
                el.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(el => {
                el.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tab + '-tab').classList.add('active');
            event.target.closest('.tab-btn').classList.add('active');
            
            // Update URL
            const url = new URL(window.location);
            url.searchParams.set('system', tab);
            window.history.pushState({}, '', url);
        }
        
        // Check URL for tab parameter
        const urlParams = new URLSearchParams(window.location.search);
        const system = urlParams.get('system');
        if (system === 'legacy') {
            document.getElementById('mc-tab').classList.remove('active');
            document.getElementById('legacy-tab').classList.add('active');
            document.querySelectorAll('.tab-btn')[0].classList.remove('active');
            document.querySelectorAll('.tab-btn')[1].classList.add('active');
        }
    </script>
</body>
</html>
'''
    
    # Save dashboard
    with open('index.html', 'w') as f:
        f.write(html)
    
    print(f"✓ Dashboard generated: index.html")
    print(f"  MC picks: {len([p for p in mc_picks if p['decision'] in ['STRONG_YES', 'YES']])}")
    print(f"  Legacy pending: {legacy_pending}")
    
    return html


if __name__ == "__main__":
    generate_dashboard()