import pandas as pd
import matplotlib.pyplot as plt

input_file = "collab_stats.csv"

def main():
    df = pd.read_csv(input_file, header=None, names=["category", "count"])
    df = df[df["category"] != "collaboration_type"]
    df["count"] = pd.to_numeric(df["count"], errors="coerce")
    df = df.dropna()

    total = df["count"].sum()
    df["percentage"] = (df["count"] / total) * 100

    colors = [
        "#FFD166",
        "#00F5D4",
        "#F78C6B"
    ]
    plt.figure(figsize=(10,10))
    wedges, texts, autotexts = plt.pie(
        df["count"],
        labels=None,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90
    )

    for w in wedges:
        w.set_alpha(0.8)

    for t in autotexts:
        t.set_color("black")
        t.set_fontsize(10)

    legend_labels = [
        f"{row['category']} ({row['percentage']:.1f}%, {int(row['count'])} users)"
        for _, row in df.iterrows()
    ]
    
    plt.legend(
        wedges,
        legend_labels,
        title="Category",
        loc="center left",
        bbox_to_anchor=(1, 0.5)
    )

    plt.title(f"User Collaboration Distribution ({total})")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()