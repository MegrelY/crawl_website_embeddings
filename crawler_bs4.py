import os
import re
import requests
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlparse, urljoin

# Define the domain and starting URL
domain = "peterattiamd.com"  # Replace with your target domain
start_url = "https://peterattiamd.com/about/"  # Starting URL

def get_page_content(url):
    """Fetch page content and extract visible text using BeautifulSoup."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        if "text/html" in response.headers["Content-Type"]:
            soup = BeautifulSoup(response.text, "html.parser")
            # Extract and return only visible text
            text = soup.get_text(separator="\n", strip=True)
            return text, response.text  # Return both plain text and HTML
        return None, None
    except requests.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")
        return None, None

def extract_links(content, base_url):
    """Extract and return absolute URLs within the same domain."""
    soup = BeautifulSoup(content, "html.parser")
    links = set()
    for a_tag in soup.find_all("a", href=True):
        href = urljoin(base_url, a_tag["href"])
        if urlparse(href).netloc == domain:
            links.add(href)
    return links

def sanitize_filename(url):
    """Convert a URL to a safe filename by removing/replacing invalid characters."""
    filename = url.replace("https://", "").replace("http://", "")
    filename = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)  # Replace invalid characters with '_'
    return filename + ".txt"

def crawl(url, max_depth=2, max_pages=50):
    """
    Crawl a website starting from the given URL, respecting max depth and max pages.
    - max_depth: Maximum depth to follow links (0 for root page only).
    - max_pages: Maximum number of pages to visit in total.
    """
    local_domain = urlparse(url).netloc
    queue = deque([(url, 0)])  # Queue holds (URL, depth)
    visited = set([url])
    page_count = 0  # Counter for the number of pages crawled

    # Directory setup for storing content
    if not os.path.exists("crawled_content"):
        os.mkdir("crawled_content")

    while queue and page_count < max_pages:
        current_url, depth = queue.popleft()
        if depth > max_depth:
            continue

        print(f"Crawling: {current_url} at depth {depth}")
        text_content, html_content = get_page_content(current_url)
        if text_content:
            filename = sanitize_filename(current_url)
            filepath = os.path.join("crawled_content", filename)
            with open(filepath, "w", encoding="utf-8") as file:
                file.write(text_content)
            page_count += 1

            # Add new links to the queue, if within depth
            if depth < max_depth and html_content:
                links = extract_links(html_content, current_url)
                for link in links:
                    if link not in visited:
                        visited.add(link)
                        queue.append((link, depth + 1))

    print(f"Crawling complete. {page_count} pages crawled.")

# Start crawling with the desired depth and page limit
crawl(start_url, max_depth=2, max_pages=5)
