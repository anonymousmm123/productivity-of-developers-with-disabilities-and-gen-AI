import pandas as pd
import numpy as np
from scipy.stats import wilcoxon, kruskal, mannwhitneyu
from statsmodels.stats.multitest import multipletests
import matplotlib.pyplot as plt
import seaborn as sns

df_physical = pd.read_csv("github_users_physical.csv")
df_visual = pd.read_csv("github_users_visual.csv")
df_non_physical = pd.read_csv("github_users_non_physical.csv")
df_disabled = pd.read_csv("github_users_disabled.csv")
df_non_disabled = pd.read_csv("github_users_non_disabled.csv")
for df in [df_physical, df_visual, df_non_physical, df_disabled, df_non_disabled]:
    df["delta_commits"] = df["commits_after"] - df["commits_before"]
    df["delta_lines"] = df["net_lines_after"] - df["net_lines_before"]
    df["delta_acceptance_rate"] = df["acceptance_rate_after"] - df["acceptance_rate_before"]

df_all = pd.concat([df_physical, df_visual, df_non_physical, df_disabled, df_non_disabled]).drop_duplicates()

#effect size
def wilcoxon_effect_size(statistic, n):
    mean = n * (n + 1) / 4
    std = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    z = (statistic - mean) / std
    return z / np.sqrt(n)

def cliff_delta(x, y):
    n_x = len(x)
    n_y = len(y)
    greater = sum(i > j for i in x for j in y)
    lesser = sum(i < j for i in x for j in y)
    return (greater - lesser) / (n_x * n_y)

#within keyword change
results_within = []

disabled_only_df = pd.concat([df_physical, df_visual, df_non_physical, df_disabled]).drop_duplicates()

for keyword in disabled_only_df["keyword"].unique():
    subset = disabled_only_df[disabled_only_df["keyword"] == keyword]

    if len(subset) < 10:
        continue
    
    for var in ["commits", "net_lines"]:
        before = subset[f"{var}_before"]
        after = subset[f"{var}_after"]

        if np.all(before == after):
            continue

        stat, p = wilcoxon(before, after)
        effect_size = wilcoxon_effect_size(stat, len(subset))
        results_within.append({ "keyword": keyword, "variable": var, "p_value": p, "effect_size": effect_size, "median_change": np.median(after - before) })

    acc_subset = subset[(subset["acceptance_rate_before"] != 0) & (subset["acceptance_rate_after"] != 0)].copy()
    if len(acc_subset) >= 10:
        before = acc_subset["acceptance_rate_before"]
        after = acc_subset["acceptance_rate_after"]

        if not np.all(before == after):
            stat, p = wilcoxon(before, after)
            effect_size = wilcoxon_effect_size(stat, len(acc_subset))
            results_within.append({ "keyword": keyword, "variable": "acceptance_rate", "p_value": p, "effect_size": effect_size, "median_change": np.median(after) - np.median(before) })

for var in ["commits", "net_lines"]:
    before = df_non_disabled[f"{var}_before"]
    after = df_non_disabled[f"{var}_after"]

    if not np.all(before == after):
        stat, p = wilcoxon(before, after)
        effect_size = wilcoxon_effect_size(stat, len(df_non_disabled))
        results_within.append({ "keyword": "non-disabled-overall", "variable": var, "p_value": p, "effect_size": effect_size, "median_change": np.median(after - before) })

acc_subset = df_non_disabled[
    (df_non_disabled["acceptance_rate_before"] != 0) &
    (df_non_disabled["acceptance_rate_after"] != 0)
].copy()

if len(acc_subset) >= 10:
    before = acc_subset["acceptance_rate_before"]
    after = acc_subset["acceptance_rate_after"]

    if not np.all(before == after):
        stat, p = wilcoxon(before, after)
        effect_size = wilcoxon_effect_size(stat, len(acc_subset))

        results_within.append({"keyword": "non-disabled-overall", "variable": "acceptance_rate", "p_value": p, "effect_size": effect_size, "median_change": np.median(after) - np.median(before)})

results_within_df = pd.DataFrame(results_within)
within_correction = multipletests(results_within_df["p_value"], method="fdr_bh")
results_within_df["p_value_corrected"] = within_correction[1]
results_within_df.to_csv("within_group_results.csv", index=False)
print(results_within_df)

category_datasets = {
    "physical": df_physical,
    "visual": df_visual,
    "non-physical": df_non_physical,
    "disabled": df_disabled,
    "non-disabled": df_non_disabled
}

subtype_datasets = {
    "physical": df_physical,
    "visual": df_visual,
    "non-physical": df_non_physical,
    "disabled": df_disabled
}

#between category change(kruskal-wallis)
for var in ["delta_commits", "delta_lines", "delta_acceptance_rate"]:
    groups = []
    for name in category_datasets:
        if var == "delta_acceptance_rate":
            group = category_datasets[name][(category_datasets[name]["acceptance_rate_before"] != 0) & (category_datasets[name]["acceptance_rate_after"] != 0)][var].dropna()
        else:
            group = category_datasets[name][var].dropna()
        groups.append(group)

    stat, p = kruskal(*groups)
    print(f"Kruskal-Wallis for {var}: statistic={stat:.3f}, p-value={p:.5f}")

#pairwise category change(mann-whitney)
pairwise_results = []
keys = list(category_datasets.keys())

for var in ["delta_commits", "delta_lines", "delta_acceptance_rate"]:
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if var == "delta_acceptance_rate":
                group1 = category_datasets[keys[i]][(category_datasets[keys[i]]["acceptance_rate_before"] != 0) & (category_datasets[keys[i]]["acceptance_rate_after"] != 0)][var].dropna()
                group2 = category_datasets[keys[j]][(category_datasets[keys[j]]["acceptance_rate_before"] != 0) & (category_datasets[keys[j]]["acceptance_rate_after"] != 0)][var].dropna()
            else:
                group1 = category_datasets[keys[i]][var].dropna()
                group2 = category_datasets[keys[j]][var].dropna()

            stat, p = mannwhitneyu(group1, group2)
            effect_size = cliff_delta(group1.values, group2.values)
            pairwise_results.append({ "variable": var, "group1": keys[i], "group2": keys[j], "p_value": p, "effect_size": effect_size })

pairwise_results_df = pd.DataFrame(pairwise_results)
between_correction = multipletests(pairwise_results_df["p_value"], method="fdr_bh")
pairwise_results_df["p_value_corrected"] = between_correction[1]
pairwise_results_df.to_csv("pairwise_between_category_results.csv", index=False)
print(pairwise_results_df)

#subtype analysis(n>=10)
subtype_within_results = []
subtype_between_results = []

for name, subset in subtype_datasets.items():
    keyword_counts = subset["keyword"].value_counts()
    valid_keywords = keyword_counts[keyword_counts >= 10].index

    sub_df = subset[subset["keyword"].isin(valid_keywords)]

    for keyword, g in sub_df.groupby("keyword"):
        for var in ["commits", "net_lines"]:
            before = g[f"{var}_before"]
            after = g[f"{var}_after"]

            if np.all(before == after):
                continue

            stat, p = wilcoxon(before, after)
            effect_size = wilcoxon_effect_size(stat, len(g))
            subtype_within_results.append({ "category": name, "keyword": keyword, "variable": var, "p_value": p, "effect_size": effect_size, "median_change": np.median(after - before), "wilcoxon": stat})

        acc_g = g[(g["acceptance_rate_before"] != 0) & (g["acceptance_rate_after"] != 0)].copy()
        print(name, keyword, len(acc_g))
        if len(acc_g) >= 10:
            before = acc_g["acceptance_rate_before"]
            after = acc_g["acceptance_rate_after"]

            if not np.all(before == after):
                stat, p = wilcoxon(before, after)
                effect_size = wilcoxon_effect_size(stat, len(acc_g))
                subtype_within_results.append({ "category": name, "keyword": keyword, "variable": "acceptance_rate", "p_value": p, "effect_size": effect_size, "median_change": np.median(after) - np.median(before), "wilcoxon": stat })

    # Kruskal-Wallis across subtypes    
    for var in ["delta_commits", "delta_lines", "delta_acceptance_rate"]:
         groups_data = []

         for _, g in sub_df.groupby("keyword"):
             if var == "delta_acceptance_rate":
                 group = g[(g["acceptance_rate_before"] != 0) & (g["acceptance_rate_after"] != 0)][var].dropna()
             else:
                 group = g[var].dropna()

             if len(group) > 0:
                 groups_data.append(group)

         if len(groups_data) > 1:
            stat, p = kruskal(*groups_data)
            subtype_between_results.append({ "category": name, "variable": var, "statistic": stat, "p_value": p })

subtype_within_df = pd.DataFrame(subtype_within_results)
subtype_between_df = pd.DataFrame(subtype_between_results)

if not subtype_within_df.empty:
    subtype_within_df["p_value_corrected"] = multipletests(subtype_within_df["p_value"], method="fdr_bh")[1]

if not subtype_between_df.empty:
    subtype_between_df["p_value_corrected"] = multipletests(subtype_between_df["p_value"], method="fdr_bh")[1]

subtype_within_df.to_csv("subtype_within_results.csv", index=False)
subtype_between_df.to_csv("subtype_between_results.csv", index=False)

sns.set_theme(style="whitegrid")

plot_df = pd.concat([df_physical.assign(category="physical"), df_visual.assign(category="visual"), df_non_physical.assign(category="non-physical"), df_disabled.assign(category="disabled"), df_non_disabled.assign(category="non-disabled")], ignore_index=True)

plt.figure()
sns.boxplot(data=plot_df, x="category", y="delta_commits")
sns.stripplot(data=plot_df, x="category", y="delta_commits", color="black", alpha=0.3)
plt.title("Delta Commits by Category")
plt.xticks(rotation=45)
plt.show()

plt.figure()
sns.boxplot(data=plot_df, x="category", y="delta_lines")
sns.stripplot(data=plot_df, x="category", y="delta_lines", color="black", alpha=0.3)
plt.title("Delta Lines by Category")
plt.xticks(rotation=45)
plt.show()

acceptance_plot_df = plot_df[(plot_df["acceptance_rate_before"] != 0) & (plot_df["acceptance_rate_after"] != 0)].copy()

plt.figure()
sns.boxplot(data=acceptance_plot_df, x="category", y="delta_acceptance_rate")
sns.stripplot(data=acceptance_plot_df, x="category", y="delta_acceptance_rate", color="black", alpha=0.3)
plt.title("Delta Acceptance Rate by Category")
plt.xticks(rotation=45)
plt.show()

sizes = [
    len(df_physical),
    len(df_visual),
    len(df_non_physical),
    len(df_disabled),
    len(df_non_disabled)
]

labels = ["physical", "visual", "non-physical", "disabled", "non-disabled"]

plt.figure(figsize=(10,10))
colors = [
        "#FF8C42",
        "#FFD166",
        "#F15BB5",
        "#00F5D4",
        "#EF476F"
    ]
wedges, texts, autotexts = plt.pie(
    sizes,
    autopct="%1.1f%%",
    startangle=90,
    colors=colors[:len(sizes)]
)

legend_labels = [f"physical {len(df_physical)}", f"visual {len(df_visual)}", f"non-physical {len(df_non_physical)}", f"disabled {len(df_disabled)}", f"non-disabled {len(df_non_disabled)}"]
total_users = plot_df["username"].nunique()

plt.legend(wedges, legend_labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0.5))
plt.title(f"Distribution of Categories (Total n = {total_users})")
plt.tight_layout()
plt.savefig("category_distribution_pie_chart.png", dpi=300, bbox_inches="tight", pad_inches=0.2)
plt.show()

#survey visuals
def filter_acceptance(df):
    return df[
        (df["acceptance_rate_before"] != 0) &
        (df["acceptance_rate_after"] != 0)
    ].copy()


comparison_groups = {
    "Physical": (df_physical.copy(), df_non_disabled.copy()),
    "Visual": (df_visual.copy(), df_non_disabled.copy()),
    "Non-Physical": (df_non_physical.copy(), df_non_disabled.copy()),
    "Disabled": (df_disabled.copy(), df_non_disabled.copy())
}

metric_info = [
    ("delta_commits", "Commits"),
    ("delta_lines", "Net Lines"),
    ("delta_acceptance_rate", "Acceptance Rate (%)")
]

for comparison_name, (target_df, control_df) in comparison_groups.items():

    target_df = target_df.copy()
    control_df = control_df.copy()

    target_df["group"] = comparison_name
    control_df["group"] = "Non-disabled"

    combined = pd.concat([target_df, control_df], ignore_index=True)

    combined["delta_acceptance_rate"] = combined["delta_acceptance_rate"] * 100

    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(10, 12))

    fig.suptitle(f"{comparison_name} vs Non-disabled", fontsize=16)

    for idx, (metric, metric_label) in enumerate(metric_info):

        ax = axes[idx]

        rows = []

        for group in [comparison_name, "Non-disabled"]:

            data = combined[combined["group"] == group]

            if metric == "delta_acceptance_rate":
                data = filter_acceptance(data)

            values = data[metric].dropna()

            if len(values) == 0:
                median = 0
                q1 = 0
                q3 = 0
            else:
                median = values.median()
                q1 = values.quantile(0.25)
                q3 = values.quantile(0.75)

            rows.append({
                "Group": group,
                "Median": median,
                "LowerError": median - q1,
                "UpperError": q3 - median
            })

        plot_data = pd.DataFrame(rows)

        x_positions = [0, 1]
        colors = ["#F15BB5", "#FFB3D9"]

        for i, row in plot_data.iterrows():

            median = row["Median"]
            lower = row["LowerError"]
            upper = row["UpperError"]

            ax.bar(
                x_positions[i],
                median,
                width=0.6,
                color=colors[i],
                edgecolor="black",
                linewidth=1.2,
                alpha=0.9
            )

            ax.errorbar(
                x=x_positions[i],
                y=median,
                yerr=[[lower], [upper]],
                fmt='none',
                capsize=8,
                color='black',
                linewidth=1.5
            )

            ax.text(
                x_positions[i],
                median,
                f"{median:.2f}",
                ha='center',
                va='bottom'
            )

        ax.set_xticks(x_positions)
        ax.set_xticklabels(plot_data["Group"])

        medians = plot_data["Median"].values
        center = np.mean(medians)

        spread = np.max(np.abs(medians - center))
        if spread == 0:
            spread = 1

        zoom_factor = 4 

        y_min = center - spread * zoom_factor
        y_max = center + spread * zoom_factor

        ax.set_ylim(y_min, y_max)

        if y_min < 0 < y_max:
            ax.axhline(y=0, linestyle='--', alpha=0.4)

        ax.set_title(metric_label)

        if metric_label == "Acceptance Rate (%)":
            ax.set_ylabel("% change")
        else:
            ax.set_ylabel("Median change")

    plt.tight_layout()

    filename = (
        comparison_name.lower()
        .replace("-", "_")
        .replace(" ", "_")
        + "_vs_non_disabled_subplots.png"
    )

    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()