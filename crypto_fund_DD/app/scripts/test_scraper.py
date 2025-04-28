from intelligent_scraper import intelligent_scrape

if __name__ == "__main__":
    query = "Bitcoin regulations 2024"
    results = intelligent_scrape(query, mode="serper", num_results=2)
    for idx, r in enumerate(results):
        print(f"\n🔹 Result {idx+1}:\n")
        print(r[:500])  # Only show first 500 characters
