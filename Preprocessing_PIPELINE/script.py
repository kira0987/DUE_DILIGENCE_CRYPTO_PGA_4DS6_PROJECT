import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
import os
import gzip
from io import BytesIO
import time

# Define full date range
START_DATE = datetime(2014, 1, 1)
END_DATE = datetime(2025, 3, 26)
BASE_URL = "https://www.sec.gov/Archives/edgar/daily-index"
OUTPUT_FILE = "sec_edgar_daily_indexes_2014_2025.csv"
MISSED_DAYS_FILE = "missed_days_2014_2025.csv"

# Custom headers
headers = {
    "User-Agent": "Houssam CRYPTODUEDILIGENCE (houssameddine.benkheder@esprit.tn)",
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}

# Function to determine quarter
def get_quarter(month):
    if 1 <= month <= 3:
        return "QTR1"
    elif 4 <= month <= 6:
        return "QTR2"
    elif 7 <= month <= 9:
        return "QTR3"
    elif 10 <= month <= 12:
        return "QTR4"

# Function to check if a day is a weekday
def is_weekday(date):
    return date.weekday() < 5  # Monday-Friday

# Function to determine file extension based on date
def get_file_extension(date):
    if date < datetime(2014, 4, 1):
        return ".idx"
    else:
        return ".idx.gz"

# Generate a single day’s URL
def generate_url(date):
    if is_weekday(date):
        year = date.strftime("%Y")
        month = date.month
        quarter = get_quarter(month)
        date_str = date.strftime("%Y%m%d")
        extension = get_file_extension(date)
        url = f"{BASE_URL}/{year}/{quarter}/master.{date_str}{extension}"
        return date_str, url, extension
    return None

# Asynchronous fetch function with faster retries
async def fetch_url(session, date_str, url, extension, semaphore):
    async with semaphore:
        retries = 3
        for attempt in range(retries):
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        raw_data = await response.read()
                        if extension == ".idx.gz":
                            with gzip.GzipFile(fileobj=BytesIO(raw_data)) as gz:
                                text = gz.read().decode("utf-8")
                        else:
                            text = raw_data.decode("utf-8")
                        lines = text.splitlines()[10:]
                        data = []
                        for line in lines:
                            if line.strip():
                                cik, company, form, date_filed, filename = line.split("|")
                                data.append([cik, company, form, date_filed, filename])
                        print(f"Processed {date_str}")
                        return data, None
                    elif response.status == 404:
                        print(f"No data for {date_str} (Status: 404 - Likely a holiday)")
                        return [], [date_str, "404", "No data available"]
                    elif response.status == 429:
                        print(f"No data for {date_str} (Status: 429 - Too Many Requests)")
                        return [], [date_str, "429", "Too Many Requests"]
                    elif response.status == 403:
                        print(f"Access denied for {date_str} (Status: 403 - Attempt {attempt + 1}/{retries})")
                        if attempt < retries - 1:
                            await asyncio.sleep(0.1)  # Faster retry delay
                        else:
                            print(f"Skipping {date_str} after {retries} attempts")
                            return [], [date_str, "403", "Access denied after retries"]
                    else:
                        print(f"No data for {date_str} (Status: {response.status})")
                        return [], [date_str, str(response.status), "Unexpected status"]
            except Exception as e:
                print(f"Failed to fetch {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(0.1)  # Faster retry delay
                else:
                    print(f"Skipping {date_str} after {retries} attempts")
                    return [], [date_str, "Exception", str(e)]
        return [], [date_str, "Unknown", "Failed after retries"]

# Fetch until 429 or end, saving full batch on stoppage
async def fetch_until_429(start_date_str):
    all_data = []
    missed_days = set()
    current_date = datetime.strptime(start_date_str, "%Y%m%d")
    batch_start_date = current_date
    hit_429 = False
    
    semaphore = asyncio.Semaphore(5)  # 5 req/s to balance speed and limit
    async with aiohttp.ClientSession() as session:
        while current_date <= END_DATE and not hit_429:
            date_info = generate_url(current_date)
            if date_info:
                date_str, url, extension = date_info
                result, missed = await fetch_url(session, date_str, url, extension, semaphore)
                all_data.extend(result)
                if missed:
                    missed_days.add(tuple(missed))
                    if missed[1] == "429":  # Stop batch on 429
                        hit_429 = True
                        break
            current_date += timedelta(days=1)
    
    # Save all data collected so far as one batch
    if all_data:
        batch_file = f"batch_{batch_start_date.strftime('%Y%m%d')}_to_{current_date.strftime('%Y%m%d')}.csv"
        pd.DataFrame(all_data, columns=["CIK", "Company Name", "Form Type", "Date Filed", "File Name"]).to_csv(batch_file, index=False)
        print(f"Saved batch to {batch_file}")
    
    # Update missed days
    if missed_days:
        missed_df = pd.DataFrame(list(missed_days), columns=["Date", "Status", "Reason"])
        if os.path.exists(MISSED_DAYS_FILE):
            existing_missed = pd.read_csv(MISSED_DAYS_FILE)
            missed_df = pd.concat([existing_missed, missed_df]).drop_duplicates()
        missed_df.to_csv(MISSED_DAYS_FILE, index=False)
        print(f"Updated missed days to {MISSED_DAYS_FILE}")
    
    return current_date, hit_429

# Concatenate all batch files
def concatenate_batches():
    batch_files = [f for f in os.listdir() if f.startswith("batch_") and f.endswith(".csv")]
    if not batch_files:
        print("No batch files found to concatenate.")
        return
    
    all_dfs = []
    for batch_file in batch_files:
        df = pd.read_csv(batch_file)
        all_dfs.append(df)
    
    combined_df = pd.concat(all_dfs).drop_duplicates()
    combined_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Concatenated all batches into {OUTPUT_FILE}")

# Main execution loop
if __name__ == "__main__":
    # Get starting date from user
    last_date = input("Enter the last date you reached (YYYYMMDD, e.g., 20151030), or press Enter to start from 20140101: ")
    if not last_date:
        last_date = "20140101"
    
    current_date = datetime.strptime(last_date, "%Y%m%d")
    
    while current_date <= END_DATE:
        print(f"Starting from {current_date.strftime('%Y%m%d')}")
        next_date, hit_429 = asyncio.run(fetch_until_429(current_date.strftime("%Y%m%d")))
        
        if next_date > END_DATE:
            break
        
        if hit_429:
            print(f"Hit 429 - Too Many Requests. Waiting 10 minutes...")
            time.sleep(600)  # 10 minutes
        else:
            print("Batch completed without 429, moving to next day.")
        
        current_date = next_date
    
    # Final concatenation
    print("All data fetched. Concatenating files...")
    concatenate_batches()
    print("Process finished!")