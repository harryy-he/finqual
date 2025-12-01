import uuid

sec_headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com",
    "User-Agent": f"Your Name (your@email.com; {uuid.uuid4()})",
    'Accept-Encoding': 'gzip, deflate',
}