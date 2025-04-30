# utils/cik_utils.py
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm

class CIKManager:
    def __init__(self, cache_path="output/cik_cache.json"):
        self.cache_path = Path(cache_path)
        self.cache = self._load_cache()
    
    def _load_cache(self):
        if self.cache_path.exists():
            with open(self.cache_path, 'r') as f:
                return json.load(f)
        return {}
    
    def save_cache(self):
        with open(self.cache_path, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def add_cik(self, cik, company_name, filings):
        self.cache[str(cik)] = {
            'name': company_name,
            'filings': filings,
            'last_accessed': str(pd.Timestamp.now()),
            'count': len(filings)
        }
    
    def get_top_ciks(self, n=100):
        return sorted(
            self.cache.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )[:n]
    
    def bulk_load_from_csv(self, csv_path, cik_col='CIK', name_col='Company Name'):
        df = pd.read_csv(csv_path)
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Loading CIKs"):
            cik = str(row[cik_col])
            if cik not in self.cache:
                self.add_cik(
                    cik=cik,
                    company_name=row[name_col],
                    filings=[]
                )
        self.save_cache()