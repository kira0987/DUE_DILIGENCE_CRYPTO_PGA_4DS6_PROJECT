import asyncio
import aiohttp
import os
from sec_api import QueryApi
import time
import logging

# Replace with your actual API key from sec-api.io
API_KEY = '2e97aec138f963ea7b4ce5bab426a9237989e0420833a13cbe8dcc5fd09c3f36'

# Folder to save prospectuses
OUTPUT_FOLDER = 'crypto_prospectuses'

# Create the output folder if it doesn't exist
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Expanded list of 85 highly regulated cryptocurrency funds with their CIK numbers
crypto_funds = [
    # Existing Major Bitcoin ETFs with Known CIK Numbers
    {'ticker': 'IBIT', 'cik': '1980994'},  # iShares Bitcoin Trust (BlackRock)
    {'ticker': 'FBTC', 'cik': '1852317'},  # Fidelity Wise Origin Bitcoin Fund
    {'ticker': 'ARKB', 'cik': '1869699'},  # ARK 21Shares Bitcoin ETF
    {'ticker': 'BITB', 'cik': '1763415'},  # Bitwise Bitcoin ETF
    {'ticker': 'BTCO', 'cik': '1898020'},  # Invesco Galaxy Bitcoin ETF
    {'ticker': 'EZBC', 'cik': '1867235'},  # Franklin Bitcoin ETF
    {'ticker': 'BRRR', 'cik': '1922449'},  # Valkyrie Bitcoin Fund
    {'ticker': 'HODL', 'cik': '1918762'},  # VanEck Bitcoin Trust
    {'ticker': 'BTCW', 'cik': '1897702'},  # WisdomTree Bitcoin Fund
    {'ticker': 'GBTC', 'cik': '1588486'},  # Grayscale Bitcoin Trust (ETF conversion)
    {'ticker': 'DEFI', 'cik': '1871283'},  # Hashdex Bitcoin Futures ETF
    {'ticker': 'BITO', 'cik': '1766930'},  # ProShares Bitcoin Strategy ETF
    {'ticker': 'XBTF', 'cik': '1454938'},  # VanEck Bitcoin Strategy ETF
    {'ticker': 'BTF', 'cik': '1711002'},   # Valkyrie Bitcoin Strategy ETF
    {'ticker': 'BTOP', 'cik': '1829774'},  # Bitwise Bitcoin and Ether Equal Weight ETF

    # Previously Added Hypothetical Funds
    {'ticker': 'JPMB', 'cik': 'TBD0001'},  # JPMorgan Bitcoin ETF
    {'ticker': 'GSBT', 'cik': 'TBD0002'},  # Goldman Sachs Bitcoin Trust
    {'ticker': 'MSBT', 'cik': 'TBD0003'},  # Morgan Stanley Bitcoin ETF
    {'ticker': 'SCHB', 'cik': 'TBD0004'},  # Schwab Bitcoin ETF
    {'ticker': 'VGB', 'cik': 'TBD0005'},   # Vanguard Bitcoin ETF
    {'ticker': 'SPXB', 'cik': 'TBD0006'},  # State Street SPDR Bitcoin ETF
    {'ticker': 'NYBT', 'cik': 'TBD0007'},  # NYSE Bitcoin Trust
    {'ticker': 'CMEB', 'cik': 'TBD0008'},  # CME Bitcoin ETF
    {'ticker': 'UBSB', 'cik': 'TBD0009'},  # UBS Bitcoin ETF
    {'ticker': 'CITI', 'cik': 'TBD0010'},  # Citi Bitcoin Trust
    {'ticker': 'ETHB', 'cik': 'TBD0011'},  # iShares Ethereum Trust
    {'ticker': 'FETH', 'cik': 'TBD0012'},  # Fidelity Ethereum Fund
    {'ticker': 'ARET', 'cik': 'TBD0013'},  # ARK 21Shares Ethereum ETF
    {'ticker': 'BITE', 'cik': 'TBD0014'},  # Bitwise Ethereum ETF
    {'ticker': 'GETH', 'cik': 'TBD0015'},  # Grayscale Ethereum Trust (ETF conversion)
    {'ticker': 'CRYP', 'cik': 'TBD0016'},  # BlackRock Crypto Blend ETF
    {'ticker': 'MULT', 'cik': 'TBD0017'},  # Fidelity Multi-Crypto Fund
    {'ticker': 'ARKC', 'cik': 'TBD0018'},  # ARK Crypto Innovation ETF
    {'ticker': 'BTDV', 'cik': 'TBD0019'},  # Bitwise Diversified Crypto ETF
    {'ticker': 'INVC', 'cik': 'TBD0020'},  # Invesco Crypto Portfolio ETF
    {'ticker': 'FRMC', 'cik': 'TBD0021'},  # Franklin Multi-Asset Crypto ETF
    {'ticker': 'VALC', 'cik': 'TBD0022'},  # Valkyrie Crypto Blend ETF
    {'ticker': 'VANC', 'cik': 'TBD0023'},  # VanEck Multi-Crypto Trust
    {'ticker': 'WISC', 'cik': 'TBD0024'},  # WisdomTree Crypto Index ETF
    {'ticker': 'GBMC', 'cik': 'TBD0025'},  # Grayscale Multi-Coin ETF
    {'ticker': 'USDC', 'cik': 'TBD0026'},  # Circle USDC Stablecoin ETF
    {'ticker': 'TETH', 'cik': 'TBD0027'},  # Tether USDt Trust ETF
    {'ticker': 'PAXG', 'cik': 'TBD0028'},  # Paxos Gold-Backed Crypto ETF
    {'ticker': 'DGCC', 'cik': 'TBD0029'},  # Digital Currency Group Crypto Fund
    {'ticker': 'COIN', 'cik': 'TBD0030'},  # Coinbase Global Crypto ETF

    # 40 More Hypothetical Funds
    {'ticker': 'BCHB', 'cik': 'TBD0031'},  # iShares Bitcoin Cash ETF
    {'ticker': 'LTCF', 'cik': 'TBD0032'},  # Fidelity Litecoin Fund
    {'ticker': 'XRPB', 'cik': 'TBD0033'},  # ARK 21Shares Ripple ETF
    {'ticker': 'ADAB', 'cik': 'TBD0034'},  # Bitwise Cardano ETF
    {'ticker': 'SOLB', 'cik': 'TBD0035'},  # Invesco Solana ETF
    {'ticker': 'DOTB', 'cik': 'TBD0036'},  # Franklin Polkadot ETF
    {'ticker': 'AVAX', 'cik': 'TBD0037'},  # Valkyrie Avalanche ETF
    {'ticker': 'LINK', 'cik': 'TBD0038'},  # VanEck Chainlink Trust
    {'ticker': 'ALGO', 'cik': 'TBD0039'},  # WisdomTree Algorand ETF
    {'ticker': 'DOGE', 'cik': 'TBD0040'},  # Grayscale Dogecoin ETF
    {'ticker': 'SHIB', 'cik': 'TBD0041'},  # BlackRock Shiba Inu ETF
    {'ticker': 'MATIC', 'cik': 'TBD0042'}, # Fidelity Polygon Fund
    {'ticker': 'ATOM', 'cik': 'TBD0043'},  # ARK Cosmos ETF
    {'ticker': 'TRXB', 'cik': 'TBD0044'},  # Bitwise Tron ETF
    {'ticker': 'XLM', 'cik': 'TBD0045'},   # Invesco Stellar ETF
    {'ticker': 'VET', 'cik': 'TBD0046'},   # Franklin VeChain ETF
    {'ticker': 'HBAR', 'cik': 'TBD0047'},  # Valkyrie Hedera ETF
    {'ticker': 'XTZ', 'cik': 'TBD0048'},   # VanEck Tezos Trust
    {'ticker': 'EOSB', 'cik': 'TBD0049'},  # WisdomTree EOS ETF
    {'ticker': 'BNBB', 'cik': 'TBD0050'},  # Grayscale Binance Coin ETF
    {'ticker': 'JPME', 'cik': 'TBD0051'},  # JPMorgan Ethereum ETF
    {'ticker': 'GSET', 'cik': 'TBD0052'},  # Goldman Sachs Ethereum Trust
    {'ticker': 'MSE', 'cik': 'TBD0053'},   # Morgan Stanley Ethereum ETF
    {'ticker': 'SCHE', 'cik': 'TBD0054'},  # Schwab Ethereum ETF
    {'ticker': 'VGE', 'cik': 'TBD0055'},   # Vanguard Ethereum ETF
    {'ticker': 'SPXE', 'cik': 'TBD0056'},  # State Street SPDR Ethereum ETF
    {'ticker': 'NYET', 'cik': 'TBD0057'},  # NYSE Ethereum Trust
    {'ticker': 'BXCR', 'cik': 'TBD0071'},  # Blackstone Crypto Fund (Placeholder CIK)
    {'ticker': 'PANX', 'cik': 'TBD0072'},  # Pantera Crypto Fund (Placeholder CIK)
    {'ticker': 'CMEE', 'cik': 'TBD0058'},  # CME Ethereum ETF
    {'ticker': 'UBSE', 'cik': 'TBD0059'},  # UBS Ethereum ETF
    {'ticker': 'CITIE', 'cik': 'TBD0060'}, # Citi Ethereum Trust
    {'ticker': 'CRYPM', 'cik': 'TBD0061'}, # BlackRock Crypto Momentum ETF
    {'ticker': 'MULTE', 'cik': 'TBD0062'}, # Fidelity Multi-Chain ETF
    {'ticker': 'ARKD', 'cik': 'TBD0063'},  # ARK DeFi ETF
    {'ticker': 'BTDG', 'cik': 'TBD0064'},  # Bitwise Growth Crypto ETF
    {'ticker': 'INVD', 'cik': 'TBD0065'},  # Invesco Digital Assets ETF
    {'ticker': 'FRMD', 'cik': 'TBD0066'},  # Franklin Diversified Crypto ETF
    {'ticker': 'VALD', 'cik': 'TBD0067'},  # Valkyrie Dynamic Crypto ETF
    {'ticker': 'VAND', 'cik': 'TBD0068'},  # VanEck Digital Innovation ETF
    {'ticker': 'WISD', 'cik': 'TBD0069'},  # WisdomTree Digital Growth ETF
    {'ticker': 'GBMD', 'cik': 'TBD0070'},  # Grayscale Digital Momentum ETF
]
# Initialize the SEC API
query_api = QueryApi(api_key=API_KEY)

async def get_latest_filing(cik, session, fallback=False):
    """Fetch the latest relevant filing, with fallback to any form if needed."""
    if cik.startswith('TBD'):
        logging.info(f"CIK {cik} is a placeholder. Skipping.")
        return None
    query = {
        "query": {
            "query_string": {
                "query": f"cik:{cik}" + ("" if fallback else " AND (formType:\"S-1\" OR formType:\"S-1/A\" OR formType:\"424B3\" OR formType:\"10-K\" OR formType:\"N-1A\" OR formType:\"485BPOS\" OR formType:\"N-CSR\")")
            }
        },
        "from": "0",
        "size": "1",
        "sort": [{"filedAt": {"order": "desc"}}]
    }
    async with session.post('https://api.sec-api.io', json=query) as response:
        if response.status == 200:
            data = await response.json()
            filings = data.get('filings', [])
            return filings[0] if filings else None
        elif response.status == 429:
            logging.warning(f"Rate limit hit for CIK {cik}. Waiting 1 second...")
            await asyncio.sleep(1)
            return await get_latest_filing(cik, session, fallback)
        else:
            logging.error(f"Failed to query SEC API for CIK {cik}. Status: {response.status}")
            return None

async def download_prospectus(ticker, cik, session, semaphore):
    """Download the prospectus with fallback to any filing."""
    async with semaphore:
        try:
            # Try specific forms first
            filing = await get_latest_filing(cik, session, fallback=False)
            if not filing:
                logging.info(f"No specific filings for {ticker} (CIK: {cik}). Falling back to any form.")
                filing = await get_latest_filing(cik, session, fallback=True)
            
            if filing:
                primary_doc_url = filing.get('linkToFilingDetails')
                form_type = filing.get('formType', 'Unknown').replace('/', '_')
                if primary_doc_url:
                    headers = {
                        'User-Agent': 'duedil houssameddine.benkheder@esprit.tn',  # Customize this
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Referer': 'https://www.sec.gov/edgar/searchedgar/companysearch.html',
                        'Connection': 'keep-alive'
                    }
                    async with session.get(primary_doc_url, headers=headers) as response:
                        if response.status == 200:
                            file_path = os.path.join(OUTPUT_FOLDER, f"{ticker}_prospectus_{form_type}.html")
                            content = await response.text()
                            with open(file_path, 'w', encoding='utf-8') as file:
                                file.write(content)
                            file_size = os.path.getsize(file_path)
                            logging.info(f"Downloaded {file_path} (Size: {file_size} bytes)")
                        elif response.status in (400, 403):
                            logging.warning(f"HTTP {response.status} for {ticker} (CIK: {cik}). Retrying in 5 seconds...")
                            await asyncio.sleep(5)
                            async with session.get(primary_doc_url, headers=headers) as retry_response:
                                if retry_response.status == 200:
                                    file_path = os.path.join(OUTPUT_FOLDER, f"{ticker}_prospectus_{form_type}.html")
                                    content = await retry_response.text()
                                    with open(file_path, 'w', encoding='utf-8') as file:
                                        file.write(content)
                                    file_size = os.path.getsize(file_path)
                                    logging.info(f"Downloaded {file_path} after retry (Size: {file_size} bytes)")
                                else:
                                    logging.error(f"Retry failed for {ticker} (CIK: {cik}). Status: {retry_response.status}")
                        else:
                            logging.error(f"Failed to download for {ticker}. Status: {response.status}")
                else:
                    logging.info(f"No primary document URL for {ticker} (CIK: {cik})")
            else:
                logging.info(f"No filings found for {ticker} (CIK: {cik}) even with fallback")
        except Exception as e:
            logging.error(f"Error downloading for {ticker} (CIK: {cik}): {str(e)}")
        finally:
            await asyncio.sleep(0.1)

async def main():
    """Main function to run asynchronous downloads."""
    semaphore = asyncio.Semaphore(10)
    downloaded_files = []
    async with aiohttp.ClientSession(headers={'Authorization': API_KEY}) as session:
        tasks = [
            download_prospectus(fund['ticker'], fund['cik'], session, semaphore)
            for fund in crypto_funds
        ]
        await asyncio.gather(*tasks)
    
    # Summary of downloaded files
    for file in os.listdir(OUTPUT_FOLDER):
        file_path = os.path.join(OUTPUT_FOLDER, file)
        file_size = os.path.getsize(file_path)
        downloaded_files.append((file, file_size))
    
    logging.info(f"Summary: Downloaded {len(downloaded_files)} files out of {len(crypto_funds)} attempted")
    for file, size in downloaded_files:
        logging.info(f" - {file} (Size: {size} bytes)")

# Run the script
print(f"Starting download of prospectuses into folder '{OUTPUT_FOLDER}'...")
start_time = time.time()
asyncio.run(main())
print(f"\nDownload process completed in {time.time() - start_time:.2f} seconds. Files saved in '{OUTPUT_FOLDER}'.")