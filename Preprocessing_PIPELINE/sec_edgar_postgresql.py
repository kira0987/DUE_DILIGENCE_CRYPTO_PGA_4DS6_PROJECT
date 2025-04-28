import pandas as pd
from sqlalchemy import create_engine, text

# Update with your database info
DB_USER = 'postgres'
DB_PASS = 'Houssamluffyking5'
DB_NAME = 'edgar_cik_data'
DB_HOST = 'localhost'
DB_PORT = '5432'

# Create SQLAlchemy engine
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# File path to your large CSV
csv_file = 'sec_edgar_daily_indexes_2014_2025.csv'

# Chunk size: number of rows to read at a time
chunksize = 100000

# Create the table if it doesn't exist (wrapped with `text()` for SQLAlchemy 2.x)
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS sec_filings (
            cik TEXT,
            company_name TEXT,
            form_type TEXT,
            date_filed TEXT,
            file_name TEXT
        );
    """))

# Load and insert in chunks
for i, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunksize)):
    # Normalize column names to match DB schema
    chunk.columns = [c.lower().replace(" ", "_") for c in chunk.columns]
    
    # Insert chunk into database
    chunk.to_sql('sec_filings', engine, if_exists='append', index=False)
    print(f'✅ Inserted chunk {i + 1} ({len(chunk)} rows)')
