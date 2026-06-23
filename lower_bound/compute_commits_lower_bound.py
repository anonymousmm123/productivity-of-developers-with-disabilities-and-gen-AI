import pandas as pd
import numpy as np

input_file = "../check_regex/github_users_regex_checked.csv"
output_file = "github_users_activity_filtered.csv"

def main():
    df = pd.read_csv(input_file)

    #removed users which have no commits in either period
    df_active = df[(df["commits_before"] > 0) | df["commits_after"] >0]

    before_lower_bound = int(np.percentile(df_active[df_active["commits_before"] > 0]["commits_before"], 25))
    after_lower_bound = int(np.percentile(df_active[df_active["commits_after"] > 0]["commits_after"], 25))

    print("before_commits lower bound:", before_lower_bound)
    print("after_commits lower bound", after_lower_bound)

    filtered = df[
        (df["commits_before"] >= before_lower_bound) & 
        (df["commits_after"] >= after_lower_bound)]
    filtered.to_csv(output_file, index=False)

if __name__ == "__main__":
    main()