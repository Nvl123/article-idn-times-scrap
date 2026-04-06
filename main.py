"""
main.py - IDN Times Trending Scraper CLI
Run: python main.py --topic news --date today --scrolls 5
"""

import argparse
import os
import sys
from datetime import datetime

import pandas as pd

from scraper import scrape_idntimes, TOPIC_URLS
from analyzer import (
    filter_and_analyze,
    save_results,
    generate_statistics,
    print_top_articles,
    create_visualizations,
)


def _setup_console_encoding():
    """Force UTF-8 output when supported to avoid UnicodeEncodeError on Windows."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def main():
    _setup_console_encoding()

    parser = argparse.ArgumentParser(
        description="🔍 IDN Times Trending Scraper & Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python main.py --topic news --date today --scrolls 5
  python main.py --topic hype --date week --scrolls 10
  python main.py --topic all  --date month --scrolls 8
  python main.py --topic tech --date all
        """,
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="all",
        choices=list(TOPIC_URLS.keys()),
        help="Topik yang ingin di-scrape. Default: all",
    )
    parser.add_argument(
        "--date",
        type=str,
        choices=["all", "today", "week", "month"],
        default="today",
        help="Filter tanggal artikel (all/today/week/month). Default: today",
    )
    parser.add_argument(
        "--scrolls",
        type=int,
        default=5,
        help="Berapa kali scroll halaman untuk memuat artikel. Default: 5",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Folder output untuk menyimpan hasil. Default: ./output/",
    )

    args = parser.parse_args()

    # ── Setup output dir ──
    output_dir = args.output or os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_prefix = f"idntimes_{args.topic}_{args.date}_{timestamp}"

    # ── Banner ──
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          🔍 IDN TIMES TRENDING SCRAPER & ANALYZER       ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  Topik       : {args.topic.upper():<41} ║")
    print(f"║  Filter      : {args.date.upper():<41} ║")
    print(f"║  Scroll      : {args.scrolls:<41} ║")
    print(f"║  Waktu       : {datetime.now().strftime('%d %b %Y %H:%M:%S'):<41} ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # ═══════════════════════════════════════════════════════════
    # PHASE 1: SCRAPING
    # ═══════════════════════════════════════════════════════════
    print("\n" + "━" * 60)
    print("  ⚙️  PHASE 1: Scraping Artikel dari IDN Times")
    print("━" * 60)

    try:
        raw_articles = scrape_idntimes(topic=args.topic, max_scrolls=args.scrolls)
    except Exception as e:
        print(f"\n[✗] FATAL ERROR saat scraping: {e}")
        sys.exit(1)

    if not raw_articles:
        print("\n[✗] Tidak ada artikel yang berhasil di-scrape.")
        print("    Coba: --scrolls 10 atau topik lain.")
        sys.exit(1)

    # ═══════════════════════════════════════════════════════════
    # PHASE 2: FILTERING & ANALYSIS
    # ═══════════════════════════════════════════════════════════
    print("\n" + "━" * 60)
    print("  📊  PHASE 2: Analisis & Filtering Data")
    print("━" * 60)

    df = filter_and_analyze(raw_articles, date_filter=args.date)

    if df.empty:
        print(f"\n[!] Tidak ada artikel yang cocok dengan filter tanggal '{args.date}'.")
        print("    Coba gunakan --date all atau --date week.")
        sys.exit(0)

    # ═══════════════════════════════════════════════════════════
    # PHASE 3: OUTPUT RESULTS
    # ═══════════════════════════════════════════════════════════
    print("\n" + "━" * 60)
    print("  📰  PHASE 3: Hasil Analisis")
    print("━" * 60)

    # Print top articles
    top_lines = print_top_articles(df, n=15)
    for line in top_lines:
        print(line)

    # Print full statistics
    stat_lines = generate_statistics(df)
    for line in stat_lines:
        print(line)

    # ═══════════════════════════════════════════════════════════
    # PHASE 4: SAVE & VISUALIZE
    # ═══════════════════════════════════════════════════════════
    print("\n" + "━" * 60)
    print("  💾  PHASE 4: Menyimpan Hasil & Membuat Visualisasi")
    print("━" * 60)

    # Save CSV & JSON
    save_results(df, output_dir, output_prefix=output_prefix)

    # Generate charts
    create_visualizations(df, output_dir, output_prefix=output_prefix)

    # ═══════════════════════════════════════════════════════════
    # DONE
    # ═══════════════════════════════════════════════════════════
    print("\n" + "═" * 60)
    print(f"  ✅ SELESAI! Semua hasil disimpan di folder: {output_dir}")
    print("═" * 60)
    print()


if __name__ == "__main__":
    main()
