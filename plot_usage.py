import os

import matplotlib.pyplot as plt
import pandas as pd


def main():
    csv_file = "gemini_usage.csv"
    if not os.path.exists(csv_file):
        print(f"Error: Could not find {csv_file}. Please run some extractions first.")
        return

    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if df.empty:
        print("Usage log is empty.")
        return

    # Calculate costs for Gemini 1.5 Flash (used as proxy for 3.6-flash free/paid pricing)
    # USD Pricing (as of 2024/2025):
    # Prompt: $0.075 / 1M tokens
    # Candidates: $0.30 / 1M tokens
    PRICE_PROMPT_1M = 0.075
    PRICE_CANDIDATE_1M = 0.30
    USD_TO_VND = 25000  # Approx exchange rate

    df["cost_usd"] = (df["prompt_tokens"] / 1_000_000 * PRICE_PROMPT_1M) + (
        df["candidates_tokens"] / 1_000_000 * PRICE_CANDIDATE_1M
    )
    df["cost_vnd"] = df["cost_usd"] * USD_TO_VND

    # Group by file_name
    summary = (
        df.groupby("file_name")
        .agg(
            {
                "prompt_tokens": "sum",
                "candidates_tokens": "sum",
                "total_tokens": "sum",
                "cost_usd": "sum",
                "cost_vnd": "sum",
            }
        )
        .reset_index()
    )

    output_lines = []
    output_lines.append("\n" + "=" * 70)
    output_lines.append(" " * 20 + "GEMINI / OPENROUTER API USAGE SUMMARY")
    output_lines.append("=" * 70)

    total_usd = 0
    total_vnd = 0
    total_tokens = 0

    for _, row in summary.iterrows():
        output_lines.append(f"File: {row['file_name']}")
        output_lines.append(
            f"  - Tokens: {row['total_tokens']:,} (Prompt: {row['prompt_tokens']:,}, Out: {row['candidates_tokens']:,})"
        )
        output_lines.append(f"  - Cost:   ${row['cost_usd']:.6f}  (~ {row['cost_vnd']:,.0f} VND)")
        output_lines.append("-" * 50)

        total_usd += row["cost_usd"]
        total_vnd += row["cost_vnd"]
        total_tokens += row["total_tokens"]

    output_lines.append(f"\nTOTAL TOKENS: {total_tokens:,}")
    output_lines.append(f"TOTAL COST:   ${total_usd:.6f}  (~ {total_vnd:,.0f} VND)")
    output_lines.append("=" * 70 + "\n")

    summary_text = "\n".join(output_lines)
    print(summary_text)

    # Save to quota_output.txt
    quota_file = "quota_output.txt"
    with open(quota_file, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"Text summary saved to {quota_file}")

    # Plot
    plt.figure(figsize=(10, 6))
    bars = plt.bar(summary["file_name"], summary["total_tokens"], color="skyblue")
    plt.title("Gemini Token Usage per File", fontsize=14)
    plt.xlabel("File Name", fontsize=12)
    plt.ylabel("Total Tokens", fontsize=12)
    plt.xticks(rotation=45, ha="right")

    # Add labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            yval + (yval * 0.01),
            f"{int(yval):,}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()
    plot_file = "gemini_usage_chart.png"
    plt.savefig(plot_file)
    print(f"Chart saved to {plot_file}")
    # Optional: plt.show() # Uncomment to show the plot interactively


if __name__ == "__main__":
    main()
