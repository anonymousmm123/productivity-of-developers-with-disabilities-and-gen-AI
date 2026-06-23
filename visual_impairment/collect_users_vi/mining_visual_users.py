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

keywords = ["visually impaired", "blind", "low vision", "partially blind", "partially sighted", "legally blind", "sight loss", "blv", "bvi"]

before_start = "2023-12-18T00:00:00Z"
before_end = "2024-12-17T23:59:59Z"

after_start = "2024-12-18T00:00:00Z"
after_end = "2025-12-17T23:59:59Z"


def run_query(query, variables):

    r = requests.post(
        URL,
        json={"query": query, "variables": variables},
        headers=headers
    )

    if r.status_code != 200:
        raise Exception(r.text)

    return r.json()

search_query = """
query ($query:String!, $cursor:String) {
  search(query:$query, type: USER, first:100, after:$cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on User {
        login
      }
    }
  }
}
"""


def search_users(query):

    users = []
    cursor = None

    while True:

        result = run_query(search_query, {
            "query": query,
            "cursor": cursor
        })

        nodes = result["data"]["search"]["nodes"]

        for n in nodes:
            users.append(n["login"])

        page = result["data"]["search"]["pageInfo"]

        if not page["hasNextPage"]:
            break

        cursor = page["endCursor"]

        time.sleep(0.5)

    return users

activity_query = """
query ($login:String!) {
  user(login:$login) {

    repositories(first:100, ownerAffiliations:OWNER) {
      nodes {

        defaultBranchRef {
          target {
            ... on Commit {

              before: history(since:"%s", until:"%s") {
                nodes {
                    additions
                    deletions
                }
                totalCount
              }

              after: history(since:"%s", until:"%s") {
                nodes {
                    additions
                    deletions
                }
                totalCount
              }

            }
          }
        }

      }
    }

  }
}
""" % (before_start, before_end, after_start, after_end)


def get_activity(login):

    result = run_query(activity_query, {"login": login})
    repos = result["data"]["user"]["repositories"]["nodes"]

    commits_before = 0
    commits_after = 0

    net_lines_before = 0
    net_lines_after = 0

    lines_added_before = 0
    lines_removed_before = 0
    lines_added_after = 0
    lines_removed_after = 0

    for r in repos:

        branch = r.get("defaultBranchRef")

        if not branch:
            continue

        target = branch["target"]
        commits_before += target["before"]["totalCount"]
        commits_after += target["after"]["totalCount"]

        for c in target["before"]["nodes"]:
            net_lines_before += c["additions"] + c["deletions"]
            lines_added_before += c["additions"]
            lines_removed_before += c["deletions"]

        for c in target["after"]["nodes"]:
            net_lines_after += c["additions"] + c["deletions"]
            lines_added_after += c["additions"]
            lines_removed_after += c["deletions"]

    return commits_before, commits_after, net_lines_before, net_lines_after, lines_added_before, lines_removed_before, lines_added_after, lines_removed_after


def main():

    users = {}

    follower_ranges = [
        "0..1","2..5","6..10","11..50","51..200","201..1000","1001..10000"
    ]

    for keyword in keywords:
        print("Looking for keyword:", keyword)
        
        for fr in follower_ranges:
            query = f'{keyword} in:bio type:user followers:{fr}'
            found = search_users(query)

            for u in found:
                users[u] = keyword

            print(keyword, fr, len(found))


    rows = []

    for u, keyword in users.items():
        print("Processing", u)

        try:
            commits_before, commits_after, net_lines_before, net_lines_after, lines_added_before, lines_removed_before, lines_added_after, lines_removed_after = get_activity(u)
        except:
            continue

        row = {
            "username": u,
            "keyword": keyword,
            "commits_before": commits_before,
            "commits_after": commits_after,
            "net_lines_before": net_lines_before,
            "net_lines_after": net_lines_after,
            "lines_added_before": lines_added_before,
            "lines_removed_before": lines_removed_before,
            "lines_added_after": lines_added_after,
            "lines_removed_after": lines_removed_after
        }

        rows.append(row)

        pd.DataFrame(rows).to_csv(
            "github_users_visually_impaired.csv",
            index=False
        )

        time.sleep(0.5)


if __name__ == "__main__":
    main()