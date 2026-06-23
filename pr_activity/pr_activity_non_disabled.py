import os
import requests
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
URL = "https://api.github.com/graphql"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

before_start = "2023-12-18T00:00:00Z"
before_end   = "2024-12-17T23:59:59Z"

after_start  = "2024-12-18T00:00:00Z"
after_end    = "2025-12-17T23:59:59Z"

def run_query(query, variables):
    r = requests.post(
        URL,
        json={"query": query, "variables": variables},
        headers=headers
    )

    if r.status_code != 200:
        raise Exception(r.text)

    return r.json()

pr_count_query = """
query ($query:String!, $cursor:String) {
  search(query:$query, type: ISSUE, first:100, after:$cursor) {
    issueCount
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

def count_prs(search_string):
    result = run_query(pr_count_query, {
        "query": search_string,
        "cursor": None
    })

    data = result["data"]["search"]
    return data["issueCount"]

def get_pr_activity(username):
    before_total = f"is:pr author:{username} created:{before_start}..{before_end}"
    after_total = f"is:pr author:{username} created:{after_start}..{after_end}"
    before_query = f"is:pr is:merged author:{username} created:{before_start}..{before_end}"
    after_query  = f"is:pr is:merged author:{username} created:{after_start}..{after_end}"

    total_before = count_prs(before_total)
    total_after = count_prs(after_total)
    prs_before = count_prs(before_query)
    prs_after  = count_prs(after_query)

    acceptance_before = (prs_before / total_before) if total_before > 0 else 0
    acceptance_after = (prs_after / total_after) if total_after > 0 else 0

    return (prs_before, prs_after, total_before, total_after, acceptance_before, acceptance_after)


def main():

    input_path = "../non_disabled_users/non_disabled_final_dataset.csv"
    output_path = "non_disabled_github_users_with_prs.csv"

    df = pd.read_csv(input_path)

    columns = ["prs_merged_before", "prs_merged_after", "total_prs_before", "total_prs_after", "acceptance_rate_before", "acceptance_rate_after"]
    for col in columns:
        if col not in df.columns:
            df[col] = 0

    for i, row in df.iterrows():

        username = row["username"]

        print(f"Processing {i+1}/{len(df)}: {username}")

        try:
            (prs_before, prs_after, total_before, total_after, acceptance_before, acceptance_after) = get_pr_activity(username)

            df.at[i, "prs_merged_before"] = prs_before
            df.at[i, "prs_merged_after"] = prs_after
            df.at[i, "total_prs_before"] = total_before
            df.at[i, "total_prs_after"] = total_after
            df.at[i, "acceptance_rate_before"] = acceptance_before
            df.at[i, "acceptance_rate_after"] = acceptance_after

        except Exception as e:
            print("Error:", username, e)
            continue

        df.to_csv(output_path, index=False)

        time.sleep(0.5)

if __name__ == "__main__":
    main()
