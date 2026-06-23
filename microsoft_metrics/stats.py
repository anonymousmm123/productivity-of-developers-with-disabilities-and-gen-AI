import pandas as pd
import numpy as np
from scipy.stats import wilcoxon
from statsmodels.stats.multitest import multipletests

df_physical = pd.read_csv("../stats/github_users_physical.csv")
df_visual = pd.read_csv("../stats/github_users_visual.csv")
df_non_physical = pd.read_csv("../stats/github_users_non_physical.csv")
df_disabled = pd.read_csv("../stats/github_users_disabled.csv")
df_non_disabled = pd.read_csv("../stats/github_users_non_disabled.csv")


def wilcoxon_effect_size(statistic, n):
    mean = n * (n + 1) / 4
    std = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    z = (statistic - mean) / std
    return z / np.sqrt(n)


datasets = {
    "physical": df_physical,
    "visual": df_visual,
    "non_physical": df_non_physical,
    "disabled": df_disabled,
    "non_disabled": df_non_disabled
}

results = []

for name, df in datasets.items():

    metrics = [
        ("commits_before", "commits_after", "commits"),
        ("total_prs_before", "total_prs_after", "pull_requests")
    ]

    for before_col, after_col, metric_name in metrics:

        before = df[before_col]
        after = df[after_col]

        valid = before.notna() & after.notna()

        if metric_name == "pull_requests":
            valid = valid & (before >0 ) & (after > 0)

        before = before[valid]
        after = after[valid]

        if len(before) < 2:
            continue

        if np.all(before == after):
            continue

        stat, p = wilcoxon(before, after)

        effect_size = wilcoxon_effect_size(
            stat,
            len(before)
        )

        median_before = np.median(before)
        median_after = np.median(after)

        median_change = np.median(after - before)

        results.append({
            "group": name,
            "metric": metric_name,
            "n": len(before),
            "median_before": median_before,
            "median_after": median_after,
            "median_change": median_change,
            "wilcoxon_statistic": stat,
            "effect_size_r": effect_size,
            "p_value": p
        })

results_df = pd.DataFrame(results)

if not results_df.empty:

    corrected = multipletests(
        results_df["p_value"],
        method="fdr_bh"
    )

    results_df["p_value_corrected"] = corrected[1]

results_df.to_csv(
    "commits_prs_before_after_results.csv",
    index=False
)

print(results_df)