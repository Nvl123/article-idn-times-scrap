# IDN Times Trending Scraper & Analyzer

A **command‑line** tool that scrapes articles from **IDN Times**, extracts rich metadata (date, category, tags, author, thumbnail, etc.), analyses the data and automatically generates **CSV/JSON** reports **plus visual charts**.

---

## 🎯 What does it do?
- **Scrape** any topic (news, hype, tech, sport, …) using the bundled ChromeDriver.
- **Fallback** to `webdriver‑manager` if the local driver version mismatches your Chrome version.
- **Collect** detailed metadata from the page’s `<meta>` tags (publish date, category, sub‑category, tags, author, editor, description, thumbnail, …).
- **Filter** by date ranges (`today`, `week`, `month`, or `all`).
- **Analyse**:
  - Category / sub‑category distribution
  - Top authors & editors
  - Trending tags/keywords
  - Publishing hour patterns
  - Daily article count (if multi‑day data)
- **Export** clean CSV & JSON files.
- **Visualise** automatically generated charts (pie, bar, timeline, etc.) saved as PNG.

---

## 📦 Installation
```bash
# Clone / copy this folder
cd C:\Users\ASUS\Documents\trending

# Install required Python packages
pip install -r requirements.txt
```

> **Note** – The repository already ships a ChromeDriver for Chrome 141. If your Chrome version is newer, the script will automatically fall back to `webdriver‑manager` and download a compatible driver.

---

## 🚀 Quick start
```bash
# Basic run – scrape the "hype" topic, all dates, 3 scrolls
python main.py --topic hype --date all --scrolls 3
```

### Available CLI arguments
| Argument | Description | Default | Example |
|----------|-------------|---------|---------|
| `--topic` | Topic to scrape (must be one of the keys in `TOPIC_URLS`). | `all` | `--topic news` |
| `--date`  | Date filter – `all`, `today`, `week`, `month`. | `today` | `--date week` |
| `--scrolls` | How many times the page is scrolled to load more articles. | `5` | `--scrolls 10` |
| `--output` | Optional folder where all results are stored. | `./output` | `--output C:\my\results` |

---

## 📊 Output structure (inside the `output/` folder)
```
output/
├─ idntimes_<topic>_<date>_<timestamp>.csv      # Tabular data (UTF‑8 BOM)
├─ idntimes_<topic>_<date>_<timestamp>.json     # Same data in JSON format
├─ idntimes_<topic>_<date>_<timestamp>_kategori.png   # Pie chart – category distribution
├─ idntimes_<topic>_<date>_<timestamp>_tags.png       # Bar chart – top 15 tags
├─ idntimes_<topic>_<date>_<timestamp>_jam_publikasi.png   # Hour‑of‑day timeline
├─ idntimes_<topic>_<date>_<timestamp>_penulis.png   # Bar chart – top authors
├─ idntimes_<topic>_<date>_<timestamp>_subkategori.png   # Sub‑category distribution
└─ idntimes_<topic>_<date>_<timestamp>_per_hari.png   # Daily article count (if applicable)
```

---

## 🛠️ How it works (under the hood)
1. **`scraper.py`** – launches Chrome (headless), scrolls the page, extracts unique article URLs, then fetches each article with `requests` to read the `<meta>` tags.
2. **`analyzer.py`** – converts the raw list into a `pandas.DataFrame`, applies the date filter, sorts, adds ranking, and builds statistics.
3. **`main.py`** – orchestrates the workflow, prints a nice banner, shows the top‑10 newest articles, prints a full statistical report, saves CSV/JSON and creates visualisations.

---

## 🎨 Visualisation style
- **Seaborn** with a dark‑grid theme for a modern look.
- **Pie chart** for category distribution (donut style).
- **Bar charts** for tags, authors, sub‑categories.
- **Line/area chart** for publishing‑hour heatmap.
- All charts are saved at **300 dpi** PNG, ready to embed in reports or presentations.

---

## 🐞 Troubleshooting
- **ChromeDriver version mismatch** – The script will automatically switch to `webdriver‑manager`. Make sure you have internet access the first time you run it.
- **No articles found** – Increase `--scrolls` or try a different topic. Some topics load content via infinite scroll that needs more scroll events.
- **Timeouts** – The per‑article request timeout is 8 seconds. If you have a very slow connection, increase the timeout in `scraper.py`.

---

## 📚 Further improvements (road‑map)
- Add **proxy / rotating user‑agents** to avoid rate‑limits.
- Store **view‑count** if IDN Times exposes it via an API (currently not available).
- Export **interactive HTML dashboards** (Plotly/Dash).
- Add **unit tests** for each module.

---

## 📜 License
MIT – feel free to fork, modify, and use it for personal or commercial projects.

---

*Happy scraping!*
