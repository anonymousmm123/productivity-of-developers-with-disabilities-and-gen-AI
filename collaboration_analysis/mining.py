import os
import requests
import pandas as pd
import time
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
url = "https://api.github.com/graphql"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

input_file = "../ai_use/github_users_with_ai_signals.csv"
output_file = "user_collaboration_types.csv"


def run_query(query, variables, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(
                url,
                json={"query": query, "variables": variables},
                headers=headers
            )

            if r.status_code == 200:
                data = r.json()

                if "errors" in data:
                    print(f"GraphQL error (attempt {attempt+1}): {data['errors']}")
                    time.sleep(2)
                    continue

                return data
            else:
                print(f"HTTP error {r.status_code}: {r.text}")

        except Exception as e:
            print(f"Request exception: {e}")

        time.sleep(2)

    return None

collab_query = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    repositories(first: 50, after: $cursor, ownerAffiliations: OWNER, privacy: PUBLIC) {
      pageInfo { hasNextPage endCursor }
      nodes {
        name
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 100) {
                totalCount
                nodes {
                  author {
                    user { login }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


def get_collaboration_type(login):
    cursor = None
    all_repo_types = set()

    while True:
        result = run_query(collab_query, {"login": login, "cursor": cursor})

        if result is None:
            print(f"Failed for {login}")
            return "error"

        user = result["data"]["user"]
        if user is None:
            return "not_found"

        repos = user["repositories"]["nodes"]

        for r in repos:
            try:
                branch = r.get("defaultBranchRef")

                if not branch or not branch["target"]:
                    continue

                history = branch["target"].get("history")
                if not history:
                    continue

                commits = history["nodes"]
                total_commits = history["totalCount"]

                if total_commits < 5:
                    continue

                authors = set()

                for c in commits:
                    author = c["author"]["user"]
                    if author and author["login"]:
                        authors.add(author["login"])

                if len(authors) == 0:
                    continue

                elif len(authors) == 1:
                    all_repo_types.add("individual")

                else:
                    all_repo_types.add("collaborative")

            except Exception as e:
                print(f"Repo error for {login}/{r.get('name')}: {e}")
                continue

        page_info = user["repositories"]["pageInfo"]

        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]

    if not all_repo_types:
        return "no_repos"

    elif len(all_repo_types) == 1:
        return all_repo_types.pop()

    else:
        return "mixed"


def main():
    df = pd.read_csv(input_file)
    usernames = df["username"].dropna().unique()

    results = []

    for i, user in enumerate(usernames):
        print(f"[{i+1}/{len(usernames)}] Processing {user}")

        collab_type = get_collaboration_type(user)

        results.append({
            "username": user,
            "collaboration_type": collab_type
        })

        pd.DataFrame(results).to_csv(output_file, index=False)

        time.sleep(0.5)

    result_df = pd.DataFrame(results)

    stats = result_df["collaboration_type"].value_counts()
    stats.to_csv("collab_stats.csv")

    print("\nFinal stats:\n", stats)


if __name__ == "__main__":
    main()