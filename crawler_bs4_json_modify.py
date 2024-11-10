import os
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
output_folder = domain  # Use domain name as folder name
os.makedirs(output_folder, exist_ok=True)

def get_page_content(url):
    """Fetch page content and extract title, headings, and paragraphs."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        if "text/html" in response.headers["Content-Type"]:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract title, headings, and paragraphs
            title = soup.title.string if soup.title else "No Title"
            headings = {f"h{level}": [sanitize_text(h.get_text(strip=True)) for h in soup.find_all(f"h{level}")]
                        for level in range(1, 4)}
            paragraphs = [sanitize_text(p.get_text(strip=True)) for p in soup.find_all("p")]
            
            return {"title": title, "headings": headings, "paragraphs": paragraphs}, response.text
        return None, None
    except requests.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")
        return None, None

def sanitize_text(text):
    """Sanitize text by removing unusual line terminators and replacing newlines within text."""
    return text.replace("\u2028", " ").replace("\u2029", " ").replace("\n", " ")

def extract_links(content, base_url):
    """Extract and return absolute URLs within the same domain."""
    soup = BeautifulSoup(content, "html.parser")
    links = {urljoin(base_url, a["href"]) for a in soup.find_all("a", href=True)
             if urlparse(urljoin(base_url, a["href"])).netloc == domain}
    return links

def sanitize_filename(url):
    """Convert a URL to a safe filename by removing/replacing invalid characters."""
    path = urlparse(url).path.replace("/", "_").strip("_")
    return f"{domain}_{path}.json"

def clean_line_terminators(filepath):
    """Remove unusual line terminators from a JSON file."""
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Replace unusual line terminators with standard ones
    content = content.replace("\u2028", "\n").replace("\u2029", "\n")

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(content)

def crawl(start_url, max_depth=2, max_pages=5):
    """Crawl a website starting from the given URL, respecting max depth and max pages."""
    queue = deque([(start_url, 0)])
    visited = set()
    page_count = 0

    while queue and page_count < max_pages:
        current_url, depth = queue.popleft()
        if depth > max_depth:
            continue

        # Generate the filename and check if the file already exists
        filename = sanitize_filename(current_url)
        filepath = os.path.join(output_folder, filename)
        
        if current_url in visited:
            continue  # Skip if the URL has already been visited

        # If the file already exists, skip saving but still extract links
        if os.path.exists(filepath):
            print(f"Skipping {current_url} - already crawled and saved.")
            content_data, html_content = None, None  # Set to None to avoid saving
        else:
            print(f"Crawling: {current_url} at depth {depth}")
            
            # Get structured page content and raw HTML content for link extraction
            content_data, html_content = get_page_content(current_url)
            
            if content_data:
                # Save structured data to a JSON file
                content_data["url"] = current_url
                content_data["timestamp"] = datetime.now().isoformat()

                with open(filepath, "w", encoding="utf-8") as file:
                    json.dump(content_data, file, ensure_ascii=False, indent=4)
                
                # Clean unusual line terminators in the saved JSON file
                clean_line_terminators(filepath)

                page_count += 1

        # Mark as visited after processing the current URL
        visited.add(current_url)

        # Extract and add new links to the queue if within depth limit and html_content is available
        if depth < max_depth:
            if html_content is None:
                _, html_content = get_page_content(current_url)  # Retrieve HTML content if skipped for saving
            if html_content:
                links = extract_links(html_content, current_url)
                for link in links:
                    if link not in visited:
                        queue.append((link, depth + 1))

    print(f"Crawling complete. {page_count} pages crawled.")

# Start crawling with the desired depth and page limit
crawl(start_url, max_depth=2, max_pages=20)
