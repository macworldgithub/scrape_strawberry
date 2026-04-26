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
import asyncio
import csv
import io
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

# ── Config ───────────────────────────────────────────────────────────────────

CATEGORIES = [
    ("skincare",      "https://www.strawberrynet.com/en/skincare?sort=6&page=1"),
    ("makeup",        "https://www.strawberrynet.com/en/makeup?sort=6&page=1"),
    ("haircare",      "https://www.strawberrynet.com/en/haircare?sort=6&page=1"),
    ("perfume",       "https://www.strawberrynet.com/en/perfume?sort=6&page=1"),
    ("mens-skincare", "https://www.strawberrynet.com/en/mens-skincare?sort=6&page=1"),
    ("cologne",       "https://www.strawberrynet.com/en/cologne?sort=6&page=1"),
    ("home-scents",   "https://www.strawberrynet.com/en/home-scents?sort=6&page=1"),
    ("health",        "https://www.strawberrynet.com/en/health?sort=6&page=1"),
    ("storeberry",    "https://www.strawberrynet.com/en/storeberry?sort=6&page=1"),
]

QTY_URL = "https://affiliate.strawberrynet.com/affiliate/cgi/QTYResponse.asp?ProdId={}"
PAGE_LOAD_WAIT = 4000
QTY_DELAY = 0.3
PAGE_TIMEOUT = 60000

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
    "quantity", "product_url",
]

# ── Shared state ─────────────────────────────────────────────────────────────

scheduler = BackgroundScheduler(timezone="UTC")
state_lock = threading.Lock()

latest_csv = ""
last_refresh_utc = None
last_product_count = 0
last_error = None

def log(msg: str):
    print(msg, flush=True)

# ── Quantity fetcher ─────────────────────────────────────────────────────────

def get_quantity(product_id: str) -> str:
    url = QTY_URL.format(product_id)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        text = resp.text.strip()

        match = re.search(r"<InvQty>\s*(\d+)\s*</InvQty>", text, re.IGNORECASE)
        if match:
            return match.group(1)

        if text.isdigit():
            return text

        return "0"
    except Exception:
        return "error"

# ── HTML parsers ─────────────────────────────────────────────────────────────

def extract_product_id(href: str) -> str:
    m = re.search(r"/(\d+)$", href)
    return m.group(1) if m else ""

def parse_products(html: str, category: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for card in soup.select("div.mulltr-a0o6yp"):
        brand_el = card.select_one("div.mulltr-8mygwt")
        name_el = card.select_one("div.mulltr-10ac8xq")
        size_el = card.select_one("div.mulltr-9c7r58")
        price_el = card.select_one("div.mulltr-12hvjv6")
        rrp_el = card.select_one("div.mulltr-3slrqv")
        discount_el = card.select_one("div.mulltr-18u8d8r div.text")
        rating_el = card.select_one("span.MuiRating-root")
        link_el = card.select_one("a.mulltr-96helz")

        brand = brand_el.get_text(strip=True) if brand_el else ""
        name = name_el.get_text(strip=True) if name_el else ""
        size = size_el.get_text(strip=True) if size_el else ""
        price = price_el.get_text(strip=True) if price_el else ""
        rrp = rrp_el.get_text(strip=True).replace("RRP ", "") if rrp_el else ""
        discount = discount_el.get_text(separator=" ", strip=True) if discount_el else ""

        rating = ""
        if rating_el:
            aria = rating_el.get("aria-label", "")
            rating = re.sub(r"\s*[Ss]tars?\s*$", "", aria).strip()

        href = link_el.get("href", "") if link_el else ""
        product_id = extract_product_id(href)
        product_url = f"https://www.strawberrynet.com{href}" if href.startswith("/") else href

        if not product_id:
            continue

        products.append({
            "category": category,
            "product_id": product_id,
            "brand": brand,
            "name": name,
            "size": size,
            "price": price,
            "rrp": rrp,
            "discount": discount,
            "rating": rating,
            "quantity": "",
            "product_url": product_url,
        })

    return products

# ── Scraper ──────────────────────────────────────────────────────────────────

async def scrape_categories() -> list:
    all_products = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"],
            locale="en-US",
        )
        page = await context.new_page()

        for category, url in CATEGORIES:
            try:
                log(f"[{category}] fetching {url}")
                await page.goto(url, wait_until="networkidle", timeout=PAGE_TIMEOUT)
                await page.wait_for_timeout(PAGE_LOAD_WAIT)
                html = await page.content()
                prods = parse_products(html, category)
                log(f"[{category}] {len(prods)} products")
                all_products.extend(prods)
            except Exception as exc:
                log(f"[{category}] error: {exc}")

        await browser.close()

    return all_products

def build_csv(products: list[dict]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(products)
    return output.getvalue()

def refresh_data():
    global latest_csv, last_refresh_utc, last_product_count, last_error

    try:
        log("Starting refresh...")
        raw = asyncio.run(scrape_categories())

        seen = set()
        products = []
        for p in raw:
            pid = p["product_id"]
            if pid not in seen:
                seen.add(pid)
                products.append(p)

        log(f"Unique products: {len(products)}")

        for i, prod in enumerate(products, 1):
            qty = get_quantity(prod["product_id"])
            prod["quantity"] = qty
            log(f"{i}/{len(products)} prod={prod['product_id']} qty={qty}")
            time.sleep(QTY_DELAY)

        csv_text = build_csv(products)

        with state_lock:
            latest_csv = csv_text
            last_refresh_utc = datetime.now(timezone.utc)
            last_product_count = len(products)
            last_error = None

        with open("latest_strawberrynet.csv", "w", encoding="utf-8", newline="") as f:
            f.write(csv_text)

        log("Refresh completed")

    except Exception as exc:
        with state_lock:
            last_error = str(exc)
        log(f"Refresh failed: {exc}")

def scheduled_refresh():
    refresh_data()

# ── FastAPI lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(
        scheduled_refresh,
        trigger="interval",
        hours=3,
        id="strawberrynet_refresh",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()

    # first scrape on startup
    await asyncio.to_thread(refresh_data)

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)

app = FastAPI(title="Strawberrynet Scraper API", lifespan=lifespan)

@app.get("/csv")
def get_csv():
    with state_lock:
        if not latest_csv:
            return Response(content="CSV not ready yet", media_type="text/plain", status_code=503)

        return Response(
            content=latest_csv,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="latest_strawberrynet.csv"'},
        )

@app.get("/status")
def status():
    with state_lock:
        return {
            "last_refresh_utc": last_refresh_utc.isoformat() if last_refresh_utc else None,
            "product_count": last_product_count,
            "error": last_error,
        }

@app.post("/refresh")
def manual_refresh():
    refresh_data()
    return {"ok": True, "message": "refresh completed"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)