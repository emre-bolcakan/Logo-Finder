import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

def is_valid(url, base_domain):
    parsed = urlparse(url)
    return parsed.netloc.endswith(base_domain)

def find_logo_url_on_page(soup, base_url, logo_identifier="logo"):
    logo_identifier = logo_identifier.lower()
    for img in soup.find_all('img', src=True):
        alt = img.get('alt', '').lower()
        cls = ' '.join(img.get('class', [])).lower()
        id_ = img.get('id', '').lower()
        src = img['src']

        if (logo_identifier in alt) or (logo_identifier in cls) or (logo_identifier in id_):
            return urljoin(base_url, src)
    return None

def page_contains_logo(soup, logo_url, base_url):
    for img in soup.find_all('img', src=True):
        src = urljoin(base_url, img['src'])
        if src == logo_url:
            return True
    return False

def crawl_find_logo_pages(base_url, max_pages=20, logo_identifier="logo"):
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    visited = set()
    to_visit = [base_url]
    pages_with_logo = []

    # Step 1: Get logo URL on base page
    try:
        resp = requests.get(base_url)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch base URL {base_url}: {e}")
        return pages_with_logo

    soup = BeautifulSoup(resp.content, 'html.parser')
    logo_url = find_logo_url_on_page(soup, base_url, logo_identifier)
    if not logo_url:
        print(f"Logo not found on base page using identifier '{logo_identifier}'.")
        return pages_with_logo

    print(f"Discovered logo URL: {logo_url}")

    # Step 2: Crawl pages to find logo presence
    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        print(f"Crawling: {url}")
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            visited.add(url)
            continue

        soup = BeautifulSoup(resp.content, 'html.parser')
        if page_contains_logo(soup, logo_url, url):
            pages_with_logo.append((url, logo_url))

        # Find new links within domain
        for a_tag in soup.find_all('a', href=True):
            link = urljoin(url, a_tag['href'])
            if is_valid(link, base_domain) and link not in visited and link not in to_visit:
                to_visit.append(link)

        visited.add(url)
        time.sleep(1)  # polite delay

    return pages_with_logo

if __name__ == "__main__":
    base_url = input("Enter the base URL to crawl (e.g., https://www.google.com/): ").strip()
    logo_identifier = input("Enter the logo identifier keyword (optional, default='logo'): ").strip()
    if not logo_identifier:
        logo_identifier = "logo"

    results = crawl_find_logo_pages(base_url, max_pages=20, logo_identifier=logo_identifier)
    print("\nPages containing the logo:")
    for page_url, logo in results:
        print(f"- Page: {page_url}")
        print(f"  Logo URL: {logo}\n")
