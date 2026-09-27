#!/usr/bin/env python3
"""
PapaCambridge downloader with JavaScript-capable HTTP client.
Attempts to replicate browser behavior by:
1. Fetching the homepage with full browser-like headers  
2. Parsing any embedded state/data from the homepage
3. Following subject links properly
4. Using proper session with cookies
"""

import os
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import time
import json

BASE_DIR = "/home/kdako/Documents/Git Repositories/PastPapersDownloader/output"
os.makedirs(BASE_DIR, exist_ok=True)

SUBJECTS = [
    {"name": "Physics", "code": "9702"},
    {"name": "Mathematics", "code": "9709"},
    {"name": "ComputerScience", "code": "9618"},
]

# Full browser-like headers for initial request
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

DOWNLOAD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://pastpapers.papacambridge.com/",
}

def extract_embedded_data(html):
    """Extract JSON data embedded in script tags"""
    data = {}
    
    # Look for window.__INITIAL_STATE__, window.APP_DATA, etc.
    patterns = [
        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
        r'window\.__PRELOADED_STATE__\s*=\s*(\{.*?\});',
        r'window\.APP_STATE\s*=\s*(\{.*?\});',
        r'window\.__NEXT_DATA__\s*=\s*(\{.*?\});',
        r'window\.__DATA__\s*=\s*(\{.*?\});',
        r'dataLayer\s*=\s*(\[.*?\]);',
        r'window\.__WPCF7\s*=\s*(\{.*?\});',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match)
                data.update(parsed)
                print(f"  Found embedded data: {list(parsed.keys())[:5]}...")
            except json.JSONDecodeError:
                pass
    
    return data

def main():
    session = requests.Session()
    
    print("="*60)
    print("  Step 1: Fetching homepage")
    print("="*60)
    
    try:
        resp = session.get("https://pastpapers.papacambridge.com/", 
                          headers=BROWSER_HEADERS, timeout=30)
        print(f"  Status: {resp.status_code}")
        print(f"  Final URL: {resp.url}")
        print(f"  Content length: {len(resp.text)}")
        print(f"  Cookies: {dict(session.cookies)}")
        
        if resp.status_code != 200:
            print("  FAILED to fetch homepage")
            return
        
        # Check what page we actually got
        soup = BeautifulSoup(resp.text, 'lxml')
        title = soup.title.string if soup.title else "No title"
        print(f"  Page title: {title}")
        
        # Extract embedded data
        embedded = extract_embedded_data(resp.text)
        
        # Look for subject navigation links in the homepage
        print("\n  Looking for subject links on homepage...")
        subject_links = {}
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            
            if not text or len(text) < 3:
                continue
            
            full_url = urllib.parse.urljoin(resp.url, str(href))
            
            # Look for links containing subject codes
            for subj in SUBJECTS:
                if subj["code"] in href or subj["code"] in text:
                    subject_links[subj["code"]] = (text, full_url)
                    print(f"    Found: {text[:50]} -> {full_url}")
        
        # Also look for general A-Level links
        alevel_links = []
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if not text:
                continue
            full_url = urllib.parse.urljoin(resp.url, str(href))
            if "a-level" in str(href).lower() or "a-levels" in str(href).lower() or "a-level" in str(text).lower():
                if full_url not in [x[1] for x in alevel_links]:
                    alevel_links.append((text[:60], full_url))
        
        print(f"\n  A-Level links found: {len(alevel_links)}")
        for t, u in alevel_links[:10]:
            print(f"    {t} -> {u}")
        
        # Try the papacambridge.com domain too
        print("\n" + "="*60)
        print("  Step 2: Trying papacambridge.com domain")
        print("="*60)
        
        session2 = requests.Session()
        resp2 = session2.get("https://papacambridge.com/", headers=BROWSER_HEADERS, timeout=30)
        print(f"  Status: {resp2.status_code}")
        print(f"  Final URL: {resp2.url}")
        print(f"  Content length: {len(resp2.text)}")
        print(f"  Cookies: {dict(session2.cookies)}")
        
        if resp2.status_code == 200:
            soup2 = BeautifulSoup(resp2.text, 'lxml')
            title2 = soup2.title.string if soup2.title else "No title"
            print(f"  Page title: {title2}")
            
            # Look for A-Level subject links
            print("\n  Looking for A-Level subject links on papacambridge.com...")
            for a in soup2.find_all("a", href=True):
                text = a.get_text(strip=True)
                href = a["href"]
                if not text or len(text) < 3:
                    continue
                
                full_url = urllib.parse.urljoin(resp2.url, str(href))
                
                if "a-level" in href.lower() or "a-level" in text.lower() or "as-and-a" in href.lower():
                    print(f"    {text[:60]} -> {full_url}")
                
                for subj in SUBJECTS:
                    if subj["code"] in href or subj["code"] in text:
                        print(f"    *** FOUND {subj['name']}: {text[:60]} -> {full_url}")
        
        # Try to use the session to access subject pages
        print("\n" + "="*60)
        print("  Step 3: Accessing subject pages with session")
        print("="*60)
        
        for subj in SUBJECTS:
            code = subj["code"]
            name = subj["name"]
            
            # Try multiple URL patterns
            urls_to_try = [
                f"https://pastpapers.papacambridge.com/a-levels/{code}-{name.lower().replace(' ', '')}/",
                f"https://pastpapers.papacambridge.com/a-levels/{code}-{name.lower()}/",
                f"https://pastpapers.papacambridge.com/a-level/{code}-{name.lower().replace(' ', '')}/",
                f"https://pastpapers.papacambridge.com/{code}/",
                f"https://papacambridge.com/a-levels/{code}-{name.lower().replace(' ', '')}/",
                f"https://papacambridge.com/a-level/{code}/",
            ]
            
            print(f"\n  Subject: {name} ({code})")
            
            for test_url in urls_to_try:
                try:
                    test_resp = session.get(test_url, headers=BROWSER_HEADERS, timeout=15, allow_redirects=True)
                    print(f"    Trying: {test_url}")
                    print(f"      Status: {test_resp.status_code}, Final: {test_resp.url}, Len: {len(test_resp.text)}")
                    
                    if test_resp.status_code == 200 and len(test_resp.text) > 10000 and "papacambridge.com/" not in test_resp.url:
                        print(f"      *** SUCCESS! Accessing subject page.")
                        print(f"      Title: {BeautifulSoup(test_resp.text, 'lxml').title.string if BeautifulSoup(test_resp.text, 'lxml').title else 'N/A'}")
                        
                        # Extract season links
                        soup3 = BeautifulSoup(test_resp.text, 'lxml')
                        seasons = []
                        for a in soup3.find_all("a", href=True):
                            text = a.get_text(strip=True)
                            href = a["href"]
                            if not text:
                                continue
                            full_url = urllib.parse.urljoin(test_url, str(href))
                            if re.search(r'(June|Oct|Nov|March|May|January|February|Summer|Winter)\s*\d{4}', text, re.IGNORECASE):
                                seasons.append((text, full_url))
                        
                        print(f"      Seasons found: {len(seasons)}")
                        for s_text, s_url in seasons[:5]:
                            print(f"        {s_text} -> {s_url}")
                        
                        # Create directory and download
                        subj_dir = os.path.join(BASE_DIR, f"A-Level {name}")
                        os.makedirs(subj_dir, exist_ok=True)
                        
                        downloaded = 0
                        for s_text, s_url in seasons[:10]:
                            sname = re.sub(r'[^\w\-]', '_', s_text)[:50]
                            sdir = os.path.join(subj_dir, sname)
                            os.makedirs(sdir, exist_ok=True)
                            
                            print(f"\n      Season: {s_text}")
                            sresp = session.get(s_url, headers=BROWSER_HEADERS, timeout=30)
                            print(f"      Status: {sresp.status_code}, Len: {len(sresp.text)}")
                            
                            if sresp.status_code == 200 and len(sresp.text) > 5000:
                                spSoup = BeautifulSoup(sresp.text, 'lxml')
                                papers = []
                                for a in spSoup.find_all("a", href=True):
                                    text = a.get_text(strip=True)
                                    href = a["href"]
                                    if not text:
                                        continue
                                    full_url = urllib.parse.urljoin(s_url, str(href))
                                    text_lower = text.lower()
                                    
                                    if any(ext in full_url.lower() for ext in ['.pdf', '.zip', '.docx', '.doc']):
                                        if any(p in text_lower for p in ['paper', 'qp_', 'ms_', 'er_', 'question', 
                                                                       'mark scheme', 'examiner', 'grade', 'insert', 
                                                                       code, '9702', '9709', '9618']):
                                            papers.append((text, full_url))
                                
                                print(f"      Papers found: {len(papers)}")
                                
                                for ptext, purl in papers[:15]:
                                    fname = re.sub(r'[^\w\.\-]', '_', ptext)[:100]
                                    ext = os.path.splitext(purl)[1]
                                    if ext and ext.lower() in ['.pdf', '.zip', '.docx', '.doc']:
                                        fname = re.sub(r'[^\w\.\-]', '_', ptext)[:100-len(ext)] + ext
                                    elif not fname.lower().endswith('.pdf'):
                                        fname += '.pdf'
                                    
                                    fpath = os.path.join(sdir, fname)
                                    
                                    if os.path.exists(fpath) and os.path.getsize(fpath) > 1000:
                                        print(f"        Skip (exists): {fname}")
                                        continue
                                    
                                    print(f"        Downloading: {fname}")
                                    try:
                                        preq = session.get(purl, headers=DOWNLOAD_HEADERS, timeout=60)
                                        if preq.status_code == 200 and len(preq.content) > 1000:
                                            with open(fpath, 'wb') as f:
                                                f.write(preq.content)
                                            print(f"          OK: {len(preq.content)} bytes")
                                            downloaded += 1
                                        else:
                                            print(f"          FAIL: {preq.status_code}, {len(preq.content)} bytes")
                                    except Exception as e:
                                        print(f"          ERROR: {e}")
                                    
                                    time.sleep(0.3)
                        
                        print(f"\n      Total downloaded for {name}: {downloaded}")
                        break  # Success, move to next subject
                        
                except Exception as e:
                    print(f"    Error with {test_url}: {e}")
            
            time.sleep(1)
    
    except Exception as e:
        print(f"  FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
