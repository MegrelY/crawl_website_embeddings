import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, urljoin
from collections import deque

# Set the domain and start URL
domain = "peterattiamd.com"  # Replace with your target domain
start_url = "https://peterattiamd.com/about/"  # Starting URL

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run headless (without opening a browser window)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize the WebDriver (Replace 'driver_path' with your driver path)
driver_path = r"D:\Coding\crawl_website_embeddings\chromedriver-win64\chromedriver.exe"  # Update this path
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

def get_page_content(url):
    """Fetch page content and hyperlinks using Selenium."""
    driver.get(url)
    
    # Wait for at least one link to be present (up to 10 seconds)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )
    except Exception as e:
        print(f"No links found on {url}: {e}")

    return driver.page_source

def extract_links(content, base_url):
    """Extract and return absolute URLs within the same domain using Selenium."""
    links = set()
    elements = driver.find_elements(By.TAG_NAME, "a")  # Find all <a> tags

    for elem in elements:
        href = elem.get_attribute("href")
        if href:
            href = urljoin(base_url, href)
            if urlparse(href).netloc == domain:
                links.add(href)
    print(f"Total links found on {base_url}: {len(links)}")  # Debug: show count of links
    return links

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
        content = get_page_content(current_url)
        if content:
            filename = current_url.replace("https://", "").replace("http://", "").replace("/", "_") + ".txt"
            with open(os.path.join("crawled_content", filename), "w", encoding="utf-8") as file:
                file.write(content)
            page_count += 1

            # Add new links to the queue, if within depth
            if depth < max_depth:
                for link in extract_links(content, current_url):
                    if link not in visited:
                        visited.add(link)
                        queue.append((link, depth + 1))

    print(f"Crawling complete. {page_count} pages crawled.")
    driver.quit()  # Close the browser after crawling

# Start crawling with the desired depth and page limit
crawl(start_url, max_depth=2, max_pages=5)
