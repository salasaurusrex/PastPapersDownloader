#!/usr/bin/env python3
"""
Direct CAIE past papers downloader.
Constructs download URLs from known patterns and downloads via requests
with browser session cookies.

URL patterns discovered:
- Season page: https://pastpapers.papacambridge.com/papers/caie/as-and-a-level-{SUBJECT_CODE}-{SEASON_SLUG}
- Download URL: https://pastpapers.papacambridge.com/download_file.php?files=<encoded-file-url>
- File URL: https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{SYLLABUS}_{SEASON_CODE}_{TYPE}_{NUM}.pdf

Season codes: s25 = May/June 2025, s24 = May/June 2024, etc.
For Oct/Nov: s25 = Oct/Nov 2025 (same code, different season slug)
"""

import os
import requests
import urllib.parse
import time
import re

BASE_DIR = "/home/kdako/Documents/Git Repositories/PastPapersDownloader/output"
os.makedirs(BASE_DIR, exist_ok=True)

# Subject definitions: code, name, and the season slugs to download
SUBJECTS = [
    {
        "name": "Physics",
        "code": "9702",
        "slug": "physics-9702",
        "seasons": [
            "2026-may-june", "2026-march",
            "2025-oct-nov", "2025-may-june", "2025-march",
            "2024-oct-nov", "2024-may-june", "2024-march",
            "2023-oct-nov", "2023-may-june", "2023-march",
            "2022-oct-nov", "2022-may-june", "2022-feb-march",
            "2021-oct-nov", "2021-may-june", "2021-march",
            "2020-oct-nov", "2020-may-june", "2020-march",
            "2019-oct-nov", "2019-may-june", "2019-march",
            "2018-oct-nov", "2018-may-june", "2018-march",
            "2017-nov", "2017-mar", "2017-jun",
            "2016-nov", "2016-mar", "2016-jun",
            "2015-nov", "2015-jun",
            "2014-nov", "2014-jun",
            "2013-nov", "2013-jun",
            "2012-nov", "2012-jun",
            "2011-nov", "2011-jun",
            "2010-nov", "2010-jun",
            "2009-nov", "2009-jun",
            "2008-nov", "2008-jun",
            "2007-nov", "2007-jun",
            "2006-nov", "2006-jun",
            "2005-nov", "2005-jun",
            "2004-nov", "2004-jun",
            "2003-nov", "2003-jun",
            "2002-nov", "2002-jun",
        ]
    },
    {
        "name": "Mathematics",
        "code": "9709",
        "slug": "mathematics-9709",
        "seasons": [
            "2026-may-june", "2026-march",
            "2025-oct-nov", "2025-may-june", "2025-march",
            "2024-oct-nov", "2024-may-june", "2024-march",
            "2023-oct-nov", "2023-may-june", "2023-march",
            "2022-oct-nov", "2022-may-june", "2022-feb-march",
            "2021-oct-nov", "2021-may-june", "2021-march",
            "2020-oct-nov", "2020-may-june", "2020-march",
            "2019-oct-nov", "2019-may-june", "2019-march",
            "2018-oct-nov", "2018-may-june", "2018-march",
            "2017-nov", "2017-mar", "2017-jun",
            "2016-nov", "2016-mar", "2016-jun",
            "2015-nov", "2015-jun",
            "2014-nov", "2014-jun",
            "2013-nov", "2013-jun",
            "2012-nov", "2012-jun",
            "2011-nov", "2011-jun",
            "2010-nov", "2010-jun",
        ]
    },
    {
        "name": "ComputerScience",
        "code": "9618",
        "slug": "computer-science-9618",
        "seasons": [
            "2026-may-june", "2026-march",
            "2025-oct-nov", "2025-may-june", "2025-march",
            "2024-oct-nov", "2024-may-june", "2024-march",
            "2023-oct-nov", "2023-may-june", "2023-march",
            "2022-oct-nov", "2022-may-june", "2022-feb-march",
            "2021-oct-nov", "2021-may-june", "2021-march",
            "2020-oct-nov", "2020-may-june", "2020-march",
            "2019-oct-nov", "2019-may-june", "2019-march",
            "2018-oct-nov", "2018-may-june", "2018-march",
            "2017-nov", "2017-mar", "2017-jun",
            "2016-nov", "2016-mar", "2016-jun",
            "2015-nov", "2015-jun",
            "2014-nov", "2014-jun",
        ]
    },
]

# Paper types and numbers to try
# qp = question paper, ms = mark scheme, er = examiner report, 
# gt = grade threshold, ci = confidential instructions
PAPER_TYPES = {
    "qp": list(range(11, 15)) + list(range(21, 25)) + list(range(31, 36)) + [37, 38] + list(range(41, 45)) + list(range(51, 55)),
    "ms": list(range(11, 15)) + list(range(21, 25)) + list(range(31, 36)) + [37, 38] + list(range(41, 45)) + list(range(51, 55)),
    "er": [11, 12, 13, 14, 21, 22, 23, 24],  # examiner reports - fewer
    "gt": [],  # grade threshold - single file per season
    "ci": [31, 32, 33, 34, 35, 37, 38],  # confidential instructions
}

# Season code mapping: which "sYY" code to use for each season slug
# May/June seasons use s{YY} where YY = last 2 digits of year
# Oct/Nov seasons also use s{YY}
# March seasons use s{YY} too
def get_season_code(season_slug):
    """Extract season code like 's25' from slug like '2025-may-june'"""
    match = re.match(r'(\d{4})', season_slug)
    if match:
        year = match.group(1)
        yy = year[2:]  # last 2 digits
        return f"s{yy}"
    return None

# Headers that work for downloads
DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def main():
    session = requests.Session()
    
    # Set up browser-like cookies by first visiting the homepage
    print("Setting up session cookies...")
    browser_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    
    try:
        resp = session.get("https://pastpapers.papacambridge.com/", 
                          headers=browser_headers, timeout=30)
        print(f"  Home: {resp.status_code}, cookies: {dict(session.cookies)}")
    except Exception as e:
        print(f"  Warning: Could not establish session: {e}")
    
    total_downloaded = 0
    
    for subject in SUBJECTS:
        name = subject["name"]
        code = subject["code"]
        slug = subject["slug"]
        seasons = subject["seasons"]
        
        subject_dir = os.path.join(BASE_DIR, f"A-Level {name}")
        os.makedirs(subject_dir, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"  Subject: {name} ({code})")
        print(f"  {len(seasons)} seasons to process")
        print(f"{'='*60}")
        
        subject_downloaded = 0
        subject_skipped = 0
        
        for season_slug in seasons:
            season_code = get_season_code(season_slug)
            if not season_code:
                continue
            
            # Create season directory
            season_dir_name = season_slug.replace('-', ' ')
            season_dir = os.path.join(subject_dir, season_dir_name)
            os.makedirs(season_dir, exist_ok=True)
            
            season_skipped = 0
            
            print(f"\n  Season: {season_slug} (code: {season_code})")
            
            season_downloaded = 0
            season_files = 0
            
            # Try each paper type
            for ptype, numbers in PAPER_TYPES.items():
                for num in numbers:
                    # Construct the file URL
                    filename = f"{code}_{season_code}_{ptype}_{num}.pdf"
                    file_url = f"https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{filename}"
                    
                    # Construct the download URL
                    encoded = urllib.parse.quote(file_url, safe='')
                    download_url = f"https://pastpapers.papacambridge.com/download_file.php?files={encoded}"
                    
                    # Output filename
                    out_name = f"{code}_{season_code}_{ptype}_{num}.pdf"
                    out_path = os.path.join(season_dir, out_name)
                    
                    # Skip if already downloaded
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
                        season_skipped += 1
                        continue
                    
                    season_files += 1
                    
                    try:
                        resp = session.get(download_url, headers=DOWNLOAD_HEADERS, timeout=30)
                        
                        if resp.status_code == 200 and len(resp.content) > 5000 and resp.headers.get('content-type', '').startswith('application/pdf'):
                            with open(out_path, 'wb') as f:
                                f.write(resp.content)
                            print(f"    OK: {out_name} ({len(resp.content)} bytes)")
                            season_downloaded += 1
                            subject_downloaded += 1
                            total_downloaded += 1
                        elif resp.status_code == 200 and len(resp.content) > 1000:
                            # Might be an HTML error page or other format
                            content_type = resp.headers.get('content-type', '')
                            if 'html' in content_type.lower():
                                # File doesn't exist
                                pass
                            else:
                                with open(out_path, 'wb') as f:
                                    f.write(resp.content)
                                print(f"    OK (non-pdf): {out_name} ({len(resp.content)} bytes, {content_type})")
                                season_downloaded += 1
                                subject_downloaded += 1
                                total_downloaded += 1
                        else:
                            # File doesn't exist or error
                            pass
                    except Exception as e:
                        pass
                    
                    time.sleep(0.1)  # Small delay to avoid rate limiting
            
            print(f"    Downloaded: {season_downloaded}, Skipped: {season_skipped}, Total attempts: {season_files}")
        
        print(f"\n  {name} total: {subject_downloaded} files downloaded")
    
    print(f"\n{'='*60}")
    print(f"  GRAND TOTAL: {total_downloaded} files downloaded")
    print(f"{'='*60}")
    
    # List what we got
    print("\n  Downloaded files:")
    for root, dirs, files in os.walk(BASE_DIR):
        for f in sorted(files):
            fpath = os.path.join(root, f)
            size = os.path.getsize(fpath)
            print(f"    {os.path.relpath(fpath, BASE_DIR)} ({size} bytes)")

if __name__ == "__main__":
    main()
