"""
analyzer.py - IDN Times Data Analyzer & Visualizer
Processes scraped data, generates rich statistics, and creates visualizations.
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for saving files
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from datetime import datetime, timedelta
from collections import Counter


# ─── Filtering & Analysis ────────────────────────────────────────
def filter_and_analyze(articles_data, date_filter="all"):
    """
    Convert raw article list into a cleaned, sorted DataFrame.
    
    Args:
        articles_data: list[dict] from scraper.
        date_filter:   'all', 'today', 'week', 'month'
    
    Returns:
        pd.DataFrame sorted by Date (newest first).
    """
    if not articles_data:
        print("[!] Tidak ada data untuk dianalisis.")
        return pd.DataFrame()

    df = pd.DataFrame(articles_data)

    # Ensure Date is datetime
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["DateUpdated"] = pd.to_datetime(df["DateUpdated"], errors="coerce")

    # ── Date Filter ──
    now = datetime.now()
    original_count = len(df)

    if date_filter.lower() == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        df = df[df["Date"] >= start]
    elif date_filter.lower() == "week":
        df = df[df["Date"] >= (now - timedelta(days=7))]
    elif date_filter.lower() == "month":
        df = df[df["Date"] >= (now - timedelta(days=30))]

    filtered_count = len(df)
    if filtered_count < original_count:
        print(f"    Filter tanggal '{date_filter}': {original_count} → {filtered_count} artikel.")

    if df.empty:
        return df

    # ── Sort by newest date ──
    df = df.sort_values(by="Date", ascending=False)

    # ── Drop duplicates ──
    df = df.drop_duplicates(subset=["URL"], keep="first")

    # ── Add rank ──
    df = df.reset_index(drop=True)
    df["Rank"] = range(1, len(df) + 1)

    return df


# ─── Save Results ────────────────────────────────────────────────
def save_results(df, output_dir, output_prefix="trends_data"):
    """Save DataFrame to CSV and JSON."""
    if df.empty:
        print("[!] Tidak bisa menyimpan data kosong.")
        return

    csv_path = os.path.join(output_dir, f"{output_prefix}.csv")
    json_path = os.path.join(output_dir, f"{output_prefix}.json")

    # Select columns for export
    export_cols = [
        "Rank", "Title", "URL", "Date", "Category", "Subcategory",
        "TagsStr", "Author", "Editor", "Description", "Thumbnail",
    ]
    existing_cols = [c for c in export_cols if c in df.columns]
    df_export = df[existing_cols].copy()
    df_export["Date"] = df_export["Date"].astype(str)

    df_export.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df_export.to_json(json_path, orient="records", indent=2, force_ascii=False)

    # Also save the title list as a readable text file
    txt_path = save_title_list(df, output_dir, output_prefix)

    print(f"    📄 CSV  : {csv_path}")
    print(f"    📄 JSON : {json_path}")
    print(f"    📄 TXT  : {txt_path}")


# ─── Save Title List ─────────────────────────────────────────────
def save_title_list(df, output_dir, output_prefix="trends_data"):
    """
    Save a human-readable text file listing ALL article titles
    along with date, category, author, tags and URL.
    """
    txt_path = os.path.join(output_dir, f"{output_prefix}_judul.txt")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("  DAFTAR JUDUL ARTIKEL IDN TIMES\n")
        f.write(f"  Digenerate: {datetime.now().strftime('%d %B %Y %H:%M:%S')}\n")
        f.write(f"  Total: {len(df)} artikel\n")
        f.write("=" * 70 + "\n\n")

        for _, row in df.iterrows():
            rank = row.get("Rank", "")
            title = row.get("Title", "")
            date_str = (
                row["Date"].strftime("%d %b %Y %H:%M")
                if pd.notna(row.get("Date"))
                else "N/A"
            )
            cat = row.get("Category", "")
            sub = row.get("Subcategory", "")
            cat_label = f"{cat}/{sub}" if sub else cat
            author = row.get("Author", "")
            tags = row.get("TagsStr", "")
            url = row.get("URL", "")

            f.write(f"#{rank}  {title}\n")
            f.write(f"     Tanggal   : {date_str}\n")
            f.write(f"     Kategori  : {cat_label}\n")
            if author:
                f.write(f"     Penulis   : {author}\n")
            if tags:
                f.write(f"     Tags      : {tags[:100]}\n")
            f.write(f"     URL       : {url}\n")
            f.write("-" * 70 + "\n")

    return txt_path


# ─── Generate Statistics ─────────────────────────────────────────
def generate_statistics(df):
    """
    Produce a rich text summary of the scraped data.
    Returns a list of strings.
    """
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("  📊  LAPORAN ANALISIS DATA IDN TIMES")
    lines.append("=" * 60)

    total = len(df)
    lines.append(f"\n  Total Artikel Dianalisis : {total}")

    # ── Date range ──
    if "Date" in df.columns and df["Date"].notna().any():
        earliest = df["Date"].min()
        latest = df["Date"].max()
        lines.append(f"  Rentang Waktu            : {earliest.strftime('%d %b %Y %H:%M')} — {latest.strftime('%d %b %Y %H:%M')}")

    # ── Category breakdown ──
    if "Category" in df.columns:
        cat_counts = df["Category"].value_counts()
        lines.append(f"\n  ── Distribusi Kategori ({'─' * 30})")
        for cat, cnt in cat_counts.items():
            bar = "█" * int(cnt / total * 30)
            pct = cnt / total * 100
            lines.append(f"    {cat:<18} {cnt:>4} artikel  ({pct:5.1f}%)  {bar}")

    # ── Subcategory breakdown ──
    if "Subcategory" in df.columns:
        sub_counts = df["Subcategory"].dropna().replace("", pd.NA).dropna().value_counts().head(10)
        if not sub_counts.empty:
            lines.append(f"\n  ── Top 10 Subkategori ({'─' * 30})")
            for sub, cnt in sub_counts.items():
                lines.append(f"    {sub:<25} {cnt:>4} artikel")

    # ── Top Authors ──
    if "Author" in df.columns:
        author_counts = df["Author"].dropna().replace("", pd.NA).dropna().value_counts().head(10)
        if not author_counts.empty:
            lines.append(f"\n  ── Top 10 Penulis Paling Produktif ({'─' * 20})")
            for auth, cnt in author_counts.items():
                lines.append(f"    {auth:<30} {cnt:>4} artikel")

    # ── Trending Tags (Keywords) ──
    if "Tags" in df.columns:
        all_tags = []
        for tags_list in df["Tags"]:
            if isinstance(tags_list, list):
                all_tags.extend(tags_list)
        tag_counter = Counter(all_tags)
        top_tags = tag_counter.most_common(20)
        if top_tags:
            lines.append(f"\n  ── 🔥 Top 20 Trending Tags/Keywords ({'─' * 18})")
            for i, (tag, cnt) in enumerate(top_tags, 1):
                fire = "🔥" if i <= 3 else "  "
                lines.append(f"    {fire} #{i:<3} {tag:<35} muncul {cnt}x")

    # ── Articles per hour (publishing pattern) ──
    if "Date" in df.columns and df["Date"].notna().any():
        hour_counts = df["Date"].dt.hour.value_counts().sort_index()
        if not hour_counts.empty:
            lines.append(f"\n  ── Pola Jam Publikasi ({'─' * 30})")
            max_h = hour_counts.max()
            for h in range(24):
                cnt = hour_counts.get(h, 0)
                bar = "▓" * int(cnt / max(max_h, 1) * 20)
                lines.append(f"    {h:02d}:00  {cnt:>3} artikel  {bar}")

    lines.append("\n" + "=" * 60)
    return lines


# ─── Print Top Articles ──────────────────────────────────────────
def print_top_articles(df, n=15):
    """Print a nicely formatted list of the top N articles."""
    lines = []
    lines.append("")
    lines.append("─" * 60)
    lines.append(f"  📰  TOP {min(n, len(df))} ARTIKEL TERBARU")
    lines.append("─" * 60)

    for _, row in df.head(n).iterrows():
        date_str = row["Date"].strftime("%d %b %Y %H:%M") if pd.notna(row.get("Date")) else "Tanggal N/A"
        cat = row.get("Category", "")
        sub = row.get("Subcategory", "")
        cat_label = f"{cat}/{sub}" if sub else cat
        author = row.get("Author", "")
        tags = row.get("TagsStr", "")

        lines.append(f"\n  #{row['Rank']}  {row['Title']}")
        lines.append(f"       📅 {date_str}  |  📂 {cat_label}  |  ✍️  {author}")
        if tags:
            lines.append(f"       🏷️  {tags[:80]}")
        lines.append(f"       🔗 {row['URL']}")

    lines.append("\n" + "─" * 60)
    return lines


# ─── Visualizations ──────────────────────────────────────────────
def create_visualizations(df, output_dir, output_prefix="trends_data"):
    """
    Generate multiple chart images from the data.
    """
    if df.empty or len(df) < 2:
        print("[!] Data terlalu sedikit untuk divisualisasikan.")
        return

    sns.set_theme(style="darkgrid", palette="deep")
    plt.rcParams.update({
        "font.size": 10,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
    })

    charts_created = []

    # ──────────────────────────────────────────────────────────
    # Chart 1: Category Distribution (Pie Chart)
    # ──────────────────────────────────────────────────────────
    if "Category" in df.columns:
        cat_counts = df["Category"].value_counts()
        if len(cat_counts) > 1:
            fig, ax = plt.subplots(figsize=(8, 8))
            colors = sns.color_palette("Set2", len(cat_counts))
            wedges, texts, autotexts = ax.pie(
                cat_counts.values,
                labels=cat_counts.index,
                autopct="%1.1f%%",
                colors=colors,
                startangle=140,
                pctdistance=0.85,
                wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
            )
            for t in autotexts:
                t.set_fontsize(10)
                t.set_fontweight("bold")
            ax.set_title("Distribusi Artikel per Kategori", fontweight="bold", pad=20)
            path = os.path.join(output_dir, f"{output_prefix}_kategori.png")
            plt.tight_layout()
            plt.savefig(path, dpi=200, bbox_inches="tight")
            plt.close()
            charts_created.append(path)

    # ──────────────────────────────────────────────────────────
    # Chart 2: Top 15 Tags Bar Chart
    # ──────────────────────────────────────────────────────────
    if "Tags" in df.columns:
        all_tags = []
        for tags_list in df["Tags"]:
            if isinstance(tags_list, list):
                all_tags.extend(tags_list)
        tag_counter = Counter(all_tags)
        top_tags = tag_counter.most_common(15)
        if top_tags:
            tags_df = pd.DataFrame(top_tags, columns=["Tag", "Count"])
            fig, ax = plt.subplots(figsize=(10, 7))
            palette = sns.color_palette("magma_r", len(tags_df))
            sns.barplot(
                data=tags_df, x="Count", y="Tag",
                hue="Tag", palette=palette, dodge=False, legend=False, ax=ax,
            )
            for i, (cnt,) in enumerate(zip(tags_df["Count"])):
                ax.text(cnt + 0.2, i, str(cnt), va="center", fontweight="bold")
            ax.set_title("🔥 Top 15 Trending Tags / Keywords", fontweight="bold", pad=15)
            ax.set_xlabel("Jumlah Kemunculan")
            ax.set_ylabel("")
            path = os.path.join(output_dir, f"{output_prefix}_tags.png")
            plt.tight_layout()
            plt.savefig(path, dpi=200, bbox_inches="tight")
            plt.close()
            charts_created.append(path)

    # ──────────────────────────────────────────────────────────
    # Chart 3: Publishing Timeline (articles per hour)
    # ──────────────────────────────────────────────────────────
    if "Date" in df.columns and df["Date"].notna().sum() >= 3:
        fig, ax = plt.subplots(figsize=(12, 5))
        hours = df["Date"].dt.hour
        hour_data = hours.value_counts().reindex(range(24), fill_value=0)
        ax.fill_between(hour_data.index, hour_data.values, alpha=0.3, color="#4C72B0")
        ax.plot(hour_data.index, hour_data.values, "o-", color="#4C72B0", linewidth=2, markersize=6)
        ax.set_title("Pola Jam Publikasi Artikel", fontweight="bold", pad=15)
        ax.set_xlabel("Jam (WIB)")
        ax.set_ylabel("Jumlah Artikel")
        ax.set_xticks(range(24))
        ax.set_xticklabels([f"{h:02d}" for h in range(24)])
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        path = os.path.join(output_dir, f"{output_prefix}_jam_publikasi.png")
        plt.tight_layout()
        plt.savefig(path, dpi=200, bbox_inches="tight")
        plt.close()
        charts_created.append(path)

    # ──────────────────────────────────────────────────────────
    # Chart 4: Top Authors Bar Chart
    # ──────────────────────────────────────────────────────────
    if "Author" in df.columns:
        author_counts = df["Author"].replace("", pd.NA).dropna().value_counts().head(10)
        if len(author_counts) >= 2:
            fig, ax = plt.subplots(figsize=(10, 6))
            palette = sns.color_palette("viridis", len(author_counts))
            sns.barplot(
                x=author_counts.values, y=author_counts.index,
                hue=author_counts.index, palette=palette, dodge=False,
                legend=False, ax=ax,
            )
            for i, cnt in enumerate(author_counts.values):
                ax.text(cnt + 0.15, i, str(cnt), va="center", fontweight="bold")
            ax.set_title("Top 10 Penulis Paling Produktif", fontweight="bold", pad=15)
            ax.set_xlabel("Jumlah Artikel")
            ax.set_ylabel("")
            path = os.path.join(output_dir, f"{output_prefix}_penulis.png")
            plt.tight_layout()
            plt.savefig(path, dpi=200, bbox_inches="tight")
            plt.close()
            charts_created.append(path)

    # ──────────────────────────────────────────────────────────
    # Chart 5: Subcategory Distribution (Horizontal Bar)
    # ──────────────────────────────────────────────────────────
    if "Subcategory" in df.columns:
        sub_counts = df["Subcategory"].replace("", pd.NA).dropna().value_counts().head(12)
        if len(sub_counts) >= 2:
            fig, ax = plt.subplots(figsize=(10, 6))
            palette = sns.color_palette("coolwarm", len(sub_counts))
            sns.barplot(
                x=sub_counts.values, y=sub_counts.index,
                hue=sub_counts.index, palette=palette, dodge=False,
                legend=False, ax=ax,
            )
            for i, cnt in enumerate(sub_counts.values):
                ax.text(cnt + 0.15, i, str(cnt), va="center", fontweight="bold")
            ax.set_title("Distribusi Subkategori Artikel", fontweight="bold", pad=15)
            ax.set_xlabel("Jumlah Artikel")
            ax.set_ylabel("")
            path = os.path.join(output_dir, f"{output_prefix}_subkategori.png")
            plt.tight_layout()
            plt.savefig(path, dpi=200, bbox_inches="tight")
            plt.close()
            charts_created.append(path)

    # ──────────────────────────────────────────────────────────
    # Chart 6: Articles per Day (if multi-day data)
    # ──────────────────────────────────────────────────────────
    if "Date" in df.columns and df["Date"].notna().sum() >= 3:
        daily = df.set_index("Date").resample("D").size()
        if len(daily) > 1:
            fig, ax = plt.subplots(figsize=(12, 5))
            daily.plot(kind="bar", color=sns.color_palette("Blues_d", len(daily)), ax=ax)
            ax.set_title("Jumlah Artikel per Hari", fontweight="bold", pad=15)
            ax.set_xlabel("Tanggal")
            ax.set_ylabel("Jumlah Artikel")
            ax.set_xticklabels([d.strftime("%d %b") for d in daily.index], rotation=45)
            ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
            path = os.path.join(output_dir, f"{output_prefix}_per_hari.png")
            plt.tight_layout()
            plt.savefig(path, dpi=200, bbox_inches="tight")
            plt.close()
            charts_created.append(path)

    if charts_created:
        print(f"\n[✓] {len(charts_created)} visualisasi berhasil dibuat:")
        for p in charts_created:
            print(f"    📊 {os.path.basename(p)}")
    else:
        print("[!] Tidak cukup data untuk membuat visualisasi.")
