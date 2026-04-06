import os
import re
import subprocess
import sys
import concurrent.futures
from difflib import SequenceMatcher
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from scraper import fetch_article_details, search_idntimes_candidates_via_driver


def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Import Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Outfit:wght@400;600;800&family=JetBrains+Mono&display=swap');

        /* Global Theme Style */
        .main {
            background-color: #0f172a;
            color: #f8fafc;
        }

        /* Typography */
        h1, h2, h3, .stHeader {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em;
            color: #f8fafc !important;
        }
        
        p, span, label, .stMarkdown {
            font-family: 'Inter', sans-serif !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-image: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Sidebar Text Contrast */
        [data-testid="stSidebarNav"] span, 
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }

        /* Radio button selected state label color */
        [data-testid="stSidebar"] [data-checked="true"] + div p {
            color: #818cf8 !important; /* Indigo accent for active menu */
            font-weight: 700 !important;
        }

        /* Glass Card Container */
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(12px);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }

        /* Button Styling */
        .stButton>button {
            width: 100%;
            border-radius: 12px;
            padding: 0.6rem 1.5rem;
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
            color: white !important;
            border: none;
            font-weight: 600;
            box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.3);
            transition: all 0.2s ease;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(79, 70, 229, 0.5);
            background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
        }

        /* Input Styling */
        .stTextInput input, .stSelectbox [data-baseweb="select"], .stNumberInput input {
            background-color: rgba(30, 41, 59, 0.7) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            color: #f8fafc !important;
        }

        /* Terminal/Code Box */
        div[data-testid="stCodeBlock"] {
            border-radius: 12px !important;
            border: 1px solid #334155 !important;
            background: #020617 !important;
        }
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border-radius: 10px !important;
            color: #94a3b8 !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            padding: 8px 16px !important;
        }
        
        .stTabs [data-baseweb="tab--active"] {
            background-color: rgba(99, 102, 241, 0.15) !important;
            color: #818cf8 !important;
            border-color: rgba(99, 102, 241, 0.4) !important;
            font-weight: 600;
        }

        /* Success/Warning Info Redesign */
        .stAlert {
            border-radius: 12px !important;
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            margin: 1rem 0 !important;
            color: #f8fafc !important;
        }

        /* Status Widget */
        div[dir="ltr"] > div[data-testid="stStatusWidget"] {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            padding: 0.5rem !important;
            margin-bottom: 1rem !important;
        }

        /* Sidebar Header */
        .sidebar-header {
            text-align: center;
            padding: 1rem 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 1.5rem;
        }

        /* Metric styling */
        [data-testid="stMetricValue"] {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 700;
            color: #818cf8 !important;
        }
        
        /* Overlap fix: add padding to avoid collision with cards */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 5rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        """
        <div class="hero-section" style="text-align: center; padding: 2rem 0; background: radial-gradient(circle at top center, rgba(99, 102, 241, 0.15) 0%, transparent 70%); border-radius: 24px; margin-bottom: 2rem;">
            <span style="display: inline-block; padding: 4px 12px; border-radius: 20px; background: rgba(99, 102, 241, 0.2); color: #818cf8; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 12px; border: 1px solid rgba(99, 102, 241, 0.3);">Premium Tools</span>
            <h1 style="margin: 0; font-size: 3rem; background: linear-gradient(135deg, #fff 0%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">IDN Times Scraper</h1>
            <p style="color: #94a3b8; font-size: 1.1rem; margin-top: 0.5rem;">Advanced Trending Scraper & Analyzer for content creators</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR_DEFAULT = BASE_DIR / "output"
TOPIC_OPTIONS = [
    "all",
    "news",
    "hype",
    "business",
    "sport",
    "tech",
    "korea",
    "life",
    "health",
    "food",
    "travel",
    "science",
    "automotive",
]
DATE_OPTIONS = ["today", "week", "month", "all"]
SEARCH_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def list_output_files(output_dir: Path):
    if not output_dir.exists():
        return set()
    return {p.resolve() for p in output_dir.iterdir() if p.is_file()}


def group_new_files(new_files):
    grouped = {"csv": [], "json": [], "txt": [], "png": [], "other": []}
    for path in sorted(new_files):
        ext = path.suffix.lower().lstrip(".")
        if ext in grouped:
            grouped[ext].append(path)
        else:
            grouped["other"].append(path)
    return grouped


def render_file_info(path: Path):
    stat = path.stat()
    size_kb = stat.st_size / 1024
    updated = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    return f"{path.name} ({size_kb:.1f} KB, update {updated})"


def normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def title_similarity(a: str, b: str) -> float:
    na = normalize_text(a)
    nb = normalize_text(b)
    if not na or not nb:
        return 0.0

    seq_score = SequenceMatcher(None, na, nb).ratio()
    set_a = set(na.split())
    set_b = set(nb.split())
    inter = len(set_a & set_b)
    union = len(set_a | set_b) or 1
    jaccard = inter / union

    # Weighted score for typo + token overlap.
    return (0.7 * seq_score) + (0.3 * jaccard)


def enrich_matches_with_publish_info(matches, max_workers=8):
    if not matches:
        return matches

    def _fetch_one(item):
        details = fetch_article_details(item.get("URL", ""))
        date_val = None
        year_val = ""
        if details and details.get("Date") is not None:
            date_obj = details["Date"]
            try:
                date_val = date_obj.strftime("%d-%m-%Y %H:%M")
                year_val = str(date_obj.year)
            except Exception:
                date_val = str(date_obj)
                year_val = ""

        enriched = dict(item)
        enriched["Tanggal Publikasi"] = date_val or "N/A"
        enriched["Tahun"] = year_val or "N/A"
        return enriched

    enriched_rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_fetch_one, m) for m in matches]
        for fut in concurrent.futures.as_completed(futures):
            try:
                enriched_rows.append(fut.result())
            except Exception:
                pass

    url_to_row = {r["URL"]: r for r in enriched_rows if "URL" in r}
    final_rows = []
    for m in matches:
        final_rows.append(url_to_row.get(m["URL"], {**m, "Tanggal Publikasi": "N/A", "Tahun": "N/A"}))
    return final_rows


def _extract_target_url(raw_href: str) -> str:
    if not raw_href:
        return ""
    href = raw_href.strip()
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/l/?"):
        href = "https://duckduckgo.com" + href

    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc:
        qs = parse_qs(parsed.query)
        uddg = qs.get("uddg", [])
        if uddg:
            return unquote(uddg[0])
    return href


def search_idntimes_candidates(query: str, max_results: int = 20):
    """
    Search titles via search engine with site:idntimes.com filter.
    Returns list of dict: {"Title", "URL"}.
    """
    q = f'site:idntimes.com "{query}"'
    common_headers = {
        "User-Agent": SEARCH_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    def parse_duckduckgo():
        headers = dict(common_headers)
        headers["Referer"] = "https://duckduckgo.com/"
        search_url = f"https://duckduckgo.com/html/?q={quote_plus(q)}"
        res = requests.get(search_url, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        rows = []
        seen = set()

        for a in soup.select("a.result__a"):
            title = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
            url = _extract_target_url(a.get("href", ""))
            if not title or not url or "idntimes.com" not in url.lower() or url in seen:
                continue
            seen.add(url)
            rows.append({"Title": title, "URL": url})
            if len(rows) >= max_results:
                break
        return rows

    def parse_bing():
        headers = dict(common_headers)
        headers["Referer"] = "https://www.bing.com/"
        search_url = f"https://www.bing.com/search?q={quote_plus(q)}"
        res = requests.get(search_url, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        rows = []
        seen = set()

        # Common Bing selector
        for a in soup.select("li.b_algo h2 a"):
            href = a.get("href", "").strip()
            title = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
            if not href or not title or "idntimes.com" not in href.lower() or href in seen:
                continue
            seen.add(href)
            rows.append({"Title": title, "URL": href})
            if len(rows) >= max_results:
                break
        if rows:
            return rows

        # Generic fallback selector for alternate Bing markup
        for a in soup.select("a[href]"):
            href = a.get("href", "").strip()
            if "idntimes.com" not in href.lower() or href in seen:
                continue
            title = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
            if len(title) < 8:
                continue
            seen.add(href)
            rows.append({"Title": title, "URL": href})
            if len(rows) >= max_results:
                break
        return rows

    def parse_bing_rss():
        headers = dict(common_headers)
        headers["Referer"] = "https://www.bing.com/"
        rss_url = f"https://www.bing.com/search?q={quote_plus(q)}&format=rss"
        res = requests.get(rss_url, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "xml")
        rows = []
        seen = set()
        for item in soup.find_all("item"):
            title_tag = item.find("title")
            link_tag = item.find("link")
            title = re.sub(r"\s+", " ", (title_tag.text if title_tag else "").strip())
            href = (link_tag.text if link_tag else "").strip()
            if not href or not title or "idntimes.com" not in href.lower() or href in seen:
                continue
            seen.add(href)
            rows.append({"Title": title, "URL": href})
            if len(rows) >= max_results:
                break
        return rows

    def parse_idntimes_search():
        headers = dict(common_headers)
        headers["Referer"] = "https://www.idntimes.com/"
        # Fallback to IDN Times own search page
        search_url = f"https://www.idntimes.com/search?query={quote_plus(query)}"
        res = requests.get(search_url, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        rows = []
        seen = set()

        for a in soup.select("a[href]"):
            href = a.get("href", "").strip()
            if href.startswith("/"):
                href = "https://www.idntimes.com" + href
            if "idntimes.com" not in href.lower():
                continue
            if any(skip in href for skip in ["/tag/", "/index", "/info/", "/sitemap", "/quiz", "install"]):
                continue
            title = re.sub(r"\s+", " ", a.get_text(" ", strip=True))
            if len(title) < 8:
                continue
            if href in seen:
                continue
            seen.add(href)
            rows.append({"Title": title, "URL": href})
            if len(rows) >= max_results:
                break
        return rows

    errors = []

    # Primary method: use Selenium/ChromeDriver to open Google Search.
    # This avoids SSL handshake issues seen on direct requests in some environments.
    try:
        rows = search_idntimes_candidates_via_driver(query, max_results=max_results)
        if rows:
            return rows
        errors.append("Google+Driver: tidak ada hasil")
    except Exception as e:
        errors.append(f"Google+Driver: {e}")

    for name, fn in [
        ("DuckDuckGo", parse_duckduckgo),
        ("Bing", parse_bing),
        ("Bing RSS", parse_bing_rss),
        ("IDN Search", parse_idntimes_search),
    ]:
        try:
            rows = fn()
            if rows:
                return rows
            errors.append(f"{name}: tidak ada hasil")
        except Exception as e:
            errors.append(f"{name}: {e}")

    raise RuntimeError(" | ".join(errors))


def run_pipeline(topic: str, date_filter: str, scrolls: int, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    before_files = list_output_files(output_dir)

    cmd = [
        sys.executable,
        str(BASE_DIR / "main.py"),
        "--topic",
        topic,
        "--date",
        date_filter,
        "--scrolls",
        str(scrolls),
        "--output",
        str(output_dir),
    ]

    st.subheader("Log Proses")
    log_box = st.empty()
    status = st.status("Menjalankan scraper...", expanded=True)

    process = subprocess.Popen(
        cmd,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    log_lines = []
    with status:
        if process.stdout is not None:
            for line in process.stdout:
                clean = line.rstrip("\n")
                log_lines.append(clean)
                shown = "\n".join(log_lines[-350:])
                log_box.code(shown or "(tidak ada output)", language="text")

        return_code = process.wait()

    if return_code == 0:
        status.update(label="Proses selesai tanpa error.", state="complete", expanded=False)
        st.success("Pipeline selesai.")
    else:
        status.update(label=f"Proses gagal (exit code: {return_code}).", state="error", expanded=True)
        st.error("Pipeline gagal. Cek log proses di atas.")

    after_files = list_output_files(output_dir)
    new_files = after_files - before_files
    return return_code, sorted(new_files), log_lines


def render_outputs(new_files):
    st.subheader("Output")
    if not new_files:
        st.info("Tidak ada file output baru yang terdeteksi dari proses terakhir.")
        return

    grouped = group_new_files(new_files)

    tab_labels = ["CSV", "JSON", "TXT", "Charts", "Lainnya"]
    tab_csv, tab_json, tab_txt, tab_png, tab_other = st.tabs(tab_labels)

    with tab_csv:
        if grouped["csv"]:
            for csv_path in grouped["csv"]:
                st.write(render_file_info(csv_path))
                try:
                    df = pd.read_csv(csv_path)
                    st.dataframe(df.head(20), use_container_width=True)
                except Exception as e:
                    st.warning(f"Gagal membaca CSV {csv_path.name}: {e}")
                st.download_button(
                    label=f"Download {csv_path.name}",
                    data=csv_path.read_bytes(),
                    file_name=csv_path.name,
                    mime="text/csv",
                    key=f"dl_csv_{csv_path.name}",
                )
        else:
            st.caption("Tidak ada file CSV baru.")

    with tab_json:
        if grouped["json"]:
            for json_path in grouped["json"]:
                st.write(render_file_info(json_path))
                content = json_path.read_text(encoding="utf-8", errors="replace")
                st.code(content[:10000], language="json")
                st.download_button(
                    label=f"Download {json_path.name}",
                    data=content.encode("utf-8"),
                    file_name=json_path.name,
                    mime="application/json",
                    key=f"dl_json_{json_path.name}",
                )
        else:
            st.caption("Tidak ada file JSON baru.")

    with tab_txt:
        if grouped["txt"]:
            for txt_path in grouped["txt"]:
                st.write(render_file_info(txt_path))
                content = txt_path.read_text(encoding="utf-8", errors="replace")
                st.code(content[:10000], language="text")
                st.download_button(
                    label=f"Download {txt_path.name}",
                    data=content.encode("utf-8"),
                    file_name=txt_path.name,
                    mime="text/plain",
                    key=f"dl_txt_{txt_path.name}",
                )
        else:
            st.caption("Tidak ada file TXT baru.")

    with tab_png:
        if grouped["png"]:
            for img_path in grouped["png"]:
                st.write(render_file_info(img_path))
                st.image(str(img_path), use_container_width=True)
                st.download_button(
                    label=f"Download {img_path.name}",
                    data=img_path.read_bytes(),
                    file_name=img_path.name,
                    mime="image/png",
                    key=f"dl_png_{img_path.name}",
                )
        else:
            st.caption("Tidak ada file chart PNG baru.")

    with tab_other:
        if grouped["other"]:
            for other_path in grouped["other"]:
                st.write(render_file_info(other_path))
                st.download_button(
                    label=f"Download {other_path.name}",
                    data=other_path.read_bytes(),
                    file_name=other_path.name,
                    key=f"dl_other_{other_path.name}",
                )
        else:
            st.caption("Tidak ada file lain.")


def render_scraper_menu():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    with st.form("run_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            topic = st.selectbox("Topik", TOPIC_OPTIONS, index=2)
        with col2:
            date_filter = st.selectbox("Filter Tanggal", DATE_OPTIONS, index=0)
        with col3:
            scrolls = st.number_input("Jumlah Scroll", min_value=1, max_value=50, value=5, step=1)
        output_input = st.text_input("Folder Output", value=str(OUTPUT_DIR_DEFAULT))
        submitted = st.form_submit_button("Start Pipeline")
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        output_dir = Path(output_input).expanduser().resolve()
        return_code, new_files, log_lines = run_pipeline(topic, date_filter, int(scrolls), output_dir)
        st.session_state["last_run"] = {
            "return_code": return_code,
            "output_dir": str(output_dir),
            "new_files": [str(p) for p in new_files],
            "log_tail": log_lines[-40:],
        }
        render_outputs(new_files)

    if "last_run" in st.session_state:
        run = st.session_state["last_run"]
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Run Summary")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Exit Code", run["return_code"])
        with c2:
            # Shorten output path for display
            display_path = Path(run["output_dir"]).name
            st.write(f"**Storage:** `.../{display_path}`")

        with st.expander("Show Latest Logs"):
            st.code("\n".join(run["log_tail"]), language="text")
        st.markdown("</div>", unsafe_allow_html=True)


def render_title_checker_menu():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Smart Similarity Check")
    st.caption("Check if your title exists or is similar to recent trending topics.")

    with st.form("title_check_form"):
        input_title = st.text_input("Masukkan Judul Artikel")
        col1, col2 = st.columns(2)
        with col1:
            max_results = st.number_input("Maksimum Hasil Search", min_value=5, max_value=50, value=20, step=1)
        with col2:
            threshold = st.slider("Ambang Similarity (%)", min_value=50, max_value=100, value=75, step=1)
        submitted = st.form_submit_button("Cek Ketersediaan Judul")
    st.markdown("</div>", unsafe_allow_html=True)

    if not submitted:
        return

    if not input_title.strip():
        st.warning("Judul tidak boleh kosong.")
        return

    status = st.status("Performing heuristic scanning...", expanded=True)
    with status:
        st.write("1/4 Mencari judul lewat search engine (site:idntimes.com)...")
        try:
            scraped = search_idntimes_candidates(input_title.strip(), max_results=int(max_results))
        except Exception as e:
            status.update(label="Pengecekan gagal.", state="error", expanded=True)
            st.error(f"Gagal mengambil hasil search: {e}")
            return
        if not scraped:
            status.update(label="Pengecekan selesai, tapi data judul kosong.", state="error", expanded=True)
            st.error("Tidak ada hasil artikel IDN Times dari search engine untuk judul ini.")
            return

        st.write("2/4 Menghitung kemiripan judul...")
        q = input_title.strip()
        q_norm = normalize_text(q)
        scored_rows = []
        for item in scraped:
            title = item.get("Title", "").strip()
            url = item.get("URL", "").strip()
            score = title_similarity(q, title)
            exact = normalize_text(title) == q_norm
            scored_rows.append(
                {
                    "Title": title,
                    "URL": url,
                    "Similarity(%)": round(score * 100, 2),
                    "Exact": "Ya" if exact else "Tidak",
                }
            )

        scored_rows.sort(key=lambda x: (x["Exact"] == "Ya", x["Similarity(%)"]), reverse=True)
        matched_rows = [
            row for row in scored_rows
            if row["Exact"] == "Ya" or row["Similarity(%)"] >= threshold
        ]
        fallback_rows = scored_rows[:15]

        st.write("3/4 Mengambil info tanggal/tahun publikasi...")
        matched_rows = enrich_matches_with_publish_info(matched_rows)
        fallback_rows = enrich_matches_with_publish_info(fallback_rows)
        st.write("4/4 Menampilkan hasil.")

    status.update(label="Scanned successfully.", state="complete", expanded=False)

    # Wrap the entire results output section to avoid overlap
    results_container = st.container()
    with results_container:
        st.markdown('<div class="glass-card" style="margin-top: 1.5rem;">', unsafe_allow_html=True)
        st.markdown("### 🏆 Final Analysis")
        st.write(f"Matches scanned from index: `{len(scraped)}`")
        
        if matched_rows:
            df_matched = pd.DataFrame(matched_rows)
            st.success(f"**Found {len(df_matched)} Similar Items** (Matches threshold {threshold}%)")
            st.dataframe(df_matched, use_container_width=True)
            best = df_matched.iloc[0]
        else:
            st.warning(f"**No direct matches found.** Showing top 15 closest articles from search engine results.")
            df_fallback = pd.DataFrame(fallback_rows)
            st.dataframe(df_fallback, use_container_width=True)
            best = df_fallback.iloc[0]

        # Detailed Best Match Card
        st.markdown(
            f"""
            <div style="background: rgba(99, 102, 241, 0.1); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(99, 102, 241, 0.3); margin-top: 1rem;">
                <h4 style="margin: 0; color: #818cf8; font-size: 1rem;">🚨 Top Candidate:</h4>
                <p style="font-size: 1.1rem; font-weight: 600; margin: 0.5rem 0;">{best['Title']}</p>
                <div style="display: flex; gap: 1rem; color: #94a3b8; font-size: 0.85rem;">
                    <span>Similarity: <b>{best['Similarity(%)']}%</b></span>
                    <span>Year: <b>{best['Tahun']}</b></span>
                    <span>Exact: <b>{best['Exact']}</b></span>
                </div>
                <a href="{best['URL']}" target="_blank" style="display: inline-block; margin-top: 0.75rem; text-decoration: none; color: white; background: #4f46e5; padding: 4px 12px; border-radius: 6px; font-size: 0.8rem;">Browse Source Article &rarr;</a>
            </div>
            """, 
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="IDN Scraper Premium", layout="wide", page_icon="🔍")
    inject_custom_css()
    
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-header">
                <span style="font-size: 1.5rem; font-weight: 800; color: #f8fafc; font-family: 'Outfit';">IDN SCRAPER</span><br>
                <span style="font-size: 0.7rem; color: #6366f1; letter-spacing: 2px;">PREMIUM v2.0</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
        menu = st.radio("Navigation", ["Dashboard", "Title Checker"], index=0)
        st.markdown("---")
        st.caption("Developed with Novil M❤️ for efficiency.")

    render_hero()

    if menu == "Dashboard":
        render_scraper_menu()
    else:
        render_title_checker_menu()


if __name__ == "__main__":
    main()
