import pandas as pd
import matplotlib.pyplot as plt
import textwrap

input_file = "../ai_use/github_users_with_ai_signals.csv"

keywords = [ "deaf","hard of hearing","slight hearing loss","minimal hearing loss","mild hearing loss","moderate hearing loss","severe hearing loss","profound hearing loss","dyscalculia","dyslexia","attention deficit disorder","adhd","add","tourette's syndrome","dyspraxia","developmental coordination disorder","autism","asd","audhd","disabled","visually impaired", "blind", "low vision", "partially blind", "partially sighted", "legally blind", "sight loss", "blv", "bvi"]

color_before = "#FFD166"
color_after = "#EF476F"
color_change = "#06D6A0"

keyword_to_category = {
    "deaf": "Physical",

    "dyscalculia": "Non-Physical",
    "dyslexia": "Non-Physical",
    "adhd": "Non-Physical",
    "autism": "Non-Physical",
    "asd": "Non-Physical",
    "audhd": "Non-Physical",

    "visually impaired": "Visual",
    "blind": "Visual",
    "legally blind": "Visual",

    "disabled": "Disabled"
}

#median before vs after for commits and net lines
def compute_stats(df, before_col, after_col, output_csv, chart_file, title, ylabel):
    stats_before = df.groupby("keyword")[before_col].median()
    stats_after = df.groupby("keyword")[after_col].median()
    
    stats = pd.DataFrame({
        "before": stats_before,
        "after": stats_after
    })

    stats = stats[(stats["before"] != 0) | (stats["after"] != 0)]
    stats = stats.sort_values(by="before", ascending=True)

    stats.to_csv(output_csv)

    print(f"\n Stats:")
    print(stats)

    #bar chart(median vals)
    wrapped_labels = ["\n".join(textwrap.wrap(label, 12)) for label in stats.index]

    x = range(len(stats))
    width = 0.35
    
    plt.figure(figsize=(12,6))
    plt.bar([i - width/2 for i in x], stats["before"], width, label = "Before", color = color_before, alpha = 0.8)
    plt.bar([i + width/2 for i in x], stats["after"], width, label = "After", color = color_after, alpha = 0.8)

    plt.xticks(x, wrapped_labels, rotation=45, ha="right")
    
    plt.axhline(0, linewidth=1)

    plt.ylabel(ylabel)
    plt.yscale("symlog")
    plt.title(title)
    plt.legend()

    plt.tight_layout()
    plt.savefig(chart_file)
    plt.show()

#median change (before-after) to see if activity increased
def compute_change(df, change_col, output_csv, chart_file, title, ylabel):

    stats = df.groupby("keyword")[change_col].median()
    stats = stats[stats != 0]
    stats = stats.sort_values(ascending=True)

    stats.to_csv(output_csv)

    print(f"\n Change stats:")
    print(stats)

    wrapped_labels = ["\n".join(textwrap.wrap(label, 12)) for label in stats.index]

    plt.figure(figsize=(14,7))
    plt.bar(range(len(stats)), stats, color = color_change, alpha = 0.8)
    plt.xticks(range(len(stats)), wrapped_labels, rotation=45, ha="right")
    plt.axhline(0,linewidth=1)
    plt.yscale("symlog")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(chart_file)
    plt.show()

def compute_acceptance_rate(df, before_col, after_col, output_csv, chart_file, title, ylabel):
    valid = df[(df["acceptance_rate_before"] != 0) & (df["acceptance_rate_after"] != 0)].copy()

    stats_before = valid.groupby("keyword")["acceptance_rate_before"].median()*100
    stats_after = valid.groupby("keyword")["acceptance_rate_after"].median()*100

    stats = pd.DataFrame({
        "before": stats_before,
        "after": stats_after
    })

    stats = stats.dropna(how="all")
    stats = stats.sort_values(by="before", ascending=True)

    stats.to_csv(output_csv)

    print(f"\n Acceptance rate stats:")
    print(stats)

    wrapped_labels = ["\n".join(textwrap.wrap(label, 12)) for label in stats.index]
    x = range(len(stats))
    width = 0.35

    plt.figure(figsize=(12,6))
    plt.bar([i - width/2 for i in x], stats["before"], width, label = "Before", color = color_before, alpha = 0.8)
    plt.bar([i + width/2 for i in x], stats["after"], width, label = "After", color = color_after, alpha = 0.8)
    plt.xticks(x, wrapped_labels, rotation=45, ha="right")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(chart_file)
    plt.show()

def create_nested_piechart(dist_df):
    import matplotlib.colors as mcolors

    nested_df = dist_df[dist_df["users"] > 0].copy()

    nested_df["category"] = nested_df["keyword"].map(
        keyword_to_category
    )

    nested_df = nested_df.dropna(subset=["category"])

    category_totals = (
        nested_df.groupby("category")["users"]
        .sum()
        .sort_values(ascending=False)
    )

    inner_labels = category_totals.index.tolist()
    inner_sizes = category_totals.values.tolist()

    category_colors = {
        "Non-Physical": "#06D6A0",
        "Physical": "#118AB2",
        "Visual": "#9B5DE5",
        "Disabled": "#EF476F",
        "Non-Disabled": "#FFD166"
    }

    inner_colors = [
        category_colors.get(cat, "#CCCCCC")
        for cat in inner_labels
    ]

    outer_sizes = []
    outer_labels = []
    outer_colors = []

    for category in inner_labels:

        base_color = category_colors[category]

        disabilities = nested_df[
            nested_df["category"] == category
        ].sort_values("users", ascending=False)

        rgb = mcolors.to_rgb(base_color)

        n = len(disabilities)

        for i, (_, row) in enumerate(disabilities.iterrows()):

            outer_labels.append(row["keyword"])
            outer_sizes.append(row["users"])

            factor = 0.35 + (i / max(n - 1, 1)) * 0.55

            shade = tuple(
                c * factor + (1 - factor)
                for c in rgb
            )

            outer_colors.append(shade)

    fig, ax = plt.subplots(figsize=(12, 12))

    ax.pie(
        outer_sizes,
        radius=1.3,
        labels=outer_labels,
        colors=outer_colors,
        labeldistance=1.08,
        textprops={"fontsize": 13},
        wedgeprops=dict(
            width=0.35,
            edgecolor="white"
        )
    )

    ax.pie(
        inner_sizes,
        radius=0.95,
        labels=inner_labels,
        colors=inner_colors,
        labeldistance=0.6,
        textprops={"weight": "bold", "fontsize": 13},
        wedgeprops=dict(
            width=0.35,
            edgecolor="white"
        )
    )

    plt.title(
        f"Nested Distribution of Categories and Disabilities\n(Total Users = {nested_df['users'].sum()})",
        fontsize=18
    )

    plt.tight_layout()

    plt.savefig(
        "nested_disability_distribution.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()

def main():
    df = pd.read_csv(input_file)

    df["commit_change"] = df["commits_after"] - df["commits_before"]
    df["lines_change"] = df["net_lines_after"] - df["net_lines_before"]

    #mean vs median choice
    plt.figure(figsize=(12,6))
    df.boxplot(column="commits_before", by="keyword", rot=45)
    plt.title("Distribution of Commits Before per Disability")
    plt.suptitle("")
    plt.ylabel("Commits")
    plt.yscale("symlog")
    plt.tight_layout()
    plt.savefig("median_motivation_boxplot.png")
    plt.show()

    #median commits
    compute_stats(
        df,
        "commits_before",
        "commits_after",
        "commit_statistics.csv",
        "commits_before_after_chart.png",
        "Median Commits Before vs After by Disability",
        "Median Commits"
    )

    #median lines
    compute_stats(
        df,
        "net_lines_before",
        "net_lines_after",
        "lines_statistics.csv",
        "lines_before_after_chart.png",
        "Median Lines Modified Before vs After by Disability",
        "Median Lines Modified"
    )

    #median change commits
    compute_change(
        df,
        "commit_change",
        "commit_change_statistics.csv",
        "commits_change_chart.png",
        "Median Change in Commits Modified by Disability",
        "Median Commit Change"
    )

    #median change lines
    compute_change(
        df,
        "lines_change",
        "lines_change_statistics.csv",
        "lines_change_chart.png",
        "Median Change in Lines Modified by Disability",
        "Median Line Change"
    )

    # median acceptance rate
    compute_acceptance_rate(
        df,
        "acceptance_rate_before",
        "acceptance_rate_after",
        "acceptance_rate_statistics.csv",
        "acceptance_rate_before_after_chart.png",
        "Median Acceptance Rate Before vs After by Disability",
        "Median Acceptance Rate (%)"
)

    #population distribution
    counts = df["keyword"].value_counts()
    distribution = {keyword: counts.get(keyword, 0) for keyword in keywords}

    dist_df = pd.DataFrame(
        list(distribution.items()),
        columns=["keyword", "users"]
    )

    total_users = dist_df["users"].sum()
    dist_df["percentage"] = (dist_df["users"] / total_users) * 100

    print("\nPopulation stats:\n")
    print(dist_df)

    dist_df.to_csv("keyword_population_stats.csv", index=False)

    pie_df = dist_df[dist_df["users"] > 0].copy()
    pie_df = pie_df.sort_values(by="percentage", ascending=False)
    total_users = pie_df["users"].sum()

    plt.figure(figsize=(10,10))

    colors = [
        "#FF8C42",
        "#FFD166",
        "#EF476F",
        "#F78C6B",
        "#06D6A0",
        "#118AB2",
        "#9B5DE5",
        "#F15BB5",
        "#00BBF9",
        "#00F5D4",
        "#FDFFB6"
    ]

    def autopct_func(pct):
        return f"{pct:.1f}%" if pct >= 1 else ""

    wedges, texts, autotexts = plt.pie(
        pie_df["users"],
        autopct=autopct_func,
        startangle=90,
        colors=colors[:len(pie_df)],
        wedgeprops={"alpha": 1},
        textprops={"fontsize": 14},
        pctdistance=0.72
    )
    for autotext in autotexts:
        autotext.set_fontsize(13)
        autotext.set_weight("bold")

    legend_labels = [
        f"{row['keyword']} ({row['percentage']:.1f}%, {int(row['users'])} users)"
        for _, row in pie_df.iterrows()
    ]

    plt.legend(
        wedges,
        legend_labels,
        title="Disability",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=12,
        title_fontsize=13
    )

    plt.title(f"Distribution of Disabilities (Total Users = {total_users})", fontsize=18)
    plt.tight_layout()
    plt.savefig("disability_distribution_pie_chart.png", dpi=300, bbox_inches="tight", pad_inches=0.2)
    plt.show()

    create_nested_piechart(dist_df)

    

if __name__ == "__main__":
    main()