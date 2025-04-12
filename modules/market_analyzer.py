import pandas as pd
from typing import Dict
import numpy as np

class MarketAnalyzer:
    @staticmethod
    def calculate_metrics(df: pd.DataFrame) -> Dict:
        """Calculate key market metrics for a single asset"""
        if df.empty:
            return {}
            
        # Clean column names (remove whitespace and special characters)
        df.columns = df.columns.str.strip().str.lower()
        
        # Handle different possible column names
        price_col = 'price' if 'price' in df.columns else 'close'
        volume_col = 'vol.' if 'vol.' in df.columns else 'volume'
        
        metrics = {
            'current_price': df[price_col].iloc[-1],
            '30_day_volatility': df[price_col].pct_change().std() * np.sqrt(365),
            'max_drawdown': (df[price_col] / df[price_col].cummax() - 1).min(),
            'avg_daily_volume': df[volume_col].mean() if volume_col in df.columns else None,
            'last_30_day_return': (
                df[price_col].iloc[-1] / df[price_col].iloc[-30] - 1
            ) if len(df) >= 30 else None
        }
        return metrics
    
    def analyze_all_markets(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """Analyze all loaded market data"""
        results = {}
        for asset, df in market_data.items():
            try:
                # Convert date column to datetime and sort
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('date')
                results[asset] = self.calculate_metrics(df)
            except Exception as e:
                print(f"Error analyzing {asset}: {str(e)}")
                results[asset] = {}
        return results