import os
import pandas as pd
from typing import Dict, List
from pathlib import Path

class DataLoader:
    def __init__(self, base_path="data"):
        self.base_path = Path(base_path)
        
    def load_market_data(self) -> Dict[str, pd.DataFrame]:
        """Load all market data CSV files into a dictionary of DataFrames"""
        market_data = {}
        market_dir = self.base_path / "market_data"
        
        for file in market_dir.glob("*.csv"):
            try:
                # Read CSV with proper parsing
                df = pd.read_csv(
                    file,
                    parse_dates=['Date'],
                    dayfirst=True,
                    thousands=','
                )
                
                # Clean column names
                df.columns = df.columns.str.strip()
                
                # Extract asset name from filename
                asset_name = file.stem.split('_')[0]  # Extract asset name (e.g., BTC from BTC_USD...)
                market_data[asset_name] = df
                
            except Exception as e:
                print(f"Error loading {file}: {str(e)}")
                
        return market_data
    
    def get_document_paths(self) -> List[str]:
        """Get paths to all fund documents"""
        doc_dir = self.base_path / "fund_documents"
        return [str(f) for f in doc_dir.glob("*.pdf")]
    
    def save_processed_data(self, asset: str, data: pd.DataFrame):
        """Save processed data to the processed directory"""
        processed_dir = self.base_path / "processed"
        processed_dir.mkdir(exist_ok=True)
    
        save_path = processed_dir / f"{asset}_processed.parquet"
        data.to_parquet(save_path)
    
def load_processed_data(self, asset: str) -> pd.DataFrame:
    """Load processed data if available"""
    processed_path = self.base_path / "processed" / f"{asset}_processed.parquet"
    if processed_path.exists():
        return pd.read_parquet(processed_path)
    return None