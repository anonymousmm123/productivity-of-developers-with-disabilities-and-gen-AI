import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

input_file = "../ai_use/github_users_with_ai_signals.csv"

def classify_activity(commits):
    if commits < 25:
        return "<25"
    elif commits <=100:
        return "25-100"
    else:
        return ">100"
    
def main():
    df = pd.read_csv(input_file)

    df["activity_before"] = df["commits_before"].apply(classify_activity)
    df["activity_after"] = df["commits_after"].apply(classify_activity)
    
    categories = ["<25", "25-100", ">100"]
    y = np.arange(len(categories))

    for keyword, group in df.groupby("keyword"):
        before_counts = group["activity_before"].value_counts().reindex(categories, fill_value=0)
        after_counts = group["activity_after"].value_counts().reindex(categories, fill_value=0)

        print(f"\n {keyword} before \n", before_counts)
        print(f"\n {keyword} after \n", after_counts)

        before_counts.to_csv(f"before_counts_{keyword}.csv")
        after_counts.to_csv(f"after_counts_{keyword}.csv")

        plt.figure(figsize=(8,5))
        plt.barh(y, before_counts.values,color='red', alpha=0.5, label='Before')
        plt.barh(y, after_counts.values, color='yellow', alpha=0.5, label='After')
        plt.yticks(y, categories)
        plt.ylabel("Activity Class")
        plt.xlabel("No. of users")
        plt.title(f"{keyword} User Distribution by Activity Level (Before vs After)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"{keyword}_before_after_overlay.png")
        plt.show()


if __name__ == "__main__":
    main()