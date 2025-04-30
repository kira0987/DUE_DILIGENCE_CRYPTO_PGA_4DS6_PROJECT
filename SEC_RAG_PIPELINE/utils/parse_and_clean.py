def clean_filing_text(raw_text):
    # Basic cleaning of SEC text
    cleaned = raw_text.replace('\xa0', ' ').replace('\n', '\n')
    return cleaned.strip()