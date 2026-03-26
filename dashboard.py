"""
Circular Waste Intelligence System – Standalone Dashboard
Reads data.csv and generates matplotlib analytics charts + console stats.

Usage:
    python dashboard.py
"""

import os
import csv
import sys
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

CSV_FILE = 'data.csv'
OUTPUT_IMAGE = 'dashboard_output.png'

# Color scheme matching the web UI
COLORS = {
    'dry_waste': '#3b82f6',
    'other_waste': '#f59e0b',
    'wet_waste': '#10b981',
}

DEFAULT_COLOR = '#8b5cf6'


def load_data():
    """Load and parse CSV data."""
    if not os.path.exists(CSV_FILE):
        print(f"❌ No data file found at '{CSV_FILE}'.")
        print("   Run the web app and classify some images first!")
        sys.exit(1)

    entries = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)

    if not entries:
        print("❌ Data file is empty. Classify some waste images first!")
        sys.exit(1)

    return entries


def compute_stats(entries):
    """Compute waste type counts and percentages."""
    counts = {}
    for e in entries:
        wt = e.get('waste_type', 'unknown')
        counts[wt] = counts.get(wt, 0) + 1

    total = len(entries)
    percentages = {k: round(v / total * 100, 1) for k, v in counts.items()}

    return counts, percentages, total


def print_summary(counts, percentages, total):
    """Print formatted summary to console."""
    print("\n" + "=" * 50)
    print("  🌿 WASTE ANALYTICS SUMMARY")
    print("=" * 50)
    print(f"\n  Total Scans: {total}\n")

    for wtype, count in sorted(counts.items()):
        bar = "█" * int(percentages[wtype] / 2)
        icon = {'dry_waste': '♻️', 'wet_waste': '🍃', 'other_waste': '🔶'}.get(wtype, '❓')
        name = wtype.replace('_', ' ').title()
        print(f"  {icon} {name:15s}  {count:4d}  ({percentages[wtype]:5.1f}%)  {bar}")

    print("\n" + "=" * 50)


def generate_charts(counts, percentages, total):
    """Generate and save bar + pie chart."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#0f172a')

    labels = list(counts.keys())
    values = list(counts.values())
    colors = [COLORS.get(l, DEFAULT_COLOR) for l in labels]
    display_labels = [l.replace('_', ' ').title() for l in labels]

    # ── Bar Chart ──
    ax1.set_facecolor('#1e293b')
    bars = ax1.bar(display_labels, values, color=colors, edgecolor='white', linewidth=0.5, width=0.6)
    ax1.set_title('Waste Type Distribution', color='white', fontsize=14, fontweight='bold', pad=12)
    ax1.set_ylabel('Count', color='#94a3b8', fontsize=11)
    ax1.tick_params(colors='#94a3b8')
    ax1.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.spines['bottom'].set_color('#334155')
    ax1.spines['left'].set_color('#334155')

    # Add value labels on bars
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                 str(val), ha='center', color='white', fontweight='bold', fontsize=12)

    # ── Pie Chart ──
    ax2.set_facecolor('#0f172a')
    wedges, texts, autotexts = ax2.pie(
        values, labels=display_labels, colors=colors, autopct='%1.1f%%',
        startangle=90, pctdistance=0.75,
        wedgeprops=dict(width=0.4, edgecolor='#0f172a', linewidth=2)
    )
    for t in texts:
        t.set_color('#e2e8f0')
        t.set_fontsize(10)
    for t in autotexts:
        t.set_color('white')
        t.set_fontweight('bold')
        t.set_fontsize(10)
    ax2.set_title('Percentage Breakdown', color='white', fontsize=14, fontweight='bold', pad=12)

    plt.suptitle(f'Circular Waste Intelligence Dashboard  •  {total} Total Scans',
                 color='#10b981', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()

    print(f"\n  📊 Dashboard chart saved as: {OUTPUT_IMAGE}")


def main():
    entries = load_data()
    counts, percentages, total = compute_stats(entries)
    print_summary(counts, percentages, total)
    generate_charts(counts, percentages, total)
    print("  ✅ Done!\n")


if __name__ == '__main__':
    main()
