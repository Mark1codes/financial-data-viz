import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages

DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

PALETTE = {
    "bg":        "#0F1117",
    "panel":     "#1A1D27",
    "grid":      "#2A2D3A",
    "text":      "#E8EAF0",
    "text_dim":  "#7B7F96",
    "accent1":   "#FF6B6B",
    "accent2":   "#4ECDC4",
    "accent3":   "#FFE66D",
    "recession": "#3A3D50",
}

FONT_FAMILY = "DejaVu Sans"


def apply_global_style():
    plt.rcParams.update({
        "figure.facecolor":     PALETTE["bg"],
        "axes.facecolor":       PALETTE["panel"],
        "axes.edgecolor":       PALETTE["grid"],
        "axes.labelcolor":      PALETTE["text_dim"],
        "axes.titlecolor":      PALETTE["text"],
        "axes.grid":            True,
        "grid.color":           PALETTE["grid"],
        "grid.linewidth":       0.6,
        "grid.alpha":           0.8,
        "xtick.color":          PALETTE["text_dim"],
        "ytick.color":          PALETTE["text_dim"],
        "xtick.labelsize":      9,
        "ytick.labelsize":      9,
        "font.family":          FONT_FAMILY,
        "text.color":           PALETTE["text"],
        "lines.linewidth":      2.2,
        "lines.solid_capstyle": "round",
    })


def load(name: str) -> pd.DataFrame:
    return pd.read_csv(os.path.join(DATA_DIR, f"{name}.csv"), parse_dates=["date"])


def shade_recessions(ax, rec_df: pd.DataFrame):
    in_recession = False
    start = None
    for _, row in rec_df.iterrows():
        if row["value"] == 1 and not in_recession:
            start = row["date"]
            in_recession = True
        elif row["value"] == 0 and in_recession:
            ax.axvspan(start, row["date"], color=PALETTE["recession"], alpha=0.5, zorder=0)
            in_recession = False
    if in_recession and start:
        ax.axvspan(start, rec_df["date"].iloc[-1], color=PALETTE["recession"], alpha=0.5, zorder=0)


def add_footer(ax, source: str = "Source: FRED, Federal Reserve Bank of St. Louis"):
    ax.annotate(
        source,
        xy=(0, -0.12), xycoords="axes fraction",
        fontsize=7.5, color=PALETTE["text_dim"], style="italic",
    )


def format_xaxis(ax, df: pd.DataFrame):
    ax.set_xlim(df["date"].min(), df["date"].max())
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def add_callout(ax, x, y, text, color, xytext=(30, 20)):
    ax.annotate(
        text,
        xy=(x, y), xycoords="data",
        xytext=xytext, textcoords="offset points",
        fontsize=8.5, color=color, fontweight="bold",
        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2),
        bbox=dict(boxstyle="round,pad=0.3", fc=PALETTE["panel"], ec=color, lw=1, alpha=0.9),
    )


def chart1_debt(rec_df: pd.DataFrame) -> plt.Figure:
    df = load("consumer_debt")
    df["value_t"] = df["value"] / 1_000_000

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor(PALETTE["bg"])
    shade_recessions(ax, rec_df)
    ax.plot(df["date"], df["value_t"], color=PALETTE["accent1"], zorder=3)
    ax.fill_between(df["date"], df["value_t"], alpha=0.15, color=PALETTE["accent1"], zorder=2)

    peak_row = df.loc[df["value_t"].idxmax()]
    add_callout(ax, peak_row["date"], peak_row["value_t"],
                f"${peak_row['value_t']:.2f}T\nAll-time high",
                PALETTE["accent1"], xytext=(-80, 20))

    ax.set_title("American Consumer Debt Has Never Been Higher",
                 fontsize=15, fontweight="bold", pad=14, loc="left")
    ax.set_ylabel("Total Consumer Credit ($ Trillions)", labelpad=8)
    format_xaxis(ax, df)
    add_footer(ax, "Source: FRED -- TOTALSL  |  Shaded areas = US recessions")
    fig.tight_layout()
    return fig


def chart2_savings(rec_df: pd.DataFrame) -> plt.Figure:
    df = load("savings_rate")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor(PALETTE["bg"])
    shade_recessions(ax, rec_df)
    ax.plot(df["date"], df["value"], color=PALETTE["accent2"], zorder=3)
    ax.fill_between(df["date"], df["value"], alpha=0.15, color=PALETTE["accent2"], zorder=2)

    covid_row = df.loc[df["value"].idxmax()]
    add_callout(ax, covid_row["date"], covid_row["value"],
                f"{covid_row['value']:.1f}%\nCOVID stimulus spike",
                PALETTE["accent2"], xytext=(10, 30))

    recent = df[df["date"] >= "2022-01-01"]
    low_row = recent.loc[recent["value"].idxmin()]
    add_callout(ax, low_row["date"], low_row["value"],
                f"{low_row['value']:.1f}%\nNear historic low",
                PALETTE["accent3"], xytext=(-110, -35))

    avg = df["value"].mean()
    ax.axhline(avg, color=PALETTE["text_dim"], linewidth=1, linestyle="--", alpha=0.6, zorder=1)
    ax.text(df["date"].max(), avg + 0.3, f"Avg: {avg:.1f}%",
            color=PALETTE["text_dim"], fontsize=8)

    ax.set_title("The Safety Net is Gone -- Savings Have Collapsed",
                 fontsize=15, fontweight="bold", pad=14, loc="left")
    ax.set_ylabel("Personal Savings Rate (%)", labelpad=8)
    format_xaxis(ax, df)
    add_footer(ax, "Source: FRED -- PSAVERT  |  Shaded areas = US recessions")
    fig.tight_layout()
    return fig


def chart3_delinquency(rec_df: pd.DataFrame) -> plt.Figure:
    df = load("delinquency_rate")
    df = df.set_index("date").resample("MS").interpolate(method="time").reset_index()

    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor(PALETTE["bg"])
    shade_recessions(ax, rec_df)
    ax.plot(df["date"], df["value"], color=PALETTE["accent3"], zorder=3)
    ax.fill_between(df["date"], df["value"], alpha=0.15, color=PALETTE["accent3"], zorder=2)

    gfc_row = df.loc[df["value"].idxmax()]
    add_callout(ax, gfc_row["date"], gfc_row["value"],
                f"{gfc_row['value']:.2f}%\nGFC peak",
                PALETTE["text_dim"], xytext=(15, 10))

    recent = df[df["date"] >= "2023-01-01"]
    if not recent.empty:
        last_row = recent.iloc[-1]
        add_callout(ax, last_row["date"], last_row["value"],
                    f"{last_row['value']:.2f}%\nRising again",
                    PALETTE["accent1"], xytext=(-100, 25))

    ax.set_title("Cracks Are Forming -- Credit Card Delinquencies Are Climbing",
                 fontsize=15, fontweight="bold", pad=14, loc="left")
    ax.set_ylabel("Credit Card Delinquency Rate (%)", labelpad=8)
    format_xaxis(ax, df)
    add_footer(ax, "Source: FRED -- DRCCLACBS  |  Shaded areas = US recessions")
    fig.tight_layout()
    return fig


CHART_DESCRIPTIONS = [
    (
        "Chart 1 -- Consumer Debt at an All-Time High",
        (
            "Total consumer credit outstanding has surged past previous records, now exceeding $5 trillion. "
            "Even through the 2020 recession, the post-pandemic rebound in spending pushed debt to historic levels. "
            "This sets the stage for a fragile consumer balance sheet heading into a high-rate environment."
        ),
    ),
    (
        "Chart 2 -- The Savings Safety Net Has Collapsed",
        (
            "The personal savings rate spiked dramatically during COVID stimulus, briefly reaching over 30%. "
            "But that buffer has since evaporated. Today's savings rate is near its lowest point in over a decade, "
            "meaning consumers have little cushion to absorb financial shocks -- they're running on fumes."
        ),
    ),
    (
        "Chart 3 -- Delinquencies Are Rising: The Cracks Are Showing",
        (
            "Credit card delinquency rates have been climbing steadily since 2022. "
            "With debt at record highs and savings nearly gone, more consumers are missing payments. "
            "This is the logical conclusion: when the buffer disappears, the debt comes due -- "
            "and a growing number of Americans can't pay it."
        ),
    ),
]


def build_pdf(figures):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_path = os.path.join(OUTPUT_DIR, "consumer_stress_story.pdf")

    with PdfPages(pdf_path) as pdf:
        cover, ax_c = plt.subplots(figsize=(10, 6))
        cover.patch.set_facecolor(PALETTE["bg"])
        ax_c.axis("off")

        ax_c.text(0.5, 0.72,
                  "The American Consumer\nIs Running Out of Road",
                  ha="center", va="center", fontsize=26, fontweight="bold",
                  color=PALETTE["text"], transform=ax_c.transAxes, linespacing=1.4)

        ax_c.text(0.5, 0.48,
                  "A three-part visual story on consumer debt, savings collapse,\n"
                  "and the rising tide of credit card delinquencies.",
                  ha="center", va="center", fontsize=12,
                  color=PALETTE["text_dim"], transform=ax_c.transAxes, linespacing=1.6)

        ax_c.text(0.5, 0.28,
                  "Data: FRED, Federal Reserve Bank of St. Louis",
                  ha="center", va="center", fontsize=9, style="italic",
                  color=PALETTE["text_dim"], transform=ax_c.transAxes)

        pdf.savefig(cover, facecolor=PALETTE["bg"])
        plt.close(cover)

        for fig, (title, description) in zip(figures, CHART_DESCRIPTIONS):
            pdf.savefig(fig, facecolor=PALETTE["bg"])
            plt.close(fig)

            desc_fig, ax_d = plt.subplots(figsize=(10, 4))
            desc_fig.patch.set_facecolor(PALETTE["bg"])
            ax_d.axis("off")

            ax_d.text(0.05, 0.80, title,
                      ha="left", va="top", fontsize=13, fontweight="bold",
                      color=PALETTE["text"], transform=ax_d.transAxes)

            ax_d.text(0.05, 0.55, description,
                      ha="left", va="top", fontsize=10.5,
                      color=PALETTE["text_dim"], transform=ax_d.transAxes,
                      wrap=True, linespacing=1.7,
                      bbox=dict(boxstyle="round,pad=0.6", fc=PALETTE["panel"],
                                ec=PALETTE["grid"], lw=0.8))

            pdf.savefig(desc_fig, facecolor=PALETTE["bg"])
            plt.close(desc_fig)

    return pdf_path


def main():
    apply_global_style()
    rec_df = load("recession")

    print("Building charts...")
    fig1 = chart1_debt(rec_df)
    print("  [ok] Chart 1 -- Consumer Debt")
    fig2 = chart2_savings(rec_df)
    print("  [ok] Chart 2 -- Savings Rate")
    fig3 = chart3_delinquency(rec_df)
    print("  [ok] Chart 3 -- Delinquency Rate")

    print("Exporting PDF...")
    path = build_pdf([fig1, fig2, fig3])
    print(f"  [ok] PDF saved -> {path}")

    fig1_path = os.path.join(OUTPUT_DIR, "chart1_consumer_debt.png")
    fig2_path = os.path.join(OUTPUT_DIR, "chart2_savings_rate.png")
    fig3_path = os.path.join(OUTPUT_DIR, "chart3_delinquency.png")

    apply_global_style()
    chart1_debt(rec_df).savefig(fig1_path, facecolor=PALETTE["bg"], dpi=150, bbox_inches="tight")
    chart2_savings(rec_df).savefig(fig2_path, facecolor=PALETTE["bg"], dpi=150, bbox_inches="tight")
    chart3_delinquency(rec_df).savefig(fig3_path, facecolor=PALETTE["bg"], dpi=150, bbox_inches="tight")

    print(f"  [ok] PNGs saved to /output/")
    print("\n[DONE] All done!")


if __name__ == "__main__":
    main()
