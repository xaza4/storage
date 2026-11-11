# This is AI assisted code.

import os
import sys
import time
import logging
from urllib.parse import urlparse, urljoin, unquote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser
from pathlib import Path

class AssetHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.extracted_links = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag in ("a", "link"):
            href = attrs_dict.get("href")
            if href:
                self.extracted_links.append(href)

        elif tag in ("script", "img", "iframe", "source"):
            src = attrs_dict.get("src")
            if src:
                self.extracted_links.append(src)
            elif tag == "source":
                srcset = attrs_dict.get("srcset")
                if srcset:
                    first_src = srcset.split(",")[0].strip().split(" ")[0]
                    self.extracted_links.append(first_src)

def setup_logger(output_dir):
    log_path = os.path.join(output_dir, "log.txt")
    os.makedirs(output_dir, exist_ok=True)

    logger = logging.getLogger("EntiretyScraper")
    logger.setLevel(logging.INFO)

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.INFO)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

def get_local_path(domain, url, output_dir):
    parsed_url = urlparse(url)
    path = parsed_url.path
    path = unquote(path)

    if path == "" or path.endswith("/"):
        path = path + "index.html"
    elif not Path(path).suffix:
        path = path + "/index.html"

    if path.startswith("/"):
        path = path[1:]

    return Path(output_dir) / path

def scrape_site(start_url):
    parsed_start = urlparse(start_url)
    domain = parsed_start.netloc

    output_dir = domain.replace(":", "_")
    os.makedirs(output_dir, exist_ok=True)

    logger = setup_logger(output_dir)
    logger.info(f"Starting complete entirety crawl for domain: {domain} (Root URL: {start_url})")

    visited = set()
    queue = [start_url]
    visited.add(start_url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    downloaded_files = 0
    failed_files = 0

    while queue:
        current_url = queue.pop(0)
        logger.info(f"Crawling: {current_url}")

        try:
            req = Request(current_url, headers=headers)
            with urlopen(req, timeout=15) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                content = response.read()

            local_path = get_local_path(domain, current_url, output_dir)
            local_path.parent.mkdir(parents=True, exist_ok=True)

            with open(local_path, "wb") as f:
                f.write(content)

            downloaded_files += 1
            logger.info(f"Saved: {current_url} -> {local_path}")

            if "text/html" in content_type:
                html_text = content.decode("utf-8", errors="ignore")
                parser = AssetHTMLParser()
                parser.feed(html_text)

                for link in parser.extracted_links:
                    absolute_url = urljoin(current_url, link)
                    parsed_abs = urlparse(absolute_url)
                    clean_url = parsed_abs._replace(fragment="").geturl()

                    if parsed_abs.netloc == domain or parsed_abs.netloc == "":
                        if clean_url not in visited:
                            visited.add(clean_url)
                            queue.append(clean_url)

        except (HTTPError, URLError, Exception) as e:
            failed_files += 1
            logger.error(f"Failed to process {current_url}: {str(e)}")

        time.sleep(0.05)

    logger.info(f"Entirety crawl complete! Total files saved: {downloaded_files}, Errors: {failed_files}")
    logger.info(f"Mirrored site and log.txt stored in directory: {os.path.abspath(output_dir)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        print("Vibed Web Scrapin")
        target_url = input("Enter target domain or full URL (e.g., example.com): ").strip()

    if not target_url:
        print("Error: No URL provided. Exiting.")
        sys.exit(1)

    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url

    scrape_site(target_url)
