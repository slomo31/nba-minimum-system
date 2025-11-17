"""
Flask Web App for NBA Minimum Total System Dashboard
"""
from flask import Flask, render_template_string, jsonify, request
import pandas as pd
import os
from datetime import datetime
import subprocess

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Serve the dashboard"""
    try:
        # Check if tracker exists
        if not os.path.exists('min_total_results_tracker.csv'):
            return """
            <html>
            <body style="font-family: Arial; padding: 40px; text-align: center;">
                <h1>Dashboard Not Ready</h1>
                <p>Run the update script first to generate data.</p>
                <a href="/update" style="padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">Update Now</a>
            </body>
            </html>
            """
        
        # Read the dashboard HTML
        if os.path.exists('min_total_dashboard.html'):
            with open('min_total_dashboard.html', 'r') as f:
                html_content = f.read()
            return html_content
        else:
            return """
            <html>
            <body style="font-family: Arial; padding: 40px; text-align: center;">
                <h1>Generating Dashboard...</h1>
                <p>Please wait while we create your dashboard.</p>
                <script>setTimeout(function(){ window.location.href = '/update'; }, 2000);</script>
            </body>
            </html>
            """
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/update')
def update_data():
    """Update the data and regenerate dashboard"""
    try:
        # Run the update scripts
        result = subprocess.run(['python', 'track_minimum_results.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            subprocess.run(['python', 'generate_dashboard.py'], 
                          capture_output=True, text=True, timeout=30)
            return """
            <html>
            <body style="font-family: Arial; padding: 40px; text-align: center;">
                <h1>✓ Update Complete!</h1>
                <p>Dashboard has been refreshed with latest data.</p>
                <a href="/" style="padding: 10px 20px; background: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">View Dashboard</a>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <body style="font-family: Arial; padding: 40px;">
                <h1>Update Error</h1>
                <pre>{result.stderr}</pre>
                <a href="/">Back to Dashboard</a>
            </body>
            </html>
            """
    except Exception as e:
        return f"Error updating: {str(e)}"

@app.route('/api/stats')
def get_stats():
    """API endpoint for current stats"""
    try:
        df = pd.read_csv('min_total_results_tracker.csv')
        
        yes_bets = df[df['decision'] == 'YES']
        wins = len(yes_bets[yes_bets['result'] == 'WIN'])
        losses = len(yes_bets[yes_bets['result'] == 'LOSS'])
        pending = len(yes_bets[yes_bets['result'] == 'PENDING'])
        
        maybe_bets = df[df['decision'] == 'MAYBE']
        maybe_wins = len(maybe_bets[maybe_bets['result'] == 'WIN'])
        maybe_losses = len(maybe_bets[maybe_bets['result'] == 'LOSS'])
        maybe_pending = len(maybe_bets[maybe_bets['result'] == 'PENDING'])
        
        return jsonify({
            'yes_record': f"{wins}-{losses}",
            'yes_pending': pending,
            'maybe_record': f"{maybe_wins}-{maybe_losses}",
            'maybe_pending': maybe_pending,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
