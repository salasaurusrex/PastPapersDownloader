#!/usr/bin/env python3
"""
Direct downloader for CAIE past papers using papacambridge.com.
Downloads A-Level Physics (9702), Mathematics (9709), and Computer Science (9618)
from pastpapers.papacambridge.com
"""

import os
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

BASE_DIR = "/home/kdako/Documents/Git Repositories/PastPapersDownloader/output"
os.makedirs(BASE_DIR, exist_ok=True)

SUBJECTS = {
    "Physics": {"code": "9702", "url": "https://pastpapers.papacambridge.com/a-levels/9702-physics/"},
    "Mathematics": {"code": "9709", "url": "https://pastpapers.papacambridge.com/a-levels/9709-mathematics/"},
    "ComputerScience": {"code": "9618", "url": "https://pastpapers.papacambridge.com/a-levels/9618-computer-science/"},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

def get_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s

def extract_links_from_page(url, session):
    """Extract all links from a page, return list of (name, url)"""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return []
    
    soup = BeautifulSoup(resp.text, "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if not text:
            continue
        # Skip various non-content links
        if any(x in href for x in ["javascript:", "#", "mailto:", "wp-", "async", "css", "js", "feed", "wp-json"]):
            continue
        if any(x in text.lower() for x in ["search", "login", "cart", "account", "orders", "wishlist", "contact"]):
            continue
        # Resolve relative URLs
        full_url = urllib.parse.urljoin(url, str(href))
        links.append((text, full_url))
    return links

def is_past_paper_link(text, url):
    """Check if this looks like a past paper download link"""
    text_lower = text.lower()
    # Common patterns for past papers
    patterns = ["qp_", "ms_", "er_", "gt_", "insert_", "9702", "9709", "9618",
                "question paper", "mark scheme", "examiner report", "grade threshold",
                "paper 1", "paper 2", "paper 3", "paper 4", "paper 5", "paper 6",
                "as_", "al_", "gce", "igcse"]
    return any(p in text_lower for p in patterns) or any(p in url.lower() for p in ["pastpaper", "paper", "examen"])

def main():
    session = get_session()
    
    for subject_name, info in SUBJECTS.items():
        code = info["code"]
        url = info["url"]
        print(f"\n{'='*60}")
        print(f"  Subject: {subject_name} (Code: {code})")
        print(f"  URL: {url}")
        print(f"{'='*60}")
        
        subject_dir = os.path.join(BASE_DIR, f"A-Level {subject_name}")
        os.makedirs(subject_dir, exist_ok=True)
        
        # Fetch the subject page
        print(f"\nFetching subject page...")
        links = extract_links_from_page(url, session)
        print(f"  Found {len(links)} links on subject page")
        
        # Identify season/year links
        season_links = []
        for text, href in links:
            # Look for season patterns like "June 2024", "Nov 2023", "Oct/Nov 2024"
            if re.search(r'(June|Oct|Nov|March|May|January|February|Summer|Winter)\s*\d{4}', text, re.IGNORECASE) or \
               re.search(r'\d{4}\s*(June|Oct|Nov|March|May)', text, re.IGNORECASE):
                season_links.append((text, href))
        
        print(f"  Found {len(season_links)} season links")
        
        # If no seasons found via regex, also try links containing the subject code
        if not season_links:
            for text, href in links:
                if code in href or code in text:
                    season_links.append((text, href))
            print(f"  Fallback: {len(season_links)} links containing subject code")
        
        # Visit each season page and download papers
        downloaded = 0
        for season_text, season_url in season_links[:10]:  # Limit to first 10 seasons
            sname = re.sub(r'[^\w\-]', '_', season_text)[:50]
            season_dir = os.path.join(subject_dir, sname)
            os.makedirs(season_dir, exist_ok=True)
            
            print(f"\n  Season: {season_text}")
            print(f"  URL: {season_url}")
            
            season_links_inner = extract_links_from_page(season_url, session)
            
            paper_links = []
            for text, href in season_links_inner:
                if is_past_paper_link(text, href) and href.endswith(('.pdf', '.zip', '.docx', '.doc')):
                    paper_links.append((text, href))
                elif is_past_paper_link(text, href) and any(ext in href.lower() for ext in ['.pdf', '.zip', '.docx', '.doc']):
                    paper_links.append((text, href))
            
            print(f"  Found {len(paper_links)} paper links")
            
            for ptext, purl in paper_links[:20]:  # Limit per season
                # Clean filename
                fname = re.sub(r'[^\w\.\-]', '_', ptext)[:100]
                if not fname.lower().endswith(('.pdf', '.zip', '.docx', '.doc')):
                    # Try to get extension from URL
                    ext = os.path.splitext(purl)[1]
                    if ext:
                        fname += ext
                    else:
                        fname += '.pdf'
                
                fpath = os.path.join(season_dir, fname)
                
                if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
                    print(f"    Skipping (exists): {fname}")
                    continue
                
                print(f"    Downloading: {fname}")
                try:
                    resp = session.get(purl, timeout=60, allow_redirects=True)
                    if resp.status_code == 200 and len(resp.content) > 1000:
                        with open(fpath, 'wb') as f:
                            f.write(resp.content)
                        print(f"      OK: {len(resp.content)} bytes")
                        downloaded += 1
                    else:
                        print(f"      FAIL: HTTP {resp.status_code}, size {len(resp.content)}")
                except Exception as e:
                    print(f"      ERROR: {e}")
        
        print(f"\n  DONE: Downloaded {downloaded} files for {subject_name}")

if __name__ == "__main__":
    main()
