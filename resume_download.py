#!/usr/bin/env python3
"""
Resume downloader - only for subjects not yet downloaded.
"""

import os
import requests
import urllib.parse
import time
import re

BASE_DIR = "/home/kdako/Documents/Git Repositories/PastPapersDownloader/output"
os.makedirs(BASE_DIR, exist_ok=True)

# Only Mathematics and Computer Science (Physics already done)
SUBJECTS = [
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

PAPER_TYPES = {
    "qp": list(range(11, 15)) + list(range(21, 25)) + list(range(31, 36)) + [37, 38] + list(range(41, 45)) + list(range(51, 55)),
    "ms": list(range(11, 15)) + list(range(21, 25)) + list(range(31, 36)) + [37, 38] + list(range(41, 45)) + list(range(51, 55)),
    "er": [11, 12, 13, 14, 21, 22, 23, 24],
    "gt": [],
    "ci": [31, 32, 33, 34, 35, 37, 38],
}

def get_season_code(season_slug):
    match = re.match(r'(\d{4})', season_slug)
    if match:
        return f"s{match.group(1)[2:]}"
    return None

DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def main():
    session = requests.Session()
    
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
        print(f"Session established: {resp.status_code}")
    except Exception as e:
        print(f"Warning: {e}")
    
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
        print(f"  {len(seasons)} seasons")
        print(f"{'='*60}")
        
        subject_downloaded = 0
        subject_skipped = 0
        
        for season_slug in seasons:
            season_code = get_season_code(season_slug)
            if not season_code:
                continue
            
            season_dir_name = season_slug.replace('-', ' ')
            season_dir = os.path.join(subject_dir, season_dir_name)
            os.makedirs(season_dir, exist_ok=True)
            
            season_skipped = 0
            season_downloaded = 0
            season_files = 0
            
            for ptype, numbers in PAPER_TYPES.items():
                for num in numbers:
                    filename = f"{code}_{season_code}_{ptype}_{num}.pdf"
                    file_url = f"https://pastpapers.papacambridge.com/directories/CAIE/CAIE-pastpapers/upload/{filename}"
                    encoded = urllib.parse.quote(file_url, safe='')
                    download_url = f"https://pastpapers.papacambridge.com/download_file.php?files={encoded}"
                    
                    out_name = f"{code}_{season_code}_{ptype}_{num}.pdf"
                    out_path = os.path.join(season_dir, out_name)
                    
                    if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
                        season_skipped += 1
                        continue
                    
                    season_files += 1
                    
                    try:
                        resp = session.get(download_url, headers=DOWNLOAD_HEADERS, timeout=30)
                        
                        if resp.status_code == 200 and len(resp.content) > 5000 and resp.headers.get('content-type', '').startswith('application/pdf'):
                            with open(out_path, 'wb') as f:
                                f.write(resp.content)
                            season_downloaded += 1
                            subject_downloaded += 1
                            total_downloaded += 1
                        elif resp.status_code == 200 and len(resp.content) > 1000:
                            ct = resp.headers.get('content-type', '')
                            if 'html' not in ct.lower():
                                with open(out_path, 'wb') as f:
                                    f.write(resp.content)
                                season_downloaded += 1
                                subject_downloaded += 1
                                total_downloaded += 1
                    except:
                        pass
                    
                    time.sleep(0.05)
            
            print(f"    {season_slug}: {season_downloaded} downloaded, {season_skipped} skipped")
        
        print(f"  {name} total: {subject_downloaded} new files")
    
    print(f"\n  GRAND TOTAL: {total_downloaded} additional files")
    
    # Summary
    print("\n  Final breakdown:")
    for root, dirs, files in os.walk(BASE_DIR):
        if files:
            level = root.replace(BASE_DIR, '').count(os.sep)
            if level == 1:
                subdir = os.path.basename(root)
                print(f"    {subdir}: {len(files)} files")

if __name__ == "__main__":
    main()
