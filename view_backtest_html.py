"""
BACKTEST HTML VIEWER
====================
Converts your 2025-2026 backtest CSV to a beautiful HTML table

Usage:
    python view_backtest_html.py
    
This will:
1. Find your latest backtest CSV
2. Convert it to HTML with color coding
3. Open in your browser
"""

import pandas as pd
import os
from datetime import datetime
import webbrowser


def find_latest_backtest():
    """Find the most recent backtest CSV file"""
    backtest_dir = 'output_archive/backtests'
    
    if not os.path.exists(backtest_dir):
        print("❌ No backtest results found")
        print(f"   Expected directory: {backtest_dir}")
        return None
    
    # Get all backtest CSV files
    files = [f for f in os.listdir(backtest_dir) if f.endswith('.csv')]
    
    if not files:
        print("❌ No backtest CSV files found")
        print(f"   Run: python run_backtest.py first")
        return None
    
    # Sort by modification time, get most recent
    files_with_time = [(f, os.path.getmtime(os.path.join(backtest_dir, f))) for f in files]
    latest_file = sorted(files_with_time, key=lambda x: x[1], reverse=True)[0][0]
    
    return os.path.join(backtest_dir, latest_file)


def create_html(df, output_path):
    """Create beautiful HTML table from dataframe"""
    
    # Calculate summary stats
    total_games = len(df)
    yes_bets = df[df['prediction'] == 'YES']
    total_yes = len(yes_bets)
    wins = len(yes_bets[yes_bets['result'] == 'WIN'])
    losses = len(yes_bets[yes_bets['result'] == 'LOSS'])
    win_rate = (wins / total_yes * 100) if total_yes > 0 else 0
    
    # Count skipped games that went over (missed opportunities)
    skipped = df[df['prediction'] == 'NO']
    missed_opportunities = len(skipped[skipped['went_over'] == True])
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NBA Backtest Results - 2025-2026 Season</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #1a1a1a;
            margin-bottom: 10px;
            border-bottom: 3px solid #007aff;
            padding-bottom: 10px;
        }}
        
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .stat-card.wins {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }}
        
        .stat-card.losses {{
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
        }}
        
        .stat-card.rate {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
        }}
        
        .filters {{
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        
        .filter-group {{
            display: inline-block;
            margin-right: 20px;
        }}
        
        .filter-group label {{
            margin-right: 10px;
            font-weight: 500;
        }}
        
        select, input {{
            padding: 5px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        thead {{
            background: #f8f9fa;
            position: sticky;
            top: 0;
        }}
        
        th {{
            padding: 12px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
        }}
        
        th:hover {{
            background: #e9ecef;
        }}
        
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #dee2e6;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .result-WIN {{
            background-color: #d4edda;
            color: #155724;
            font-weight: bold;
        }}
        
        .result-LOSS {{
            background-color: #f8d7da;
            color: #721c24;
            font-weight: bold;
        }}
        
        .result-SKIPPED {{
            background-color: #e2e3e5;
            color: #6c757d;
        }}
        
        .confidence {{
            font-weight: bold;
        }}
        
        .confidence-high {{
            color: #28a745;
        }}
        
        .confidence-medium {{
            color: #ffc107;
        }}
        
        .confidence-low {{
            color: #dc3545;
        }}
        
        .went-over-true {{
            color: #28a745;
            font-weight: bold;
        }}
        
        .went-over-false {{
            color: #dc3545;
        }}
        
        .total-info {{
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏀 NBA Betting System - Backtest Results</h1>
        <div class="subtitle">2025-2026 Season Analysis | Generated {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</div>
        
        <div class="summary">
            <div class="stat-card">
                <div class="stat-label">Total Games Analyzed</div>
                <div class="stat-value">{total_games}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">YES Bets Placed</div>
                <div class="stat-value">{total_yes}</div>
            </div>
            <div class="stat-card wins">
                <div class="stat-label">Wins</div>
                <div class="stat-value">{wins}</div>
            </div>
            <div class="stat-card losses">
                <div class="stat-label">Losses</div>
                <div class="stat-value">{losses}</div>
            </div>
            <div class="stat-card rate">
                <div class="stat-label">Win Rate</div>
                <div class="stat-value">{win_rate:.1f}%</div>
            </div>
        </div>
        
        <div class="filters">
            <div class="filter-group">
                <label>Result:</label>
                <select id="filterResult" onchange="filterTable()">
                    <option value="all">All</option>
                    <option value="WIN">Wins Only</option>
                    <option value="LOSS">Losses Only</option>
                    <option value="SKIPPED">Skipped Only</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Prediction:</label>
                <select id="filterPrediction" onchange="filterTable()">
                    <option value="all">All</option>
                    <option value="YES">YES Bets</option>
                    <option value="NO">NO Bets</option>
                </select>
            </div>
            <div class="filter-group">
                <label>Search:</label>
                <input type="text" id="searchBox" onkeyup="filterTable()" placeholder="Team name...">
            </div>
        </div>
        
        <table id="resultsTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Date ▼</th>
                    <th onclick="sortTable(1)">Game</th>
                    <th onclick="sortTable(2)">Min Total</th>
                    <th onclick="sortTable(3)">Actual</th>
                    <th onclick="sortTable(4)">Went Over?</th>
                    <th onclick="sortTable(5)">Prediction</th>
                    <th onclick="sortTable(6)">Confidence</th>
                    <th onclick="sortTable(7)">Result</th>
                    <th>Reasoning</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Add rows
    for _, row in df.iterrows():
        # Determine confidence class
        conf = row['confidence']
        if conf >= 80:
            conf_class = 'confidence-high'
        elif conf >= 70:
            conf_class = 'confidence-medium'
        else:
            conf_class = 'confidence-low'
        
        # Went over class
        went_over_class = 'went-over-true' if row['went_over'] else 'went-over-false'
        went_over_text = '✅ YES' if row['went_over'] else '❌ NO'
        
        # Result class
        result_class = f"result-{row['result']}"
        
        # Format prediction
        pred_emoji = '✅' if row['prediction'] == 'YES' else '⏭️'
        
        # Result emoji
        if row['result'] == 'WIN':
            result_emoji = '🎯'
        elif row['result'] == 'LOSS':
            result_emoji = '💔'
        else:
            result_emoji = '⏭️'
        
        html += f"""
                <tr>
                    <td>{row['date']}</td>
                    <td><strong>{row['game']}</strong></td>
                    <td>{row['minimum']}</td>
                    <td><strong>{row['actual_total']}</strong></td>
                    <td class="{went_over_class}">{went_over_text}</td>
                    <td>{pred_emoji} {row['prediction']}</td>
                    <td class="confidence {conf_class}">{conf}%</td>
                    <td class="{result_class}">{result_emoji} {row['result']}</td>
                    <td class="total-info">{row['reasoning']}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
    
    <script>
        function sortTable(columnIndex) {
            var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            table = document.getElementById("resultsTable");
            switching = true;
            dir = "asc";
            
            while (switching) {
                switching = false;
                rows = table.rows;
                
                for (i = 1; i < (rows.length - 1); i++) {
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("TD")[columnIndex];
                    y = rows[i + 1].getElementsByTagName("TD")[columnIndex];
                    
                    var xContent = x.textContent || x.innerText;
                    var yContent = y.textContent || y.innerText;
                    
                    if (dir == "asc") {
                        if (xContent.toLowerCase() > yContent.toLowerCase()) {
                            shouldSwitch = true;
                            break;
                        }
                    } else if (dir == "desc") {
                        if (xContent.toLowerCase() < yContent.toLowerCase()) {
                            shouldSwitch = true;
                            break;
                        }
                    }
                }
                
                if (shouldSwitch) {
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount++;
                } else {
                    if (switchcount == 0 && dir == "asc") {
                        dir = "desc";
                        switching = true;
                    }
                }
            }
        }
        
        function filterTable() {
            var resultFilter = document.getElementById("filterResult").value;
            var predictionFilter = document.getElementById("filterPrediction").value;
            var searchTerm = document.getElementById("searchBox").value.toLowerCase();
            
            var table = document.getElementById("resultsTable");
            var rows = table.getElementsByTagName("tr");
            
            for (var i = 1; i < rows.length; i++) {
                var row = rows[i];
                var cells = row.getElementsByTagName("td");
                
                if (cells.length > 0) {
                    var result = cells[7].textContent.trim();
                    var prediction = cells[5].textContent.trim();
                    var game = cells[1].textContent.toLowerCase();
                    
                    var showResult = (resultFilter === "all" || result.includes(resultFilter));
                    var showPrediction = (predictionFilter === "all" || prediction.includes(predictionFilter));
                    var showSearch = (searchTerm === "" || game.includes(searchTerm));
                    
                    if (showResult && showPrediction && showSearch) {
                        row.style.display = "";
                    } else {
                        row.style.display = "none";
                    }
                }
            }
        }
    </script>
</body>
</html>
"""
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML file created: {output_path}")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("📊 BACKTEST HTML VIEWER")
    print("=" * 70)
    print()
    
    # Find latest backtest
    csv_path = find_latest_backtest()
    
    if not csv_path:
        return False
    
    print(f"📁 Loading: {csv_path}")
    
    # Load data
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} games")
    
    # Create HTML
    output_path = 'backtest_results.html'
    create_html(df, output_path)
    
    # Open in browser
    print(f"\n🌐 Opening in browser...")
    full_path = os.path.abspath(output_path)
    webbrowser.open('file://' + full_path)
    
    print("\n" + "=" * 70)
    print("✅ DONE!")
    print("=" * 70)
    print(f"\nHTML file location: {full_path}")
    print("You can also open it manually from your project folder")
    print()
    
    return True


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
