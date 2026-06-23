import pandas as pd
import matplotlib.pyplot as plt

def main():

    #df = pd.read_csv("github_users_with_ai_signals.csv")
    df = pd.read_csv("non_disabled_github_users_with_ai_signals.csv")
    df["ai_first_seen"] = pd.to_datetime(df["ai_first_seen"], errors="coerce")

    df["used_ai"] = (
        (df["ai_commit_count_before"] > 0) |
        (df["ai_commit_count_after"] > 0)
    )

    total_users = len(df)
    ai_users = df[df["used_ai"]]
    num_ai_users = len(ai_users)

    percent_ai = (num_ai_users / total_users) * 100 if total_users else 0

    mean_before = ai_users["ai_commit_ratio_before"].mean()
    mean_after = ai_users["ai_commit_ratio_after"].mean()

    median_before = ai_users["ai_commit_ratio_before"].median()
    median_after = ai_users["ai_commit_ratio_after"].median()

    median_first_seen = ai_users["ai_first_seen"].dropna().median()
    earliest = ai_users["ai_first_seen"].min()
    latest = ai_users["ai_first_seen"].max()

    categories = []

    for col in df.columns:
        if col.startswith("mentions_") and col.endswith("_before"):
            cat = col.replace("mentions_", "").replace("_before", "")
            categories.append(cat)

    categories = sorted(categories)

    print(f"Total users: {total_users}")
    print(f"AI users: {num_ai_users}")
    print(f"Percentage AI users: {percent_ai:.2f}%\n")

    print(f"Mean BEFORE: {mean_before:.4f}")
    print(f"Mean AFTER:  {mean_after:.4f}")
    print(f"Median BEFORE: {median_before:.4f}")
    print(f"Median AFTER:  {median_after:.4f}\n")

    print(f"Median first AI mention: {median_first_seen}")
    print(f"Earliest AI mention:     {earliest}")
    print(f"Latest AI mention:       {latest}\n")

    print("Category Usage (before vs after vs total users)\n")

    category_summary = []
    category_user_counts = {}

    for cat in categories:

        before_col = f"mentions_{cat}_before"
        after_col = f"mentions_{cat}_after"
        total_col = f"mentions_{cat}"

        before_mask = ai_users[before_col] > 0 if before_col in ai_users else pd.Series(False, index=ai_users.index)
        after_mask = ai_users[after_col] > 0 if after_col in ai_users else pd.Series(False, index=ai_users.index)

        before_users = before_mask.sum()
        after_users = after_mask.sum()
        both_users = (before_mask & after_mask).sum()
        total_users_cat = (ai_users[total_col] > 0).sum() if total_col in ai_users else 0

        category_summary.append({
            "category": cat,
            "before_users": before_users,
            "after_users": after_users,
            "both_users": both_users,
            "total_users": total_users_cat
        })

        category_user_counts[cat] = total_users_cat

        print(f"{cat.upper()}:")
        print(f" before users: {before_users}")
        print(f" after users:  {after_users}")
        print(f" both users:   {both_users}")
        print(f" total users:  {total_users_cat}\n")

    summary = pd.DataFrame([{
        "total_users": total_users,
        "ai_users": num_ai_users,
        "percent_ai": percent_ai,
        "mean_before": mean_before,
        "mean_after": mean_after,
        "median_before": median_before,
        "median_after": median_after,
        "median_first_seen": median_first_seen,
        "earliest_first_seen": earliest,
        "latest_first_seen": latest
    }])

    summary.to_csv("non_disabled_ai_usage_summary.csv", index=False)

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

    def make_autopct(values, threshold=4):
        def autopct(pct):
            return f"{pct:.1f}%" if pct >= threshold else ""
        return autopct
    
    sorted_categories = sorted(category_user_counts.items(), key=lambda x: x[1], reverse=True)
    labels = [item[0] for item in sorted_categories]
    sizes = [item[1] for item in sorted_categories]
    total = sum(sizes)

    legend_labels = [f"{label}: {size} ({size/total:.1%})" for label, size in zip(labels, sizes)]
    plt.figure(figsize=(10,10))
    wedges, _, autotexts = plt.pie(sizes, startangle=90, colors=colors[:len(labels)], autopct=make_autopct(sizes), pctdistance=0.75, textprops={"color": "black"}, wedgeprops={"alpha": 1})
    plt.legend(wedges, legend_labels, title="AI Tool Categories", loc="center left", bbox_to_anchor=(1, 0.5))
    plt.title("AI Tool Usage Distribution (by unique users)")
    plt.tight_layout()
    plt.savefig("non_disabled_ai_tool_usage_distribution_pie_chart.png", dpi=300, bbox_inches="tight", pad_inches=0.2)
    plt.show()

    mention_cols = [col for col in df.columns if col.startswith("mentions_")]
    df["mentioned_ai"] = df[mention_cols].sum(axis=1) > 0
    mentioned_ai_users = df["mentioned_ai"].sum()
    not_mentioned_ai_users = len(df) - mentioned_ai_users
    sizes = [mentioned_ai_users, not_mentioned_ai_users]
    labels = [f"Mentioned AI: {mentioned_ai_users}", f"Did Not Mention AI: {not_mentioned_ai_users}"]
    total = sum(sizes)
    legend_labels = [f"{label}: {size} ({size/total:.1%})" for label, size in zip(labels, sizes)]
    plt.figure(figsize=(10, 10))
    wedges, _, autotexts =plt.pie(sizes, startangle=90, colors=[colors[4], colors[2]], autopct=make_autopct(sizes, threshold=3), pctdistance=0.75, textprops={"color": "black"}, wedgeprops={"alpha": 1})
    plt.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0.5))
    plt.title("Users Mentioning AI Tools Usage in Commit Messages vs Not")
    plt.tight_layout()
    plt.savefig("non_disabled_mentioned_ai_usage_pie_chart.png", dpi=300, bbox_inches="tight", pad_inches=0.2)
    plt.show()

    pd.DataFrame(category_summary).to_csv("non_disabled_ai_category_usage_summary.csv", index=False)

if __name__ == "__main__":
    main()