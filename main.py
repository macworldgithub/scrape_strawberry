# """
# Strawberrynet Multi-Category Scraper
# =====================================
# Fetches PAGE 1 ONLY (sort=6 = newest) from each category,
# then fetches quantity for every unique product.

# Categories:
#   skincare, makeup, haircare, perfume, mens-skincare,
#   cologne, home-scents, health, storeberry

# Run locally:
#     pip install playwright requests beautifulsoup4
#     playwright install chromium
#     python strawberrynet_scraper.py

# Output: strawberrynet_newest_products.csv
# """

# import asyncio
# import csv
# import re
# import time
# import requests
# from bs4 import BeautifulSoup
# from playwright.async_api import async_playwright

# # ── Config ───────────────────────────────────────────────────────────────────

# CATEGORIES = [
#     ("skincare",      "https://www.strawberrynet.com/en/skincare?sort=6&page=1"),
#     ("makeup",        "https://www.strawberrynet.com/en/makeup?sort=6&page=1"),
#     ("haircare",      "https://www.strawberrynet.com/en/haircare?sort=6&page=1"),
#     ("perfume",       "https://www.strawberrynet.com/en/perfume?sort=6&page=1"),
#     ("mens-skincare", "https://www.strawberrynet.com/en/mens-skincare?sort=6&page=1"),
#     ("cologne",       "https://www.strawberrynet.com/en/cologne?sort=6&page=1"),
#     ("home-scents",   "https://www.strawberrynet.com/en/home-scents?sort=6&page=1"),
#     ("health",        "https://www.strawberrynet.com/en/health?sort=6&page=1"),
#     ("storeberry",    "https://www.strawberrynet.com/en/storeberry?sort=6&page=1"),
# ]

# QTY_URL     = "https://affiliate.strawberrynet.com/affiliate/cgi/QTYResponse.asp?ProdId={}"
# OUTPUT_FILE = "strawberrynet_newest_products.csv"

# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/122.0.0.0 Safari/537.36"
#     )
# }

# PAGE_LOAD_WAIT = 4000   # ms to wait after networkidle for JS to finish rendering
# QTY_DELAY      = 0.3    # seconds between affiliate API calls
# PAGE_TIMEOUT   = 60000  # ms for Playwright goto


# # ── Quantity fetcher ─────────────────────────────────────────────────────────

# def get_quantity(product_id: str) -> str:
#     """
#     Call the affiliate quantity API and parse <InvQty>VALUE</InvQty>.

#     Example response:
#         <InvQty>3</InvQty>
#     """
#     url = QTY_URL.format(product_id)
#     try:
#         resp = requests.get(url, headers=HEADERS, timeout=10)
#         text = resp.text.strip()

#         # PRIMARY: extract value inside <InvQty>...</InvQty>
#         match = re.search(r"<InvQty>\s*(\d+)\s*</InvQty>", text, re.IGNORECASE)
#         if match:
#             return match.group(1)

#         # FALLBACK: bare integer
#         if text.isdigit():
#             return text

#         print(f"    [QTY unexpected] ProdId={product_id}: {repr(text)}")
#         return "0"

#     except Exception as exc:
#         print(f"    [QTY error] ProdId={product_id}: {exc}")
#         return "error"


# # ── HTML parsers ─────────────────────────────────────────────────────────────

# def extract_product_id(href: str) -> str:
#     """Pull the trailing numeric ID from a product URL."""
#     m = re.search(r"/(\d+)$", href)
#     return m.group(1) if m else ""


# def parse_products(html: str, category: str) -> list:
#     """
#     Parse all product cards from a rendered category page.
#     Injects the category name into every record.
#     """
#     soup = BeautifulSoup(html, "html.parser")
#     products = []

#     for card in soup.select("div.mulltr-a0o6yp"):

#         brand_el    = card.select_one("div.mulltr-8mygwt")
#         name_el     = card.select_one("div.mulltr-10ac8xq")
#         size_el     = card.select_one("div.mulltr-9c7r58")
#         price_el    = card.select_one("div.mulltr-12hvjv6")
#         rrp_el      = card.select_one("div.mulltr-3slrqv")
#         discount_el = card.select_one("div.mulltr-18u8d8r div.text")
#         rating_el   = card.select_one("span.MuiRating-root")
#         link_el     = card.select_one("a.mulltr-96helz")

#         brand    = brand_el.get_text(strip=True)    if brand_el    else ""
#         name     = name_el.get_text(strip=True)     if name_el     else ""
#         size     = size_el.get_text(strip=True)     if size_el     else ""
#         price    = price_el.get_text(strip=True)    if price_el    else ""
#         rrp      = rrp_el.get_text(strip=True).replace("RRP ", "") if rrp_el else ""
#         discount = discount_el.get_text(separator=" ", strip=True) if discount_el else ""

#         rating = ""
#         if rating_el:
#             aria   = rating_el.get("aria-label", "")
#             rating = re.sub(r"\s*[Ss]tars?\s*$", "", aria).strip()

#         href        = link_el.get("href", "") if link_el else ""
#         product_id  = extract_product_id(href)
#         product_url = (
#             f"https://www.strawberrynet.com{href}" if href.startswith("/") else href
#         )

#         if not product_id:
#             continue

#         products.append({
#             "category":    category,
#             "product_id":  product_id,
#             "brand":       brand,
#             "name":        name,
#             "size":        size,
#             "price":       price,
#             "rrp":         rrp,
#             "discount":    discount,
#             "rating":      rating,
#             "product_url": product_url,
#             "quantity":    "",
#         })

#     return products


# # ── Playwright scraper (page 1 per category) ─────────────────────────────────

# async def scrape_categories() -> list:
#     all_products = []

#     async with async_playwright() as pw:
#         browser = await pw.chromium.launch(headless=True)
#         context = await browser.new_context(
#             user_agent=HEADERS["User-Agent"],
#             locale="en-US",
#         )
#         page = await context.new_page()

#         for category, url in CATEGORIES:
#             print(f"\n  [{category}] {url}")
#             try:
#                 await page.goto(url, wait_until="networkidle", timeout=PAGE_TIMEOUT)
#                 await page.wait_for_timeout(PAGE_LOAD_WAIT)

#                 html  = await page.content()
#                 prods = parse_products(html, category)
#                 print(f"  [{category}] → {len(prods)} products found")
#                 all_products.extend(prods)

#             except Exception as exc:
#                 print(f"  [{category}] ERROR: {exc}")

#         await browser.close()

#     return all_products


# # ── Main ─────────────────────────────────────────────────────────────────────

# def main():
#     print("=" * 65)
#     print("  Strawberrynet Multi-Category Scraper")
#     print("  Fetching PAGE 1 (newest, sort=6) for each category")
#     print("=" * 65)

#     # ── Step 1: scrape page 1 of each category ────────────────────────────
#     print("\n[1/2] Scraping category pages …")
#     raw = asyncio.run(scrape_categories())

#     print(f"\n  Total raw products : {len(raw)}")

#     # Deduplicate by product_id (a product may appear in multiple categories)
#     seen     = set()
#     products = []
#     for p in raw:
#         if p["product_id"] not in seen:
#             seen.add(p["product_id"])
#             products.append(p)

#     print(f"  Unique products    : {len(products)}")

#     # Summary per category
#     print("\n  Products per category:")
#     from collections import Counter
#     cat_counts = Counter(p["category"] for p in products)
#     for cat, url in CATEGORIES:
#         print(f"    {cat:<20} {cat_counts.get(cat, 0):>4}")

#     # ── Step 2: fetch quantities ──────────────────────────────────────────
#     print("\n[2/2] Fetching quantities from affiliate API …")
#     for i, prod in enumerate(products, 1):
#         qty = get_quantity(prod["product_id"])
#         prod["quantity"] = qty
#         print(
#             f"  [{i:>4}/{len(products)}] "
#             f"[{prod['category']:<15}] "
#             f"ProdId={prod['product_id']:>7}  qty={qty}"
#         )
#         time.sleep(QTY_DELAY)

#     # ── Step 3: write CSV ─────────────────────────────────────────────────
#     fieldnames = [
#         "category", "product_id", "brand", "name", "size",
#         "price", "rrp", "discount", "rating",
#         "quantity", "product_url",
#     ]
#     with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(products)

#     print(f"\n✓ {len(products)} products saved → {OUTPUT_FILE}")
#     print("=" * 65)


# if __name__ == "__main__":
#     main()
# """
# Strawberrynet Multi-Category Scraper
# =====================================
# Fetches PAGE 1 ONLY (sort=6 = newest) from each category,
# fetches quantity for every unique product,
# then PRINTS the CSV content to stdout.

# Run locally:
#     pip install playwright requests beautifulsoup4
#     playwright install chromium
#     python strawberrynet_scraper.py

#     # or save to file:
#     python strawberrynet_scraper.py > strawberrynet_newest_products.csv
# """

# import asyncio
# import csv
# import io
# import re
# import sys
# import time
# import requests
# from bs4 import BeautifulSoup
# from playwright.async_api import async_playwright

# # ── Config ───────────────────────────────────────────────────────────────────

# CATEGORIES = [
#     ("skincare",      "https://www.strawberrynet.com/en/skincare?sort=6&page=1"),
#     ("makeup",        "https://www.strawberrynet.com/en/makeup?sort=6&page=1"),
#     ("haircare",      "https://www.strawberrynet.com/en/haircare?sort=6&page=1"),
#     ("perfume",       "https://www.strawberrynet.com/en/perfume?sort=6&page=1"),
#     ("mens-skincare", "https://www.strawberrynet.com/en/mens-skincare?sort=6&page=1"),
#     ("cologne",       "https://www.strawberrynet.com/en/cologne?sort=6&page=1"),
#     ("home-scents",   "https://www.strawberrynet.com/en/home-scents?sort=6&page=1"),
#     ("health",        "https://www.strawberrynet.com/en/health?sort=6&page=1"),
#     ("storeberry",    "https://www.strawberrynet.com/en/storeberry?sort=6&page=1"),
# ]

# QTY_URL        = "https://affiliate.strawberrynet.com/affiliate/cgi/QTYResponse.asp?ProdId={}"
# PAGE_LOAD_WAIT = 4000   # ms to wait after networkidle for JS to finish rendering
# QTY_DELAY      = 0.3    # seconds between affiliate API calls
# PAGE_TIMEOUT   = 60000  # ms for Playwright goto

# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/122.0.0.0 Safari/537.36"
#     )
# }

# CSV_FIELDS = [
#     "category", "product_id", "brand", "name", "size",
#     "price", "rrp", "discount", "rating",
#     "quantity", "product_url",
# ]


# # ── Quantity fetcher ─────────────────────────────────────────────────────────

# def get_quantity(product_id: str) -> str:
#     """
#     Call the affiliate quantity API and parse <InvQty>VALUE</InvQty>.

#     Example response:
#         <InvQty>3</InvQty>
#     """
#     url = QTY_URL.format(product_id)
#     try:
#         resp = requests.get(url, headers=HEADERS, timeout=10)
#         text = resp.text.strip()

#         match = re.search(r"<InvQty>\s*(\d+)\s*</InvQty>", text, re.IGNORECASE)
#         if match:
#             return match.group(1)

#         if text.isdigit():
#             return text

#         log(f"  [QTY unexpected] ProdId={product_id}: {repr(text)}")
#         return "0"

#     except Exception as exc:
#         log(f"  [QTY error] ProdId={product_id}: {exc}")
#         return "error"


# # ── HTML parsers ─────────────────────────────────────────────────────────────

# def extract_product_id(href: str) -> str:
#     m = re.search(r"/(\d+)$", href)
#     return m.group(1) if m else ""


# def parse_products(html: str, category: str) -> list:
#     soup = BeautifulSoup(html, "html.parser")
#     products = []

#     for card in soup.select("div.mulltr-a0o6yp"):

#         brand_el    = card.select_one("div.mulltr-8mygwt")
#         name_el     = card.select_one("div.mulltr-10ac8xq")
#         size_el     = card.select_one("div.mulltr-9c7r58")
#         price_el    = card.select_one("div.mulltr-12hvjv6")
#         rrp_el      = card.select_one("div.mulltr-3slrqv")
#         discount_el = card.select_one("div.mulltr-18u8d8r div.text")
#         rating_el   = card.select_one("span.MuiRating-root")
#         link_el     = card.select_one("a.mulltr-96helz")

#         brand    = brand_el.get_text(strip=True)    if brand_el    else ""
#         name     = name_el.get_text(strip=True)     if name_el     else ""
#         size     = size_el.get_text(strip=True)     if size_el     else ""
#         price    = price_el.get_text(strip=True)    if price_el    else ""
#         rrp      = rrp_el.get_text(strip=True).replace("RRP ", "") if rrp_el else ""
#         discount = discount_el.get_text(separator=" ", strip=True) if discount_el else ""

#         rating = ""
#         if rating_el:
#             aria   = rating_el.get("aria-label", "")
#             rating = re.sub(r"\s*[Ss]tars?\s*$", "", aria).strip()

#         href        = link_el.get("href", "") if link_el else ""
#         product_id  = extract_product_id(href)
#         product_url = (
#             f"https://www.strawberrynet.com{href}" if href.startswith("/") else href
#         )

#         if not product_id:
#             continue

#         products.append({
#             "category":    category,
#             "product_id":  product_id,
#             "brand":       brand,
#             "name":        name,
#             "size":        size,
#             "price":       price,
#             "rrp":         rrp,
#             "discount":    discount,
#             "rating":      rating,
#             "product_url": product_url,
#             "quantity":    "",
#         })

#     return products


# # ── Playwright scraper ───────────────────────────────────────────────────────

# async def scrape_categories() -> list:
#     all_products = []

#     async with async_playwright() as pw:
#         browser = await pw.chromium.launch(headless=True)
#         context = await browser.new_context(
#             user_agent=HEADERS["User-Agent"],
#             locale="en-US",
#         )
#         page = await context.new_page()

#         for category, url in CATEGORIES:
#             log(f"  [{category}] Fetching {url}")
#             try:
#                 await page.goto(url, wait_until="networkidle", timeout=PAGE_TIMEOUT)
#                 await page.wait_for_timeout(PAGE_LOAD_WAIT)
#                 html  = await page.content()
#                 prods = parse_products(html, category)
#                 log(f"  [{category}] → {len(prods)} products")
#                 all_products.extend(prods)
#             except Exception as exc:
#                 log(f"  [{category}] ERROR: {exc}")

#         await browser.close()

#     return all_products


# # ── Logging helper (always writes to stderr so stdout stays clean CSV) ────────

# def log(msg: str):
#     print(msg, file=sys.stderr, flush=True)


# # ── Main ─────────────────────────────────────────────────────────────────────

# def main():
#     log("=" * 65)
#     log("  Strawberrynet Multi-Category Scraper")
#     log("  PAGE 1 only, sort=6 (newest) for each category")
#     log("=" * 65)

#     # Step 1 – scrape page 1 of every category
#     log("\n[1/2] Scraping category pages ...")
#     raw = asyncio.run(scrape_categories())
#     log(f"\n  Total raw products : {len(raw)}")

#     # Deduplicate by product_id
#     seen, products = set(), []
#     for p in raw:
#         if p["product_id"] not in seen:
#             seen.add(p["product_id"])
#             products.append(p)
#     log(f"  Unique products    : {len(products)}")

#     # Step 2 – fetch quantities
#     log("\n[2/2] Fetching quantities ...")
#     for i, prod in enumerate(products, 1):
#         qty = get_quantity(prod["product_id"])
#         prod["quantity"] = qty
#         log(
#             f"  [{i:>4}/{len(products)}] "
#             f"[{prod['category']:<15}] "
#             f"ProdId={prod['product_id']:>7}  qty={qty}"
#         )
#         time.sleep(QTY_DELAY)

#     # Step 3 – write CSV to stdout
#     output = io.StringIO()
#     writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
#     writer.writeheader()
#     writer.writerows(products)
#     print(output.getvalue(), end="")

#     log(f"\n✓ Done — {len(products)} products written to stdout as CSV")
#     log("=" * 65)


# if __name__ == "__main__":
#     main()
# import asyncio
# import csv
# import io
# import re
# import threading
# import time
# from contextlib import asynccontextmanager
# from datetime import datetime, timezone

# import requests
# import uvicorn
# from apscheduler.schedulers.background import BackgroundScheduler
# from bs4 import BeautifulSoup
# from fastapi import FastAPI, Response
# from playwright.async_api import async_playwright

# # ── Config ───────────────────────────────────────────────────────────────────

# CATEGORIES = [
#     ("skincare",      "https://www.strawberrynet.com/en/skincare?sort=6&page=1"),
#     ("makeup",        "https://www.strawberrynet.com/en/makeup?sort=6&page=1"),
#     ("haircare",      "https://www.strawberrynet.com/en/haircare?sort=6&page=1"),
#     ("perfume",       "https://www.strawberrynet.com/en/perfume?sort=6&page=1"),
#     ("mens-skincare", "https://www.strawberrynet.com/en/mens-skincare?sort=6&page=1"),
#     ("cologne",       "https://www.strawberrynet.com/en/cologne?sort=6&page=1"),
#     ("home-scents",   "https://www.strawberrynet.com/en/home-scents?sort=6&page=1"),
#     ("health",        "https://www.strawberrynet.com/en/health?sort=6&page=1"),
#     ("storeberry",    "https://www.strawberrynet.com/en/storeberry?sort=6&page=1"),
# ]

# QTY_URL = "https://affiliate.strawberrynet.com/affiliate/cgi/QTYResponse.asp?ProdId={}"
# PAGE_LOAD_WAIT   = 6000   # increased for VPS (slower rendering)
# QTY_DELAY        = 0.4
# PAGE_TIMEOUT     = 90000  # 90s — VPS networks are slower
# SCROLL_PAUSE     = 1500   # ms between scroll steps to trigger lazy-load
# MAX_RETRIES      = 3      # retry each category on failure

# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/122.0.0.0 Safari/537.36"
#     )
# }

# CSV_FIELDS = [
#     "category", "product_id", "brand", "name", "size",
#     "price", "rrp", "discount", "rating",
#     "quantity", "product_url",
# ]

# # ── Shared state ─────────────────────────────────────────────────────────────

# scheduler   = BackgroundScheduler(timezone="UTC")
# state_lock  = threading.Lock()

# latest_csv        = ""
# last_refresh_utc  = None
# last_product_count = 0
# last_error        = None

# def log(msg: str):
#     print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True)

# # ── Quantity fetcher ─────────────────────────────────────────────────────────

# def get_quantity(product_id: str) -> str:
#     url = QTY_URL.format(product_id)
#     try:
#         resp = requests.get(url, headers=HEADERS, timeout=10)
#         text = resp.text.strip()

#         match = re.search(r"<InvQty>\s*(\d+)\s*</InvQty>", text, re.IGNORECASE)
#         if match:
#             return match.group(1)

#         if text.isdigit():
#             return text

#         return "0"
#     except Exception:
#         return "error"

# # ── HTML parsers ─────────────────────────────────────────────────────────────

# def extract_product_id(href: str) -> str:
#     m = re.search(r"/(\d+)$", href)
#     return m.group(1) if m else ""

# def parse_products(html: str, category: str) -> list:
#     soup = BeautifulSoup(html, "html.parser")
#     products = []

#     for card in soup.select("div.mulltr-a0o6yp"):
#         brand_el    = card.select_one("div.mulltr-8mygwt")
#         name_el     = card.select_one("div.mulltr-10ac8xq")
#         size_el     = card.select_one("div.mulltr-9c7r58")
#         price_el    = card.select_one("div.mulltr-12hvjv6")
#         rrp_el      = card.select_one("div.mulltr-3slrqv")
#         discount_el = card.select_one("div.mulltr-18u8d8r div.text")
#         rating_el   = card.select_one("span.MuiRating-root")
#         link_el     = card.select_one("a.mulltr-96helz")

#         brand    = brand_el.get_text(strip=True)    if brand_el    else ""
#         name     = name_el.get_text(strip=True)     if name_el     else ""
#         size     = size_el.get_text(strip=True)     if size_el     else ""
#         price    = price_el.get_text(strip=True)    if price_el    else ""
#         rrp      = rrp_el.get_text(strip=True).replace("RRP ", "") if rrp_el else ""
#         discount = discount_el.get_text(separator=" ", strip=True) if discount_el else ""

#         rating = ""
#         if rating_el:
#             aria   = rating_el.get("aria-label", "")
#             rating = re.sub(r"\s*[Ss]tars?\s*$", "", aria).strip()

#         href       = link_el.get("href", "") if link_el else ""
#         product_id = extract_product_id(href)
#         product_url = (
#             f"https://www.strawberrynet.com{href}" if href.startswith("/") else href
#         )

#         if not product_id:
#             continue

#         products.append({
#             "category":   category,
#             "product_id": product_id,
#             "brand":      brand,
#             "name":       name,
#             "size":       size,
#             "price":      price,
#             "rrp":        rrp,
#             "discount":   discount,
#             "rating":     rating,
#             "quantity":   "",
#             "product_url": product_url,
#         })

#     return products

# # ── Scraper ──────────────────────────────────────────────────────────────────

# async def fetch_category(page, category: str, url: str) -> list:
#     """Fetch one category with retry logic and VPS-safe wait strategy."""
#     for attempt in range(1, MAX_RETRIES + 1):
#         try:
#             log(f"[{category}] attempt {attempt} → {url}")

#             # Use 'domcontentloaded' instead of 'networkidle' — much more
#             # reliable on headless Linux where background XHRs never settle.
#             await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)

#             # Wait for at least one product card to appear in the DOM.
#             # Falls back gracefully if nothing renders.
#             try:
#                 await page.wait_for_selector(
#                     "div.mulltr-a0o6yp",
#                     timeout=PAGE_LOAD_WAIT,
#                     state="attached",
#                 )
#             except Exception:
#                 log(f"[{category}] selector wait timed-out, continuing anyway")

#             # Scroll through the page to trigger any lazy-loaded products.
#             await _scroll_page(page)

#             html   = await page.content()
#             prods  = parse_products(html, category)
#             log(f"[{category}] {len(prods)} products")

#             if prods or attempt == MAX_RETRIES:
#                 return prods

#             log(f"[{category}] 0 products, retrying...")
#             await asyncio.sleep(3)

#         except Exception as exc:
#             log(f"[{category}] attempt {attempt} error: {exc}")
#             if attempt == MAX_RETRIES:
#                 return []
#             await asyncio.sleep(5)

#     return []


# async def _scroll_page(page):
#     """Scroll down gradually so lazy-loaded cards render."""
#     try:
#         viewport_height = await page.evaluate("window.innerHeight")
#         total_height    = await page.evaluate("document.body.scrollHeight")
#         scrolled        = 0
#         step            = max(viewport_height, 600)

#         while scrolled < total_height:
#             scrolled += step
#             await page.evaluate(f"window.scrollTo(0, {scrolled})")
#             await page.wait_for_timeout(SCROLL_PAUSE)
#             total_height = await page.evaluate("document.body.scrollHeight")
#     except Exception:
#         pass  # non-fatal


# async def scrape_categories() -> list:
#     all_products = []

#     async with async_playwright() as pw:
#         browser = await pw.chromium.launch(
#             headless=True,
#             args=[
#                 # ── Critical for Linux/VPS (no kernel sandbox) ──
#                 "--no-sandbox",
#                 "--disable-setuid-sandbox",
#                 # ── Stability & memory on resource-constrained VPS ──
#                 "--disable-dev-shm-usage",       # avoids /dev/shm OOM crashes
#                 "--disable-gpu",                 # no GPU on VPS
#                 "--disable-software-rasterizer",
#                 # ── Reduce unnecessary overhead ──
#                 "--disable-extensions",
#                 "--disable-background-networking",
#                 "--disable-default-apps",
#                 "--no-first-run",
#                 "--disable-translate",
#                 "--mute-audio",
#                 "--disable-notifications",
#             ],
#         )

#         context = await browser.new_context(
#             user_agent=HEADERS["User-Agent"],
#             locale="en-US",
#             # Viewport that matches a typical desktop — affects responsive layout
#             viewport={"width": 1366, "height": 768},
#             # Block images/fonts/media to speed up loads on slow VPS networks
#             java_script_enabled=True,
#         )

#         # Block heavy assets we don't need for scraping
#         await context.route(
#             "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,otf,eot,mp4,mp3}",
#             lambda route, _: route.abort(),
#         )

#         # Reuse ONE page across all categories (avoids re-creating contexts)
#         page = await context.new_page()

#         for category, url in CATEGORIES:
#             prods = await fetch_category(page, category, url)
#             all_products.extend(prods)

#         await browser.close()

#     return all_products


# # ── CSV builder ──────────────────────────────────────────────────────────────

# def build_csv(products: list[dict]) -> str:
#     output = io.StringIO()
#     writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
#     writer.writeheader()
#     writer.writerows(products)
#     return output.getvalue()


# # ── Refresh orchestrator ─────────────────────────────────────────────────────

# def refresh_data():
#     """
#     Run the async scrape from a synchronous context.

#     APScheduler calls this from a worker thread that has NO event loop.
#     We create a fresh loop each time instead of using asyncio.run() to
#     avoid 'no current event loop' errors on Python ≥ 3.10.
#     """
#     global latest_csv, last_refresh_utc, last_product_count, last_error

#     try:
#         log("Starting refresh...")

#         # Safe cross-thread async execution
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         try:
#             raw = loop.run_until_complete(scrape_categories())
#         finally:
#             loop.close()
#             asyncio.set_event_loop(None)

#         # De-duplicate by product_id
#         seen, products = set(), []
#         for p in raw:
#             pid = p["product_id"]
#             if pid not in seen:
#                 seen.add(pid)
#                 products.append(p)

#         log(f"Unique products: {len(products)}")

#         for i, prod in enumerate(products, 1):
#             qty = get_quantity(prod["product_id"])
#             prod["quantity"] = qty
#             log(f"  qty {i}/{len(products)} pid={prod['product_id']} qty={qty}")
#             time.sleep(QTY_DELAY)

#         csv_text = build_csv(products)

#         with state_lock:
#             latest_csv         = csv_text
#             last_refresh_utc   = datetime.now(timezone.utc)
#             last_product_count = len(products)
#             last_error         = None

#         with open("latest_strawberrynet.csv", "w", encoding="utf-8", newline="") as f:
#             f.write(csv_text)

#         log(f"Refresh completed — {len(products)} products written.")

#     except Exception as exc:
#         with state_lock:
#             last_error = str(exc)
#         log(f"Refresh failed: {exc}")


# # ── FastAPI lifespan ─────────────────────────────────────────────────────────

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     scheduler.add_job(
#         refresh_data,
#         trigger="interval",
#         hours=3,
#         id="strawberrynet_refresh",
#         replace_existing=True,
#         max_instances=1,
#         coalesce=True,
#     )
#     scheduler.start()

#     # First scrape on startup — run in a thread so we don't block the event loop
#     await asyncio.to_thread(refresh_data)

#     try:
#         yield
#     finally:
#         scheduler.shutdown(wait=False)


# app = FastAPI(title="Strawberrynet Scraper API", lifespan=lifespan)


# @app.get("/csv")
# def get_csv():
#     with state_lock:
#         if not latest_csv:
#             return Response(
#                 content="CSV not ready yet",
#                 media_type="text/plain",
#                 status_code=503,
#             )
#         return Response(
#             content=latest_csv,
#             media_type="text/csv",
#             headers={"Content-Disposition": 'attachment; filename="latest_strawberrynet.csv"'},
#         )


# @app.get("/status")
# def status():
#     with state_lock:
#         return {
#             "last_refresh_utc": last_refresh_utc.isoformat() if last_refresh_utc else None,
#             "product_count":    last_product_count,
#             "error":            last_error,
#         }


# @app.post("/refresh")
# def manual_refresh():
#     refresh_data()
#     return {"ok": True, "message": "refresh completed"}


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=3020, reload=False)
# import asyncio
# import csv
# import io
# import logging
# import os
# import re
# import threading
# import time
# from contextlib import asynccontextmanager
# from datetime import datetime, timezone

# import requests
# import uvicorn
# from apscheduler.schedulers.background import BackgroundScheduler
# from bs4 import BeautifulSoup
# from fastapi import FastAPI, Response
# from playwright.async_api import async_playwright

# # ── Logging ──────────────────────────────────────────────────────────────────

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     datefmt="%H:%M:%S",
# )
# logger = logging.getLogger(__name__)


# def log(msg: str):
#     logger.info(msg)


# # ── Paths ─────────────────────────────────────────────────────────────────────

# BASE_DIR = "/var/www/scrape_strawberry"
# CSV_FILE = f"latest_strawberrynet.csv"

# os.makedirs(BASE_DIR, exist_ok=True)

# # ── Config ────────────────────────────────────────────────────────────────────

# CATEGORIES = [
#     # ("skincare",      "https://www.strawberrynet.com/en/skincare?sort=6"),
#     # ("makeup",        "https://www.strawberrynet.com/en/makeup?sort=6"),
#     # ("haircare",      "https://www.strawberrynet.com/en/haircare?sort=6"),
#     # ("perfume",       "https://www.strawberrynet.com/en/perfume?sort=6"),
#     ("mens-skincare", "https://www.strawberrynet.com/en/mens-skincare?sort=6"),
#     # ("cologne",       "https://www.strawberrynet.com/en/cologne?sort=6"),
#     # ("home-scents",   "https://www.strawberrynet.com/en/home-scents?sort=6"),
#     # ("health",        "https://www.strawberrynet.com/en/health?sort=6"),
#     # ("storeberry",    "https://www.strawberrynet.com/en/storeberry?sort=6"),
# ]

# QTY_URL        = "https://affiliate.strawberrynet.com/affiliate/cgi/QTYResponse.asp?ProdId={}"
# PAGE_LOAD_WAIT = 6000    # ms — wait for product cards to appear
# QTY_DELAY      = 0.4    # seconds between quantity API calls
# PAGE_TIMEOUT   = 90_000  # ms — navigation timeout
# SCROLL_PAUSE   = 1500    # ms between scroll steps for lazy-load
# MAX_RETRIES    = 3       # per-page retry attempts

# HEADERS = {
#     "User-Agent": (
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/122.0.0.0 Safari/537.36"
#     )
# }

# CSV_FIELDS = [
#     "category", "product_id", "brand", "name", "size",
#     "price", "rrp", "discount", "rating",
#     "quantity", "product_url", "image_url",
# ]

# # ── Shared state ──────────────────────────────────────────────────────────────

# scheduler   = BackgroundScheduler(timezone="UTC")
# state_lock  = threading.Lock()

# latest_csv         = ""
# last_refresh_utc   = None
# last_product_count = 0
# last_error         = None
# is_refreshing      = False   # prevent overlapping manual + scheduled runs

# # ── Quantity fetcher ──────────────────────────────────────────────────────────

# def get_quantity(product_id: str) -> str:
#     url = QTY_URL.format(product_id)
#     for attempt in range(1, 4):
#         try:
#             resp = requests.get(url, headers=HEADERS, timeout=10)
#             text = resp.text.strip()
#             match = re.search(r"<InvQty>\s*(\d+)\s*</InvQty>", text, re.IGNORECASE)
#             if match:
#                 return match.group(1)
#             if text.isdigit():
#                 return text
#             return "0"
#         except requests.RequestException as exc:
#             log(f"  qty pid={product_id} attempt {attempt} error: {exc}")
#             if attempt < 3:
#                 time.sleep(1)
#     return "error"

# # ── HTML parsers ──────────────────────────────────────────────────────────────

# def extract_product_id(href: str) -> str:
#     m = re.search(r"/(\d+)$", href)
#     return m.group(1) if m else ""


# def parse_products(html: str, category: str) -> list:
#     soup = BeautifulSoup(html, "html.parser")
#     products = []

#     for card in soup.select("div.mulltr-a0o6yp"):
#         brand_el    = card.select_one("div.mulltr-8mygwt")
#         name_el     = card.select_one("div.mulltr-10ac8xq")
#         size_el     = card.select_one("div.mulltr-9c7r58")
#         price_el    = card.select_one("div.mulltr-12hvjv6")
#         rrp_el      = card.select_one("div.mulltr-3slrqv")
#         discount_el = card.select_one("div.mulltr-18u8d8r div.text")
#         rating_el   = card.select_one("span.MuiRating-root")
#         link_el     = card.select_one("a.mulltr-96helz")
#         img_el      = card.select_one("img.prodimg")

#         brand    = brand_el.get_text(strip=True)    if brand_el    else ""
#         name     = name_el.get_text(strip=True)     if name_el     else ""
#         size     = size_el.get_text(strip=True)     if size_el     else ""
#         price    = price_el.get_text(strip=True)    if price_el    else ""
#         rrp      = rrp_el.get_text(strip=True).replace("RRP ", "") if rrp_el else ""
#         discount = discount_el.get_text(separator=" ", strip=True) if discount_el else ""

#         rating = ""
#         if rating_el:
#             aria   = rating_el.get("aria-label", "")
#             rating = re.sub(r"\s*[Ss]tars?\s*$", "", aria).strip()

#         href        = link_el.get("href", "") if link_el else ""
#         product_id  = extract_product_id(href)
#         product_url = (
#             f"https://www.strawberrynet.com{href}" if href.startswith("/") else href
#         )

#         # Image URL — src is already an absolute CDN URL (a.cdnsbn.com)
#         image_url = ""
#         if img_el:
#             src = img_el.get("src", "")
#             if src.startswith("http"):
#                 image_url = src
#             elif src.startswith("/"):
#                 image_url = f"https://www.strawberrynet.com{src}"
#             else:
#                 image_url = src

#         if not product_id:
#             continue

#         products.append({
#             "category":    category,
#             "product_id":  product_id,
#             "brand":       brand,
#             "name":        name,
#             "size":        size,
#             "price":       price,
#             "rrp":         rrp,
#             "discount":    discount,
#             "rating":      rating,
#             "quantity":    "",
#             "product_url": product_url,
#             "image_url":   image_url,
#         })

#     return products


# def parse_total_pages(html: str) -> int | None:
#     """
#     Extract total page count from the MUI pagination component.

#     The site renders buttons like:
#         aria-label="Go to page 78"
#     The highest number found is the last page.
#     """
#     soup = BeautifulSoup(html, "html.parser")
#     numbers = []

#     # Primary: aria-label="Go to page N" on pagination buttons
#     for el in soup.select("[aria-label]"):
#         m = re.search(r"[Gg]o to page (\d+)", el.get("aria-label", ""))
#         if m:
#             numbers.append(int(m.group(1)))
#     if numbers:
#         return max(numbers)

#     # Fallback: numbered text inside MUI pagination list items
#     for btn in soup.select("ul.MuiPagination-ul li button"):
#         txt = btn.get_text(strip=True)
#         if txt.isdigit():
#             numbers.append(int(txt))
#     if numbers:
#         return max(numbers)

#     # Last resort: plain text "Page 1 of N"
#     m = re.search(r"[Pp]age\s+\d+\s+of\s+(\d+)", soup.get_text(" "))
#     if m:
#         return int(m.group(1))

#     return None

# # ── Playwright helpers ────────────────────────────────────────────────────────

# async def _scroll_page(page) -> None:
#     """Scroll gradually to trigger lazy-loaded product cards."""
#     try:
#         viewport_height = await page.evaluate("window.innerHeight")
#         total_height    = await page.evaluate("document.body.scrollHeight")
#         scrolled        = 0
#         step            = max(viewport_height, 600)

#         while scrolled < total_height:
#             scrolled += step
#             await page.evaluate(f"window.scrollTo(0, {scrolled})")
#             await page.wait_for_timeout(SCROLL_PAUSE)
#             # Re-read in case new content extended the page
#             total_height = await page.evaluate("document.body.scrollHeight")
#     except Exception:
#         pass  # non-fatal; best-effort scroll


# async def _load_page_html(page, url: str, category: str, page_num: int) -> str | None:
#     """
#     Navigate to `url`, wait for product cards, scroll, and return raw HTML.
#     Returns None on unrecoverable failure.
#     """
#     for attempt in range(1, MAX_RETRIES + 1):
#         try:
#             await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)

#             try:
#                 await page.wait_for_selector(
#                     "div.mulltr-a0o6yp",
#                     timeout=PAGE_LOAD_WAIT,
#                     state="attached",
#                 )
#             except Exception:
#                 log(f"[{category}] p{page_num} selector timeout (attempt {attempt}) — continuing")

#             await _scroll_page(page)
#             return await page.content()

#         except Exception as exc:
#             log(f"[{category}] p{page_num} navigation error (attempt {attempt}): {exc}")
#             if attempt < MAX_RETRIES:
#                 await asyncio.sleep(5)

#     return None  # all retries exhausted

# # ── Category scraper ──────────────────────────────────────────────────────────

# async def scrape_category(page, category: str, base_url: str) -> list:
#     """
#     Scrape all pages for one category.

#     Flow:
#     1. Load page 1 and announce total pages.
#     2. Parse page 1 products from the already-loaded HTML (no extra request).
#     3. Paginate page 2, 3, … stopping when:
#        - An empty page is returned (natural end), OR
#        - All returned product IDs were already seen (site looped back).
#     """
#     # ── Step 1: announce total pages ─────────────────────────────────────
#     first_url  = f"{base_url}&page=1"
#     first_html = await _load_page_html(page, first_url, category, 1)

#     if first_html is None:
#         log(f"[{category}] failed to load page 1 — skipping category")
#         return []

#     total_pages = parse_total_pages(first_html)
#     if total_pages:
#         log(f"[{category}] ── total pages: {total_pages} ──")
#     else:
#         log(f"[{category}] ── total pages: unknown (paginating until empty) ──")

#     # ── Step 2 & 3: paginate ─────────────────────────────────────────────
#     all_products: list = []
#     seen_ids:     set  = set()
#     page_num:     int  = 0

#     while True:
#         page_num += 1
#         url = f"{base_url}&page={page_num}"

#         # Reuse page-1 HTML — no second request needed
#         if page_num == 1:
#             html = first_html
#             log(f"[{category}] page 1 → parsing (reused from total-pages fetch)")
#         else:
#             html = await _load_page_html(page, url, category, page_num)
#             if html is None:
#                 log(f"[{category}] page {page_num} failed after all retries — stopping")
#                 break

#         prods = parse_products(html, category)
#         log(f"[{category}] page {page_num} → {len(prods)} products parsed")

#         if not prods:
#             log(f"[{category}] page {page_num} empty — end of catalogue")
#             break

#         new_prods = [p for p in prods if p["product_id"] not in seen_ids]
#         if not new_prods:
#             log(f"[{category}] page {page_num} all duplicates — site looped back, stopping")
#             break

#         for p in new_prods:
#             seen_ids.add(p["product_id"])

#         all_products.extend(new_prods)
#         log(f"[{category}] running total: {len(all_products)} products (after page {page_num})")

#     fetched_pages = page_num - 1  # last page was empty/duplicate, doesn't count
#     log(f"[{category}] DONE — {len(all_products)} products across {fetched_pages} pages")
#     return all_products

# # ── Browser orchestrator ──────────────────────────────────────────────────────

# async def scrape_all_categories() -> list:
#     all_products = []

#     async with async_playwright() as pw:
#         browser = await pw.chromium.launch(
#             headless=True,
#             args=[
#                 # Required for headless Linux / VPS (no kernel sandbox)
#                 "--no-sandbox",
#                 "--disable-setuid-sandbox",
#                 # Stability on memory-constrained VPS
#                 "--disable-dev-shm-usage",
#                 "--disable-gpu",
#                 "--disable-software-rasterizer",
#                 # Reduce noise & overhead
#                 "--disable-extensions",
#                 "--disable-background-networking",
#                 "--disable-default-apps",
#                 "--disable-sync",
#                 "--no-first-run",
#                 "--disable-translate",
#                 "--mute-audio",
#                 "--disable-notifications",
#                 "--disable-infobars",
#                 "--hide-scrollbars",
#             ],
#         )

#         context = await browser.new_context(
#             user_agent=HEADERS["User-Agent"],
#             locale="en-US",
#             viewport={"width": 1366, "height": 768},
#             java_script_enabled=True,
#             # Ignore HTTPS errors common on restricted VPS networks
#             ignore_https_errors=True,
#         )

#         # Block heavy binary assets to speed up loads.
#         # Images are blocked at the *download* level but their src URLs are
#         # already embedded in the HTML, so image_url capture is unaffected.
#         await context.route(
#             "**/*.{png,jpg,jpeg,gif,webp,svg,ico,"
#             "woff,woff2,ttf,otf,eot,"
#             "mp4,mp3,ogg,wav,webm}",
#             lambda route, _: route.abort(),
#         )

#         # Single page reused across all categories (lighter than new contexts)
#         browser_page = await context.new_page()

#         for category, base_url in CATEGORIES:
#             try:
#                 prods = await scrape_category(browser_page, category, base_url)
#                 all_products.extend(prods)
#             except Exception as exc:
#                 log(f"[{category}] unhandled exception: {exc}")

#         await browser.close()

#     return all_products

# # ── CSV builder ───────────────────────────────────────────────────────────────

# def build_csv(products: list[dict]) -> str:
#     output = io.StringIO()
#     writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore")
#     writer.writeheader()
#     writer.writerows(products)
#     return output.getvalue()

# # ── Refresh orchestrator ──────────────────────────────────────────────────────

# def refresh_data() -> None:
#     """
#     Full scrape + quantity fetch cycle.

#     Safe to call from APScheduler worker threads (no running event loop).
#     Also safe to call from the FastAPI /refresh endpoint via asyncio.to_thread.
#     """
#     global latest_csv, last_refresh_utc, last_product_count, last_error, is_refreshing

#     with state_lock:
#         if is_refreshing:
#             log("Refresh already in progress — skipping")
#             return
#         is_refreshing = True

#     try:
#         log("=" * 60)
#         log("Refresh started")
#         log("=" * 60)

#         # Run async scrape in a fresh event loop (thread-safe)
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#         try:
#             raw = loop.run_until_complete(scrape_all_categories())
#         finally:
#             loop.close()
#             asyncio.set_event_loop(None)

#         # Global dedup by product_id across all categories
#         seen, products = set(), []
#         for p in raw:
#             pid = p["product_id"]
#             if pid not in seen:
#                 seen.add(pid)
#                 products.append(p)

#         log(f"Unique products after dedup: {len(products)}")

#         # Fetch stock quantities
#         log("Fetching quantities...")
#         for i, prod in enumerate(products, 1):
#             qty = get_quantity(prod["product_id"])
#             prod["quantity"] = qty
#             if i % 100 == 0 or i == len(products):
#                 log(f"  qty progress: {i}/{len(products)}")
#             else:
#                 log(f"  qty {i}/{len(products)} pid={prod['product_id']} qty={qty}")
#             time.sleep(QTY_DELAY)

#         csv_text = build_csv(products)

#         # Atomic-ish write: write to temp file then replace
#         tmp_file = CSV_FILE + ".tmp"
#         with open(tmp_file, "w", encoding="utf-8", newline="") as f:
#             f.write(csv_text)
#         os.replace(tmp_file, CSV_FILE)

#         with state_lock:
#             latest_csv         = csv_text
#             last_refresh_utc   = datetime.now(timezone.utc)
#             last_product_count = len(products)
#             last_error         = None

#         log("=" * 60)
#         log(f"Refresh completed — {len(products)} products saved to {CSV_FILE}")
#         log("=" * 60)

#     except Exception as exc:
#         log(f"Refresh FAILED: {exc}")
#         with state_lock:
#             last_error = str(exc)

#     finally:
#         with state_lock:
#             is_refreshing = False


# def _load_csv_from_disk() -> None:
#     """On startup, load any existing CSV from disk so /csv works immediately."""
#     global latest_csv, last_refresh_utc, last_product_count
#     if os.path.exists(CSV_FILE):
#         try:
#             with open(CSV_FILE, "r", encoding="utf-8") as f:
#                 data = f.read()
#             mtime = os.path.getmtime(CSV_FILE)
#             with state_lock:
#                 latest_csv         = data
#                 last_refresh_utc   = datetime.fromtimestamp(mtime, tz=timezone.utc)
#                 last_product_count = max(0, data.count("\n") - 1)
#             log(f"Loaded existing CSV from disk ({last_product_count} products)")
#         except Exception as exc:
#             log(f"Could not load existing CSV: {exc}")

# # ── FastAPI lifespan ──────────────────────────────────────────────────────────

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Serve stale data immediately if a previous CSV exists
#     _load_csv_from_disk()

#     # Schedule automatic refresh every 3 hours
#     scheduler.add_job(
#         refresh_data,
#         trigger="interval",
#         hours=3,
#         id="strawberrynet_refresh",
#         replace_existing=True,
#         max_instances=1,
#         coalesce=True,
#         misfire_grace_time=300,  # allow up to 5 min late execution
#     )
#     scheduler.start()
#     log("Scheduler started (interval: 3 hours)")

#     # Run first scrape in background so startup is non-blocking
#     thread = threading.Thread(target=refresh_data, daemon=True, name="initial-refresh")
#     thread.start()
#     log("Initial refresh started in background thread")

#     try:
#         yield
#     finally:
#         scheduler.shutdown(wait=False)
#         log("Scheduler stopped")


# # ── App ───────────────────────────────────────────────────────────────────────

# app = FastAPI(
#     title="Strawberrynet Scraper API",
#     description="Scrapes all categories from strawberrynet.com and exposes the data as CSV.",
#     version="2.0.0",
#     lifespan=lifespan,
# )


# @app.get("/csv", summary="Download latest product CSV")
# def get_csv():
#     with state_lock:
#         if not latest_csv:
#             return Response(
#                 content="CSV not ready yet — scrape is still running, please try again shortly.",
#                 media_type="text/plain",
#                 status_code=503,
#             )
#         return Response(
#             content=latest_csv,
#             media_type="text/csv",
#             headers={
#                 "Content-Disposition": 'attachment; filename="latest_strawberrynet.csv"',
#                 "X-Product-Count": str(last_product_count),
#             },
#         )


# @app.get("/status", summary="Scraper health and last-run info")
# def get_status():
#     with state_lock:
#         return {
#             "status":           "refreshing" if is_refreshing else "idle",
#             "last_refresh_utc": last_refresh_utc.isoformat() if last_refresh_utc else None,
#             "product_count":    last_product_count,
#             "csv_ready":        bool(latest_csv),
#             "last_error":       last_error,
#         }


# @app.post("/refresh", summary="Trigger a manual scrape")
# async def manual_refresh():
#     with state_lock:
#         if is_refreshing:
#             return {"ok": False, "message": "Refresh already in progress"}
#     # Run in a thread so the HTTP response returns immediately
#     thread = threading.Thread(target=refresh_data, daemon=True, name="manual-refresh")
#     thread.start()
#     return {"ok": True, "message": "Refresh started in background — poll /status for progress"}


# @app.get("/health", summary="Simple liveness probe")
# def health():
#     return {"ok": True}


# # ── Entrypoint ────────────────────────────────────────────────────────────────

# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host="0.0.0.0",
#         port=3020,
#         reload=False,
#         workers=1,           # single worker — scraper holds global state
#         log_level="info",
#         access_log=True,
#     )
import asyncio
import csv
import io
import logging
import os
import re
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import requests
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from bs4 import BeautifulSoup
from fastapi import FastAPI, Response
from playwright.async_api import async_playwright

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def log(msg: str):
    logger.info(msg)


# ── Paths ──────────────────────────────────────────────────────────────────────

BASE_DIR = "/var/www/scrape_strawberry"
CSV_FILE = f"{BASE_DIR}/latest_strawberrynet.csv"

os.makedirs(BASE_DIR, exist_ok=True)

# ── Config ─────────────────────────────────────────────────────────────────────

CATEGORIES = [
    ("skincare",      "https://www.strawberrynet.com/en/skincare?sort=6"),
    ("makeup",        "https://www.strawberrynet.com/en/makeup?sort=6"),
    ("haircare",      "https://www.strawberrynet.com/en/haircare?sort=6"),
    ("perfume",       "https://www.strawberrynet.com/en/perfume?sort=6"),
    ("mens-skincare", "https://www.strawberrynet.com/en/mens-skincare?sort=6"),
    ("cologne",       "https://www.strawberrynet.com/en/cologne?sort=6"),
    ("home-scents",   "https://www.strawberrynet.com/en/home-scents?sort=6"),
    ("health",        "https://www.strawberrynet.com/en/health?sort=6"),
    ("storeberry",    "https://www.strawberrynet.com/en/storeberry?sort=6"),
]

QTY_URL        = "https://affiliate.strawberrynet.com/affiliate/cgi/QTYResponse.asp?ProdId={}"
PAGE_LOAD_WAIT = 8000    # ms — wait for product cards to appear (increased)
QTY_DELAY      = 0.4    # seconds between quantity API calls
PAGE_TIMEOUT   = 90_000  # ms — navigation timeout
SCROLL_PAUSE   = 1500    # ms between scroll steps for lazy-load
MAX_RETRIES    = 3       # per-page retry attempts

# CDN image host used by strawberrynet — used to validate image URLs
CDN_HOST = "a.cdnsbn.com"
PLACEHOLDER_PATTERN = re.compile(r"no.?image|placeholder|icon\.svg", re.IGNORECASE)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

CSV_FIELDS = [
    "category", "product_id", "brand", "name", "size",
    "price", "rrp", "discount", "rating",
    "quantity", "product_url", "image_url",
]

# ── Shared state ───────────────────────────────────────────────────────────────

scheduler   = BackgroundScheduler(timezone="UTC")
state_lock  = threading.Lock()

latest_csv         = ""
last_refresh_utc   = None
last_product_count = 0
last_error         = None
is_refreshing      = False

# ── Quantity fetcher ───────────────────────────────────────────────────────────

def get_quantity(product_id: str) -> str:
    url = QTY_URL.format(product_id)
    for attempt in range(1, 4):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            text = resp.text.strip()
            match = re.search(r"<InvQty>\s*(\d+)\s*</InvQty>", text, re.IGNORECASE)
            if match:
                return match.group(1)
            if text.isdigit():
                return text
            return "0"
        except requests.RequestException as exc:
            log(f"  qty pid={product_id} attempt {attempt} error: {exc}")
            if attempt < 3:
                time.sleep(1)
    return "error"

# ── HTML parsers ───────────────────────────────────────────────────────────────

def extract_product_id(href: str) -> str:
    m = re.search(r"/(\d+)$", href)
    return m.group(1) if m else ""


def extract_image_url(card) -> str:
    """
    Extract the real product image URL from a product card.

    The site uses <img class="prodimg" src="https://a.cdnsbn.com/images/products/...">
    We look for this element and validate the src is a real CDN product image,
    not a placeholder. We do NOT abort image requests in the browser so that
    the src attribute is always fully resolved before we read the HTML.
    """
    # Primary: <img class="prodimg"> — the main product thumbnail
    img = card.select_one("img.prodimg")
    if img:
        src = img.get("src", "").strip()
        if src and CDN_HOST in src and not PLACEHOLDER_PATTERN.search(src):
            return src

    # Fallback 1: any img inside the card whose src points to the products CDN path
    for img in card.select("img[src]"):
        src = img.get("src", "").strip()
        if src and CDN_HOST in src and "/images/products/" in src:
            return src

    # Fallback 2: data-src (some lazy-load implementations)
    for img in card.select("img[data-src]"):
        src = img.get("data-src", "").strip()
        if src and CDN_HOST in src and "/images/products/" in src:
            return src

    return ""


def parse_products(html: str, category: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for card in soup.select("div.mulltr-a0o6yp"):
        brand_el    = card.select_one("div.mulltr-8mygwt")
        name_el     = card.select_one("div.mulltr-10ac8xq")
        size_el     = card.select_one("div.mulltr-9c7r58")
        price_el    = card.select_one("div.mulltr-12hvjv6")
        rrp_el      = card.select_one("div.mulltr-3slrqv")
        discount_el = card.select_one("div.mulltr-18u8d8r div.text")
        rating_el   = card.select_one("span.MuiRating-root")
        link_el     = card.select_one("a.mulltr-96helz")

        brand    = brand_el.get_text(strip=True)    if brand_el    else ""
        name     = name_el.get_text(strip=True)     if name_el     else ""
        size     = size_el.get_text(strip=True)     if size_el     else ""
        price    = price_el.get_text(strip=True)    if price_el    else ""
        rrp      = rrp_el.get_text(strip=True).replace("RRP ", "") if rrp_el else ""
        discount = discount_el.get_text(separator=" ", strip=True) if discount_el else ""

        rating = ""
        if rating_el:
            aria   = rating_el.get("aria-label", "")
            rating = re.sub(r"\s*[Ss]tars?\s*$", "", aria).strip()

        href        = link_el.get("href", "") if link_el else ""
        product_id  = extract_product_id(href)
        product_url = (
            f"https://www.strawberrynet.com{href}" if href.startswith("/") else href
        )

        image_url = extract_image_url(card)

        if not product_id:
            continue

        products.append({
            "category":    category,
            "product_id":  product_id,
            "brand":       brand,
            "name":        name,
            "size":        size,
            "price":       price,
            "rrp":         rrp,
            "discount":    discount,
            "rating":      rating,
            "quantity":    "",
            "product_url": product_url,
            "image_url":   image_url,
        })

    return products


def parse_total_pages(html: str) -> int | None:
    """
    Extract total page count from the MUI pagination component.
    The site renders buttons like: aria-label="Go to page 78"
    The highest number found is the last page.
    """
    soup = BeautifulSoup(html, "html.parser")
    numbers = []

    # Primary: aria-label="Go to page N"
    for el in soup.select("[aria-label]"):
        m = re.search(r"[Gg]o to page (\d+)", el.get("aria-label", ""))
        if m:
            numbers.append(int(m.group(1)))
    if numbers:
        return max(numbers)

    # Fallback: numbered buttons in MUI pagination list
    for btn in soup.select("ul.MuiPagination-ul li button"):
        txt = btn.get_text(strip=True)
        if txt.isdigit():
            numbers.append(int(txt))
    if numbers:
        return max(numbers)

    # Last resort: "Page 1 of N"
    m = re.search(r"[Pp]age\s+\d+\s+of\s+(\d+)", soup.get_text(" "))
    if m:
        return int(m.group(1))

    return None

# ── Playwright helpers ─────────────────────────────────────────────────────────

async def _scroll_page(page) -> None:
    """Scroll gradually to trigger lazy-loaded product cards AND their images."""
    try:
        viewport_height = await page.evaluate("window.innerHeight")
        total_height    = await page.evaluate("document.body.scrollHeight")
        scrolled        = 0
        step            = max(viewport_height, 600)

        while scrolled < total_height:
            scrolled += step
            await page.evaluate(f"window.scrollTo(0, {scrolled})")
            await page.wait_for_timeout(SCROLL_PAUSE)
            total_height = await page.evaluate("document.body.scrollHeight")

        # Scroll back to top then wait — ensures all lazy images have loaded
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(1000)
    except Exception:
        pass


async def _wait_for_images(page, category: str, page_num: int) -> None:
    """
    Wait until product images have their real src set (not placeholder/empty).
    Times out gracefully after 8 seconds.
    """
    try:
        await page.wait_for_function(
            """() => {
                const imgs = document.querySelectorAll('img.prodimg');
                if (imgs.length === 0) return true;
                let loaded = 0;
                for (const img of imgs) {
                    const src = img.getAttribute('src') || '';
                    if (src.includes('/images/products/')) loaded++;
                }
                return loaded > 0;
            }""",
            timeout=8000,
        )
    except Exception:
        log(f"[{category}] p{page_num} image wait timed out — continuing anyway")


async def _load_page_html(page, url: str, category: str, page_num: int) -> str | None:
    """
    Navigate, wait for product cards, scroll to trigger lazy-load,
    wait for images to resolve, then return raw HTML.
    Returns None on unrecoverable failure.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)

            # Wait for product cards
            try:
                await page.wait_for_selector(
                    "div.mulltr-a0o6yp",
                    timeout=PAGE_LOAD_WAIT,
                    state="attached",
                )
            except Exception:
                log(f"[{category}] p{page_num} selector timeout (attempt {attempt})")

            # Scroll so lazy-loaded images fire their requests
            await _scroll_page(page)

            # Wait for real product image srcs to appear in the DOM
            await _wait_for_images(page, category, page_num)

            html = await page.content()

            # Quick sanity-check: did we get real image URLs?
            if CDN_HOST in html and "/images/products/" in html:
                return html

            log(f"[{category}] p{page_num} attempt {attempt} — no product image URLs in HTML, retrying")
            await asyncio.sleep(3)

        except Exception as exc:
            log(f"[{category}] p{page_num} navigation error (attempt {attempt}): {exc}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(5)

    return None

# ── Category scraper ───────────────────────────────────────────────────────────

async def scrape_category(page, category: str, base_url: str) -> list:
    """
    Scrape all pages for one category.

    1. Load page 1 and announce total pages.
    2. Parse page 1 products from the already-loaded HTML (no extra request).
    3. Paginate page 2, 3, … stopping when:
       - An empty page is returned (natural end), OR
       - All returned product IDs were already seen (site looped back).
    """
    first_url  = f"{base_url}&page=1"
    first_html = await _load_page_html(page, first_url, category, 1)

    if first_html is None:
        log(f"[{category}] failed to load page 1 — skipping category")
        return []

    total_pages = parse_total_pages(first_html)
    if total_pages:
        log(f"[{category}] ── total pages: {total_pages} ──")
    else:
        log(f"[{category}] ── total pages: unknown (paginating until empty) ──")

    all_products: list = []
    seen_ids:     set  = set()
    page_num:     int  = 0

    while True:
        page_num += 1
        url = f"{base_url}&page={page_num}"

        if page_num == 1:
            html = first_html
            log(f"[{category}] page 1 → parsing (reused from total-pages fetch)")
        else:
            html = await _load_page_html(page, url, category, page_num)
            if html is None:
                log(f"[{category}] page {page_num} failed after all retries — stopping")
                break

        prods = parse_products(html, category)
        log(f"[{category}] page {page_num} → {len(prods)} products parsed")

        if not prods:
            log(f"[{category}] page {page_num} empty — end of catalogue")
            break

        new_prods = [p for p in prods if p["product_id"] not in seen_ids]
        if not new_prods:
            log(f"[{category}] page {page_num} all duplicates — site looped, stopping")
            break

        # Log image URL quality for the first product of each page (debug aid)
        sample = new_prods[0]
        log(f"[{category}] page {page_num} sample image_url: {sample['image_url'] or '(EMPTY)'}")

        for p in new_prods:
            seen_ids.add(p["product_id"])

        all_products.extend(new_prods)
        log(f"[{category}] running total: {len(all_products)} products (after page {page_num})")

    fetched = page_num - 1
    log(f"[{category}] DONE — {len(all_products)} products across {fetched} pages")
    return all_products

# ── Browser orchestrator ───────────────────────────────────────────────────────

async def scrape_all_categories() -> list:
    all_products = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                # Required for headless Linux / VPS (no kernel sandbox)
                "--no-sandbox",
                "--disable-setuid-sandbox",
                # Stability on memory-constrained VPS
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                # Reduce noise & overhead
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
                "--no-first-run",
                "--disable-translate",
                "--mute-audio",
                "--disable-notifications",
                "--disable-infobars",
                "--hide-scrollbars",
            ],
        )

        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="en-US",
            viewport={"width": 1366, "height": 768},
            java_script_enabled=True,
            ignore_https_errors=True,
        )

        # ── IMPORTANT: Do NOT block image requests ────────────────────────
        # Blocking images prevents <img src> from being set in the DOM,
        # causing placeholder URLs to appear instead of real product images.
        # We only block heavyweight non-image binary assets that waste bandwidth.
        await context.route(
            "**/*.{woff,woff2,ttf,otf,eot,mp4,mp3,ogg,wav,webm}",
            lambda route, _: route.abort(),
        )

        # Single reusable page across all categories
        browser_page = await context.new_page()

        for category, base_url in CATEGORIES:
            try:
                prods = await scrape_category(browser_page, category, base_url)
                all_products.extend(prods)
            except Exception as exc:
                log(f"[{category}] unhandled exception: {exc}")

        await browser.close()

    return all_products

# ── CSV builder ────────────────────────────────────────────────────────────────

def build_csv(products: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(products)
    return output.getvalue()

# ── Refresh orchestrator ───────────────────────────────────────────────────────

def refresh_data() -> None:
    global latest_csv, last_refresh_utc, last_product_count, last_error, is_refreshing

    with state_lock:
        if is_refreshing:
            log("Refresh already in progress — skipping")
            return
        is_refreshing = True

    try:
        log("=" * 60)
        log("Refresh started")
        log("=" * 60)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            raw = loop.run_until_complete(scrape_all_categories())
        finally:
            loop.close()
            asyncio.set_event_loop(None)

        # Global dedup by product_id across all categories
        seen, products = set(), []
        for p in raw:
            pid = p["product_id"]
            if pid not in seen:
                seen.add(pid)
                products.append(p)

        log(f"Unique products after dedup: {len(products)}")

        # Stats: how many have real image URLs vs empty
        with_img    = sum(1 for p in products if p.get("image_url"))
        without_img = len(products) - with_img
        log(f"Image URL coverage: {with_img}/{len(products)} ({without_img} missing)")

        log("Fetching quantities...")
        for i, prod in enumerate(products, 1):
            qty = get_quantity(prod["product_id"])
            prod["quantity"] = qty
            if i % 100 == 0 or i == len(products):
                log(f"  qty progress: {i}/{len(products)}")
            else:
                log(f"  qty {i}/{len(products)} pid={prod['product_id']} qty={qty}")
            time.sleep(QTY_DELAY)

        csv_text = build_csv(products)

        # Atomic write: temp file → replace
        tmp_file = CSV_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8", newline="") as f:
            f.write(csv_text)
        os.replace(tmp_file, CSV_FILE)

        with state_lock:
            latest_csv         = csv_text
            last_refresh_utc   = datetime.now(timezone.utc)
            last_product_count = len(products)
            last_error         = None

        log("=" * 60)
        log(f"Refresh completed — {len(products)} products saved to {CSV_FILE}")
        log("=" * 60)

    except Exception as exc:
        log(f"Refresh FAILED: {exc}")
        with state_lock:
            last_error = str(exc)

    finally:
        with state_lock:
            is_refreshing = False


def _load_csv_from_disk() -> None:
    """On startup, load any existing CSV so /csv works immediately."""
    global latest_csv, last_refresh_utc, last_product_count
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, "r", encoding="utf-8") as f:
                data = f.read()
            mtime = os.path.getmtime(CSV_FILE)
            with state_lock:
                latest_csv         = data
                last_refresh_utc   = datetime.fromtimestamp(mtime, tz=timezone.utc)
                last_product_count = max(0, data.count("\n") - 1)
            log(f"Loaded existing CSV from disk ({last_product_count} products)")
        except Exception as exc:
            log(f"Could not load existing CSV: {exc}")

# ── FastAPI lifespan ───────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_csv_from_disk()

    scheduler.add_job(
        refresh_data,
        trigger="interval",
        hours=3,
        id="strawberrynet_refresh",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    log("Scheduler started (interval: 3 hours)")

    thread = threading.Thread(target=refresh_data, daemon=True, name="initial-refresh")
    thread.start()
    log("Initial refresh started in background thread")

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        log("Scheduler stopped")


# ── App ────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Strawberrynet Scraper API",
    description="Scrapes all categories from strawberrynet.com and exposes data as CSV.",
    version="2.1.0",
    lifespan=lifespan,
)


@app.get("/csv", summary="Download latest product CSV")
def get_csv():
    with state_lock:
        if not latest_csv:
            return Response(
                content="CSV not ready yet — scrape is still running, please try again shortly.",
                media_type="text/plain",
                status_code=503,
            )
        return Response(
            content=latest_csv,
            media_type="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="latest_strawberrynet.csv"',
                "X-Product-Count": str(last_product_count),
            },
        )


@app.get("/status", summary="Scraper health and last-run info")
def get_status():
    with state_lock:
        return {
            "status":           "refreshing" if is_refreshing else "idle",
            "last_refresh_utc": last_refresh_utc.isoformat() if last_refresh_utc else None,
            "product_count":    last_product_count,
            "csv_ready":        bool(latest_csv),
            "last_error":       last_error,
        }


@app.post("/refresh", summary="Trigger a manual scrape")
async def manual_refresh():
    with state_lock:
        if is_refreshing:
            return {"ok": False, "message": "Refresh already in progress"}
    thread = threading.Thread(target=refresh_data, daemon=True, name="manual-refresh")
    thread.start()
    return {"ok": True, "message": "Refresh started in background — poll /status for progress"}


@app.get("/health", summary="Liveness probe")
def health():
    return {"ok": True}


# ── Entrypoint ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3020,
        reload=False,
        workers=1,
        log_level="info",
        access_log=True,
    )