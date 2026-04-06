"""
scraper.py - IDN Times Article Scraper
Uses Selenium (ChromeDriver) to load pages, then requests for article detail.
Extracts rich metadata from each article's meta tags.
"""

import time
import os
import concurrent.futures
import re
import requests
from dateutil import parser as dateparser
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
from bs4 import BeautifulSoup
from tqdm import tqdm

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_WDM = True
except ImportError:
    HAS_WDM = False


# ─── Topic URL Map ───────────────────────────────────────────────
TOPIC_URLS = {
    "all":        "https://www.idntimes.com/",
    "news":       "https://www.idntimes.com/news",
    "hype":       "https://www.idntimes.com/hype",
    "business":   "https://www.idntimes.com/business",
    "sport":      "https://www.idntimes.com/sport",
    "tech":       "https://www.idntimes.com/tech",
    "korea":      "https://www.idntimes.com/korea",
    "life":       "https://www.idntimes.com/life",
    "health":     "https://www.idntimes.com/health",
    "food":       "https://www.idntimes.com/food",
    "travel":     "https://www.idntimes.com/travel",
    "science":    "https://www.idntimes.com/science",
    "automotive": "https://www.idntimes.com/automotive",
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/146.0.7680.178 Safari/537.36"
)


def _extract_article_cards(soup):
    """Extract unique article cards (title + URL) from page soup."""
    processed_urls = set()
    cards = []

    links = soup.find_all("a", href=True)
    for a in links:
        href = a["href"]
        if href.startswith("/"):
            href = "https://www.idntimes.com" + href

        # Filter: must be idntimes, not tag/index/info pages
        if "idntimes.com" not in href:
            continue
        if any(skip in href for skip in ["/tag/", "/index", "/info/", "/sitemap", "/quiz", "install"]):
            continue

        # Must contain a title-like element
        title_elem = a.find(["h2", "h3"])
        if not title_elem:
            continue
        title = re.sub(r"\s+", " ", title_elem.get_text(strip=True))
        if len(title) < 15:
            continue

        if href not in processed_urls:
            processed_urls.add(href)
            cards.append({"Title": title, "URL": href})

    return cards


# ─── Driver Initialization ───────────────────────────────────────
def initialize_driver():
    """
    Create a headless Chrome driver.
    1. Try the local chromedriver bundled in this project.
    2. Fallback to Selenium Manager (auto-matching, built into selenium).
    3. Fallback to webdriver-manager for auto-matching version.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"user-agent={USER_AGENT}")
    # Suppress logging noise
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    # --- Attempt 1: local chromedriver ---
    driver_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "chromedriver-win64", "chromedriver-win64", "chromedriver.exe"
    )
    if os.path.exists(driver_path):
        try:
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            print("[✓] Using local ChromeDriver.")
            return driver
        except (SessionNotCreatedException, WebDriverException) as e:
            print(f"[!] Local ChromeDriver gagal (versi tidak cocok).")
            print(f"    Detail: {str(e).splitlines()[0]}")

    # --- Attempt 2: Selenium Manager (built-in selenium) ---
    # Selenium 4.6+ can auto-resolve and download the matching driver.
    print("[*] Mencoba Selenium Manager (auto-detect ChromeDriver)...")
    try:
        driver = webdriver.Chrome(options=options)
        print("[✓] ChromeDriver berhasil dimuat via Selenium Manager.")
        return driver
    except Exception as e:
        print(f"[!] Selenium Manager gagal: {e}")

    # --- Attempt 3: webdriver-manager ---
    if HAS_WDM:
        print("[*] Mengunduh ChromeDriver yang sesuai via webdriver-manager...")
        try:
            installed_path = ChromeDriverManager().install()

            # Some webdriver-manager versions can return a non-executable path
            # (e.g. THIRD_PARTY_NOTICES.chromedriver). Normalize to the real exe.
            exe_path = installed_path
            if not exe_path.lower().endswith(".exe"):
                candidate = os.path.join(os.path.dirname(installed_path), "chromedriver.exe")
                if os.path.exists(candidate):
                    exe_path = candidate

            if not os.path.exists(exe_path) or not exe_path.lower().endswith(".exe"):
                raise RuntimeError(
                    f"Path driver tidak valid dari webdriver-manager: {installed_path}"
                )

            service = Service(executable_path=exe_path)
            driver = webdriver.Chrome(service=service, options=options)
            print("[✓] ChromeDriver berhasil dimuat via webdriver-manager.")
            return driver
        except Exception as e:
            print(f"[✗] webdriver-manager juga gagal: {e}")

    raise RuntimeError(
        "Tidak bisa menginisialisasi ChromeDriver.\n"
        "Pastikan Google Chrome terinstall dan dependency sudah benar.\n"
        "Coba jalankan:\n"
        "  pip install -U selenium webdriver-manager"
    )


def scrape_article_titles(topic="all", max_scrolls=5):
    """
    Scrape only article titles + URLs from IDN Times topic page.
    Faster than full metadata scraping.
    """
    driver = initialize_driver()
    try:
        url = TOPIC_URLS.get(topic.lower(), f"https://www.idntimes.com/{topic.lower()}")
        print(f"[*] Membuka halaman: {url}")
        driver.get(url)
        time.sleep(2)

        print(f"[*] Scrolling halaman ({max_scrolls}x) untuk memuat lebih banyak artikel...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in tqdm(range(max_scrolls), desc="Scrolling"):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                try:
                    load_more = driver.find_element(By.CSS_SELECTOR, "button[class*='load'], a[class*='load']")
                    load_more.click()
                    time.sleep(1.5)
                except Exception:
                    pass
            last_height = new_height

        soup = BeautifulSoup(driver.page_source, "html.parser")
        cards = _extract_article_cards(soup)
        print(f"[✓] Ditemukan {len(cards)} judul artikel unik.")
        return cards
    finally:
        driver.quit()


# ─── Article Detail Fetcher ──────────────────────────────────────
def fetch_article_details(url):
    """
    Fetch individual article page with requests (fast) and extract
    all available metadata from <meta> tags.
    
    IDN Times exposes rich meta tags including:
      - content_published_date, content_updated_date
      - content_category, content_subcategory
      - content_tag (keywords)
      - content_creator_fullname (author)
      - content_editor
      - og:description (summary)
      - og:image (thumbnail)
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        res = requests.get(url, headers=headers, timeout=8)
        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")

        def get_meta(name=None, property=None):
            """Helper to safely read a meta tag content."""
            if name:
                tag = soup.find("meta", attrs={"name": name})
            elif property:
                tag = soup.find("meta", attrs={"property": property})
            else:
                return None
            return tag.get("content", "").strip() if tag else None

        # ── Date ──
        date_str = get_meta(name="content_published_date")
        dt = None
        if date_str:
            try:
                dt = dateparser.parse(date_str)
            except Exception:
                pass
        if dt and dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)

        # ── Updated date ──
        updated_str = get_meta(name="content_updated_date")
        dt_updated = None
        if updated_str:
            try:
                dt_updated = dateparser.parse(updated_str)
                if dt_updated and dt_updated.tzinfo is not None:
                    dt_updated = dt_updated.replace(tzinfo=None)
            except Exception:
                pass

        # ── Category / Subcategory ──
        category = get_meta(name="content_category") or ""
        subcategory = get_meta(name="content_subcategory") or ""

        # ── Tags / Keywords ──
        tags_str = get_meta(name="content_tag") or get_meta(name="keywords") or ""
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        # ── Author / Editor ──
        author = get_meta(name="content_creator_fullname") or get_meta(name="author") or ""
        editor = get_meta(name="content_editor") or ""

        # ── Description ──
        description = get_meta(name="description") or get_meta(property="og:description") or ""

        # ── Thumbnail image ──
        thumbnail = get_meta(property="og:image") or ""

        # ── Content ID ──
        content_id = get_meta(name="content_id") or ""

        return {
            "Date": dt,
            "DateUpdated": dt_updated,
            "Category": category,
            "Subcategory": subcategory,
            "Tags": tags,
            "TagsStr": ", ".join(tags),
            "Author": author,
            "Editor": editor,
            "Description": description,
            "Thumbnail": thumbnail,
            "ContentID": content_id,
        }
    except requests.exceptions.Timeout:
        return None
    except Exception:
        return None


# ─── Main Scraper ─────────────────────────────────────────────────
def scrape_idntimes(topic="all", max_scrolls=5):
    """
    Scrape IDN Times for a given topic.
    
    Args:
        topic:       Topic name (e.g. news, hype, tech, all)
        max_scrolls: How many page-scrolls to perform (more = more articles)
    
    Returns:
        list[dict] — Raw article data with full metadata.
    """
    driver = initialize_driver()

    url = TOPIC_URLS.get(topic.lower(), f"https://www.idntimes.com/{topic.lower()}")
    print(f"[*] Membuka halaman: {url}")
    driver.get(url)
    time.sleep(2)  # initial load

    # ── Scroll to load dynamic content ──
    print(f"[*] Scrolling halaman ({max_scrolls}x) untuk memuat lebih banyak artikel...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in tqdm(range(max_scrolls), desc="Scrolling"):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # No new content loaded, try clicking "load more" button if exists
            try:
                load_more = driver.find_element(By.CSS_SELECTOR, "button[class*='load'], a[class*='load']")
                load_more.click()
                time.sleep(1.5)
            except Exception:
                pass
        last_height = new_height

    # ── Parse the fully loaded page ──
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    # ── Extract unique article URLs ──
    raw_articles = _extract_article_cards(soup)

    print(f"[✓] Ditemukan {len(raw_articles)} artikel unik dari halaman.")

    if not raw_articles:
        print("[!] Tidak ada artikel ditemukan. Coba tambah jumlah scroll.")
        return []

    # ── Fetch detailed metadata concurrently ──
    print(f"[*] Mengambil metadata detail dari setiap artikel (max 15 thread)...")
    articles_data = []
    failed_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        future_map = {
            executor.submit(fetch_article_details, art["URL"]): art
            for art in raw_articles
        }
        for future in tqdm(
            concurrent.futures.as_completed(future_map),
            total=len(raw_articles),
            desc="Metadata"
        ):
            art = future_map[future]
            try:
                details = future.result()
                if details:
                    art.update(details)
                else:
                    art.update({
                        "Date": None, "DateUpdated": None,
                        "Category": topic.upper(), "Subcategory": "",
                        "Tags": [], "TagsStr": "",
                        "Author": "", "Editor": "",
                        "Description": "", "Thumbnail": "", "ContentID": "",
                    })
                    failed_count += 1
                articles_data.append(art)
            except Exception:
                failed_count += 1

    print(f"[✓] Metadata berhasil: {len(articles_data) - failed_count}/{len(articles_data)}")
    if failed_count:
        print(f"[!] {failed_count} artikel gagal diambil metadatanya (timeout/error).")

    return articles_data
