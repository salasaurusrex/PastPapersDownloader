#!/usr/bin/env python3
"""
Download CAIE past papers using proper session handling with cookies.
Downloads A-Level Physics (9702), Mathematics (9709), and Computer Science (9618)
from pastpapers.papacambridge.com
"""

import os
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import time

BASE_DIR = "/home/kdako/Documents/Git Repositories/PastPapersDownloader/output"
os.makedirs(BASE_DIR, exist_ok=True)

SUBJECTS = [
    {"name": "Physics", "code": "9702"},
    {"name": "Mathematics", "code": "9709"},
    {"name": "ComputerScience", "code": "9618"},
]

HEADERS_GET = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

HEADERS_SUBDOC = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
}

def main():
    session = requests.Session()
    
    # First: navigate to the homepage to establish session cookies
    print("Establishing session...")
    try:
        resp = session.get("https://pastpapers.papacambridge.com/", headers=HEADERS_GET, timeout=30)
        print(f"  Home status: {resp.status_code}, final URL: {resp.url}")
        print(f"  Cookies: {dict(session.cookies)}")
    except Exception as e:
        print(f"  ERROR: {e}")
        return
    
    # Now try each subject page
    for subject in SUBJECTS:
        name = subject["name"]
        code = subject["code"]
        url = f"https://pastpapers.papacambridge.com/a-levels/{code}-{name.lower().replace(' ', '-')}/"
        
        print(f"\n{'='*60}")
        print(f"  Subject: {name} (Code: {code})")
        print(f"  URL: {url}")
        
        subject_dir = os.path.join(BASE_DIR, f"A-Level {name}")
        
        try:
            resp = session.get(url, headers=HEADERS_GET, timeout=30)
            print(f"  Status: {resp.status_code}, final URL: {resp.url}")
            print(f"  Content length: {len(resp.text)}")
            
            if resp.status_code != 200 or "papacambridge.com/" == resp.url or len(resp.text) < 5000:
                print(f"  REDIRECTED/BLOCKED - trying with fresh cookies from home...")
                # Re-fetch home to refresh cookies
                session.cookies.clear()
                resp = session.get("https://pastpapers.papacambridge.com/", headers=HEADERS_GET, timeout=30)
                print(f"  Home refetched, cookies: {dict(session.cookies)}")
                resp = session.get(url, headers=HEADERS_GET, timeout=30)
                print(f"  Retry status: {resp.status_code}, final URL: {resp.url}")
            
            if resp.status_code != 200 or len(resp.text) < 10000:
                print(f"  Cannot access subject page (status={resp.status_code}, len={len(resp.text)})")
                print(f"  Page content preview:")
                print(f"    {resp.text[:300]}")
                continue
            
            soup = BeautifulSoup(resp.text, "lxml")
            
            # Find season/year links
            season_links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if not text or len(text) < 3:
                    continue
                
                full_url = urllib.parse.urljoin(url, str(href))
                
                # Look for season patterns
                if re.search(r'(June|Oct|Nov|March|May|January|February|Summer|Winter)\s*\d{4}', text, re.IGNORECASE) or \
                   re.search(r'\d{4}\s*(June|Oct|Nov|March|May)', text, re.IGNORECASE):
                    season_links.append((text, full_url))
            
            print(f"  Found {len(season_links)} season links")
            
            # Also look for links containing the subject code
            code_links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if not text:
                    continue
                full_url = urllib.parse.urljoin(url, str(href))
                if code in href or code in text:
                    if (text, full_url) not in season_links:
                        code_links.append((text, full_url))
            
            if code_links:
                print(f"  Found {len(code_links)} links containing subject code")
                # Use code_links as fallback for seasons
                if not season_links:
                    season_links = code_links
            
            if not season_links:
                # Dump some links for debugging
                all_links = []
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text(strip=True)
                    if text and len(text) > 5:
                        full_url = urllib.parse.urljoin(url, str(href))
                        if not any(x in full_url for x in ['javascript:', '#', 'mailto:', 'wp-login', 'wp-admin']):
                            if not any(x in text.lower() for x in ['login', 'cart', 'account', 'orders', 'wishlist', 'search', 'contact']):
                                all_links.append((text[:60], full_url))
                
                print(f"  No season links found. Sample of links:")
                for t, u in all_links[:15]:
                    print(f"    {t} -> {u}")
                continue
            
            os.makedirs(subject_dir, exist_ok=True)
            
            downloaded = 0
            for season_text, season_url in season_links[:10]:
                sname = re.sub(r'[^\w\-]', '_', season_text)[:50]
                season_dir = os.path.join(subject_dir, sname)
                os.makedirs(season_dir, exist_ok=True)
                
                print(f"\n  Season: {season_text}")
                print(f"  URL: {season_url}")
                
                try:
                    sresp = session.get(season_url, headers=HEADERS_SUBDOC, timeout=30)
                    print(f"    Status: {sresp.status_code}, len: {len(sresp.text)}")
                    
                    if sresp.status_code != 200 or len(sresp.text) < 5000:
                        print(f"    Skipping (cannot access)")
                        continue
                    
                    ssoup = BeautifulSoup(sresp.text, "lxml")
                    
                    # Find paper download links
                    paper_links = []
                    for a in ssoup.find_all("a", href=True):
                        href = a["href"]
                        text = a.get_text(strip=True)
                        if not text:
                            continue
                        
                        full_url = urllib.parse.urljoin(season_url, str(href))
                        
                        # Look for PDF/ZIP/DOCX links with paper-related text
                        is_paper = False
                        text_lower = text.lower()
                        
                        if any(ext in full_url.lower() for ext in ['.pdf', '.zip', '.docx', '.doc']):
                            if any(p in text_lower for p in ['paper', 'qp_', 'ms_', 'er_', 'question', 'mark scheme', 
                                                               'examiner', 'grade threshold', 'insert', 'code', '9702', '9709', '9618']):
                                is_paper = True
                        
                        if is_paper:
                            paper_links.append((text, full_url))
                    
                    print(f"    Found {len(paper_links)} paper links")
                    
                    for ptext, purl in paper_links[:20]:
                        fname = re.sub(r'[^\w\.\-]', '_', ptext)[:100]
                        ext = os.path.splitext(purl)[1]
                        if ext and ext.lower() in ['.pdf', '.zip', '.docx', '.doc']:
                            fname = re.sub(r'[^\w\.\-]', '_', ptext)[:100 - len(ext)] + ext
                        elif not fname.lower().endswith('.pdf'):
                            fname += '.pdf'
                        
                        fpath = os.path.join(season_dir, fname)
                        
                        if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
                            print(f"      Skipping (exists): {fname}")
                            continue
                        
                        print(f"      Downloading: {fname}")
                        try:
                            preq = session.get(purl, headers={
                                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Accept": "*/*",
                                "Accept-Language": "en-US,en;q=0.5",
                                "Accept-Encoding": "gzip, deflate, br",
                                "Connection": "keep-alive",
                                "Referer": season_url,
                            }, timeout=60)
                            
                            if preq.status_code == 200 and len(preq.content) > 1000:
                                with open(fpath, 'wb') as f:
                                    f.write(preq.content)
                                print(f"        OK: {len(preq.content)} bytes")
                                downloaded += 1
                            else:
                                print(f"        FAIL: HTTP {preq.status_code}, size {len(preq.content)}")
                        except Exception as e:
                            print(f"        ERROR: {e}")
                        
                        time.sleep(0.5)  # Rate limiting
                
                except Exception as e:
                    print(f"    ERROR fetching season: {e}")
            
            print(f"\n  DONE: Downloaded {downloaded} files for {name}")
        
        except Exception as e:
            print(f"  ERROR: {e}")
        
        time.sleep(2)

if __name__ == "__main__":
    main()
