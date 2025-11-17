"""
CSV Exporter
============
Exports results to timestamped CSV files
"""

import pandas as pd
import os
from datetime import datetime


class CSVExporter:
    """Export results with timestamps"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    
    def save_decisions(self, decisions_df, output_dir='output_archive/decisions'):
        """Save decisions to CSV"""
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, f'{self.timestamp}_decisions.csv')
        decisions_df.to_csv(filepath, index=False)
        
        print(f"✓ Saved decisions: {filepath}")
        return filepath
    
    def save_backtest(self, backtest_df, output_dir='output_archive/backtests'):
        """Save backtest results to CSV"""
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, f'{self.timestamp}_backtest.csv')
        backtest_df.to_csv(filepath, index=False)
        
        print(f"✓ Saved backtest: {filepath}")
        return filepath


def main():
    print("CSV Exporter - Ready")


if __name__ == "__main__":
    main()
