import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
import os
import gzip
from io import BytesIO

# Define date range
start_date = datetime(2019,2,12)
end_date = datetime(2025, 3, 26)
base_url = "https://www.sec.gov/Archives/edgar/daily-index"
output_file = "sec_edgar_daily_indexes_2019_2025.csv"
missed_days_file = "missed_days_2019.csv"

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
    # Use .idx before April 1, 2014, .idx.gz for QTR2 2014 (April 1 - June 30), .idx after June 30, 2014
    if date < datetime(2014, 4, 1):
        return ".idx"
    elif datetime(2014, 4, 1) <= date <= datetime(2014, 6, 30):
        return ".idx.gz"
    else:
        return ".idx"

# Generate list of dates and URLs
dates_to_fetch = []
current_date = start_date
while current_date <= end_date:
    if is_weekday(current_date):
        year = current_date.strftime("%Y")
        month = current_date.month
        quarter = get_quarter(month)
        date_str = current_date.strftime("%Y%m%d")
        extension = get_file_extension(current_date)
        url = f"{base_url}/{year}/{quarter}/master.{date_str}{extension}"
        dates_to_fetch.append((date_str, url, extension))
    current_date += timedelta(days=1)

# Load existing data
all_data = []
if os.path.exists(output_file):
    all_data = pd.read_csv(output_file).values.tolist()

# Load or initialize missed days list
missed_days = []
if os.path.exists(missed_days_file):
    missed_days = pd.read_csv(missed_days_file).values.tolist()

# Asynchronous fetch function
async def fetch_url(session, date_str, url, extension, semaphore):
    async with semaphore:  # Limit concurrency to 10
        retries = 3
        for attempt in range(retries):
            try:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        # Get raw bytes
                        raw_data = await response.read()
                        if extension == ".idx.gz":
                            # Decompress gzip content
                            with gzip.GzipFile(fileobj=BytesIO(raw_data)) as gz:
                                text = gz.read().decode("utf-8")
                        else:
                            # Uncompressed .idx file
                            text = raw_data.decode("utf-8")
                        
                        lines = text.splitlines()[10:]  # Skip header
                        data = []
                        for line in lines:
                            if line.strip():
                                cik, company, form, date_filed, filename = line.split("|")
                                data.append([cik, company, form, date_filed, filename])
                        print(f"Processed {date_str}")
                        return data, None  # Success, no missed day
                    elif response.status == 404:
                        print(f"No data for {date_str} (Status: 404 - Likely a holiday)")
                        return [], [date_str, "404", "No data available"]
                    elif response.status == 403:
                        print(f"Access denied for {date_str} (Status: 403 - Attempt {attempt + 1}/{retries})")
                        if attempt < retries - 1:
                            await asyncio.sleep(5)
                        else:
                            print(f"Skipping {date_str} after {retries} attempts")
                            return [], [date_str, "403", "Access denied after retries"]
                    else:
                        print(f"No data for {date_str} (Status: {response.status})")
                        return [], [date_str, str(response.status), "Unexpected status"]
            except Exception as e:
                print(f"Failed to fetch {url}: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                else:
                    print(f"Skipping {date_str} after {retries} attempts")
                    return [], [date_str, "Exception", str(e)]
        return [], [date_str, "Unknown", "Failed after retries"]

# Main async function to fetch all URLs
async def fetch_all():
    semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, date_str, url, extension, semaphore) for date_str, url, extension in dates_to_fetch]
        results = await asyncio.gather(*tasks)
        for result, missed in results:
            all_data.extend(result)
            if missed:
                missed_days.append(missed)
        
        # Save progress every 1000 entries
        if len(all_data) % 1000 == 0 and all_data:
            pd.DataFrame(all_data, columns=["CIK", "Company Name", "Form Type", "Date Filed", "File Name"]).to_csv(output_file, index=False)
            print(f"Saved progress to {output_file}")
        
        # Save missed days incrementally
        if missed_days:
            pd.DataFrame(missed_days, columns=["Date", "Status", "Reason"]).to_csv(missed_days_file, index=False)
            print(f"Saved missed days to {missed_days_file}")

# Run the async fetch
if __name__ == "__main__":
    asyncio.run(fetch_all())
    
    # Final save for successful data
    if all_data:
        df = pd.DataFrame(all_data, columns=["CIK", "Company Name", "Form Type", "Date Filed", "File Name"])
        df.to_csv(output_file, index=False)
        print("CSV file generated successfully!")
    
    # Final save for missed days
    if missed_days:
        missed_df = pd.DataFrame(missed_days, columns=["Date", "Status", "Reason"])
        missed_df.to_csv(missed_days_file, index=False)
        print(f"Missed days saved to {missed_days_file}")
    else:
        print("No missed days to report.")