import os
import re
import json
import requests
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlparse, urljoin
from datetime import datetime

# Define the domain and starting URL
domain = "peterattiamd.com"  # Replace with your target domain
start_url = "https://peterattiamd.com/about/"  # Starting URL

# Directory setup for storing JSON content
output_folder = "crawled_json"
if not os.path.exists(output_folder):
    os.mkdir(output_folder)

def get_page_content(url):
    """Fetch page content and extract structured data."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        if "text/html" in response.headers["Content-Type"]:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract title
            title = soup.title.string if soup.title else "No Title"
            
            # Extract headings
            headings = {
                "h1": [h.get_text(strip=True) for h in soup.find_all("h1")],
                "h2": [h.get_text(strip=True) for h in soup.find_all("h2")],
                "h3": [h.get_text(strip=True) for h in soup.find_all("h3")]
            }
            
            # Extract paragraphs
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]

            # Extract lists
            lists = {
                "unordered": [li.get_text(strip=True) for ul in soup.find_all("ul") for li in ul.find_all("li")],
                "ordered": [li.get_text(strip=True) for ol in soup.find_all("ol") for li in ol.find_all("li")]
            }

            # Extract links
            links = [a["href"] for a in soup.find_all("a", href=True)]
            
            # Collect tables if needed
            tables = []
            for table in soup.find_all("table"):
                table_data = []
                for row in table.find_all("tr"):
                    row_data = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
                    table_data.append(row_data)
                tables.append(table_data)

            # Structured content as dictionary and full HTML content
            content_data = {
                "title": title,
                "headings": headings,
                "paragraphs": paragraphs,
                "lists": lists,
                "links": links,
                "tables": tables
            }
            return content_data, response.text  # Only two values returned
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
        # Ensure link is within the same domain
        if urlparse(href).netloc == domain and href not in links:
            links.add(href)
    return links

def sanitize_filename(url):
    """Convert a URL to a safe filename by removing/replacing invalid characters."""
    parsed_url = urlparse(url)
    path = parsed_url.path.replace("/", "_").strip("_")
    domain = parsed_url.netloc
    return f"{domain}_{path}.json"

def clean_text(text):
    """Remove duplicated lines, normalize text encoding, and optionally remove newlines."""
    lines = text.splitlines()
    unique_lines = list(dict.fromkeys(lines))  # Remove duplicates
    cleaned_text = " ".join(unique_lines)  # Join with spaces instead of newlines
    return cleaned_text.encode("utf-8", "ignore").decode("utf-8")  # Normalize encoding


import os
import json
from collections import deque
from urllib.parse import urlparse
from datetime import datetime

def crawl(start_url, max_depth=2, max_pages=5):
    """
    Crawl a website starting from the given URL, respecting max depth and max pages.
    - max_depth: Maximum depth to follow links (0 for root page only).
    - max_pages: Maximum number of pages to visit in total.
    """
    domain = urlparse(start_url).netloc
    queue = deque([(start_url, 0)])  # Queue holds (URL, depth)
    visited = set([start_url])
    page_count = 0  # Counter for the number of pages crawled

    # Directory setup for storing JSON content
    output_folder = "crawled_json"
    if not os.path.exists(output_folder):
        os.mkdir(output_folder)

    while queue and page_count < max_pages:
        current_url, depth = queue.popleft()
        if depth > max_depth:
            continue

        print(f"Crawling: {current_url} at depth {depth}")
        
        # Get structured page content and raw HTML content for link extraction
        content_data, html_content = get_page_content(current_url)
        
        # Check if page content was successfully retrieved
        if content_data:
            # Prepare data for JSON
            data = {
                "timestamp": datetime.now().isoformat(),
                "url": current_url,
                "title": content_data["title"],
                "headings": content_data["headings"],
                "paragraphs": content_data["paragraphs"],
                "lists": content_data["lists"],
                "links": content_data["links"],
                "tables": content_data["tables"]
            }

            # Generate a filename based on the domain and URL path
            filename = sanitize_filename(current_url)
            filepath = os.path.join(output_folder, filename)

            # Save structured data to a JSON file
            with open(filepath, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

            page_count += 1

            # Extract and add new links to the queue if within depth limit
            if depth < max_depth:
                links = extract_links(html_content, current_url)
                for link in links:
                    if link not in visited:
                        visited.add(link)
                        queue.append((link, depth + 1))

    print(f"Crawling complete. {page_count} pages crawled.")

# Helper function to create a safe filename based on URL
def sanitize_filename(url):
    """Convert a URL to a safe filename by removing/replacing invalid characters."""
    parsed_url = urlparse(url)
    path = parsed_url.path.replace("/", "_").strip("_")
    domain = parsed_url.netloc
    return f"{domain}_{path}.json"


# Start crawling with the desired depth and page limit
crawl(start_url, max_depth=2, max_pages=20)
