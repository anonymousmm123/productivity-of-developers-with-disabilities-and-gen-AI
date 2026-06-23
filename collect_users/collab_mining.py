import os
import random
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
before_end = "2024-12-17T23:59:59Z"

after_start = "2024-12-18T00:00:00Z"
after_end = "2025-12-17T23:59:59Z"

min_commits_before = 7
min_commits_after = 5

def run_query(query, variables):

    r = requests.post(
        URL,
        json={"query": query, "variables": variables},
        headers=headers
    )

    if r.status_code != 200:
        raise Exception(r.text)

    return r.json()

repos_query = """
query($login:String!) {
  user(login:$login) {

    repositories(
      first:100,
      affiliations:[OWNER, COLLABORATOR, ORGANIZATION_MEMBER]
      ownerAffiliations:[OWNER, COLLABORATOR, ORGANIZATION_MEMBER]
      isFork:false
      privacy:PUBLIC
      orderBy:{field:STARGAZERS,direction:DESC}
    ) {

      nodes {
        name
        nameWithOwner

        collaborators(first:20) {
          nodes {
            login
          }
        }
      }
    }
  }
}
"""

def get_collaborative_repos(username):

    data = run_query(repos_query, {"login": username})
    user = data["data"]["user"]
    if not user:
        return []
    
    repos = user["repositories"]["nodes"]
    collaborative_repos = []    
    for repo in repos:
        collaborators = repo["collaborators"]["nodes"]
        
        collaborators_logins = [c["login"] for c in collaborators if c["login"].lower() != username.lower()]

        if len(collaborators_logins) == 0:
            continue

        collaborative_repos.append({
            "repo": repo["nameWithOwner"],
            "collaborators": collaborators_logins
        })

    return collaborative_repos

activity_query = """
query($login:String!) {

  user(login:$login) {

    repositoriesContributedTo(
      first:100,
      contributionTypes:[COMMIT]
      includeUserRepositories:true
    ) {

      nodes {

        nameWithOwner

        defaultBranchRef {
          target {

            ... on Commit {

              before: history(
                since:"%s",
                until:"%s",
                author:{id:null}
              ) {
                totalCount
                nodes {
                  author {
                    user {
                      login
                    }
                  }

                  additions
                  deletions
                }
              }

              after: history(
                since:"%s",
                until:"%s",
                author:{id:null}
              ) {
                totalCount
                nodes {
                  author {
                    user {
                      login
                    }
                  }

                  additions
                  deletions
                }
              }

            }
          }
        }
      }
    }
  }
}
""" % (before_start, before_end, after_start, after_end)

def get_activity(username):
    
    result = run_query(activity_query, {"login": username})
    user = result["data"]["user"]
    if not user:
        return None
    
    repos = user["repositoriesContributedTo"]["nodes"]

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
        if not target:
            continue
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

    return {
        "commits_before": commits_before,
        "commits_after": commits_after,
        "net_lines_before": net_lines_before,
        "net_lines_after": net_lines_after,
        "lines_added_before": lines_added_before,
        "lines_removed_before": lines_removed_before,
        "lines_added_after": lines_added_after,
        "lines_removed_after": lines_removed_after
    }

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

def lower_bound(activity):

    return (activity["commits_before"] >= min_commits_before and  activity["commits_after"] >= min_commits_after)

def mached_collaboratos(seed_username):
    repos = get_collaborative_repos(seed_username)
    random.shuffle(repos)
    checked = set()

    for repo in repos:
        collaborators = repo["collaborators"]
        random.shuffle(collaborators)

        for collaborator in collaborators:
            if collaborator.lower() == seed_username.lower():
                continue

            if collaborator.lower() in checked:
                continue

            checked.add(collaborator.lower())

            print(f"Checking collaborator {collaborator} from repo {repo['repo']}")

            try:
                activity = get_activity(collaborator)

                if not activity:
                    continue

                if not lower_bound(activity):
                    print(f"Collaborator {collaborator} does not meet the activity criteria")
                    continue

                print(f"Collaborator {collaborator} meets the activity criteria")
                return collaborator, activity
            
            except Exception as e:
                print(f"Error checking collaborator {collaborator}: {e}")
                continue

            time.sleep(0.5)

    return None, None

def main():
    input = "../collaboration_analysis/user_collaboration_types.csv"
    output = "matched_collaborators.csv"

    df = pd.read_csv(input)
    
    rows = []

    for index, row in df.iterrows():
        username = row["username"]
        collab_type = row["collaboration_type"]

        if str(collab_type).lower() != "collaborative":
            continue

        print(f"Processing {index+1}/{len(df)}: {username})")

        try:
            collaborator, collaborator_activity = mached_collaboratos(username)

            if not collaborator:
                print(f"No suitable collaborator found for {username}")
                continue

            collaborator_prs = get_pr_activity(collaborator)

            out = {
                "username": username,
                "collaborator": collaborator,
                "commits_before": collaborator_activity["commits_before"],
                "commits_after": collaborator_activity["commits_after"],
                "net_lines_before": collaborator_activity["net_lines_before"],
                "net_lines_after": collaborator_activity["net_lines_after"],
                "lines_added_before": collaborator_activity["lines_added_before"],
                "lines_removed_before": collaborator_activity["lines_removed_before"],
                "lines_added_after": collaborator_activity["lines_added_after"],
                "lines_removed_after": collaborator_activity["lines_removed_after"],
                "pr_count_before": collaborator_prs["pr_count_before"],
                "pr_count_after": collaborator_prs["pr_count_after"],
                "merged_pr_count_before": collaborator_prs["merged_pr_count_before"],
                "merged_pr_count_after": collaborator_prs["merged_pr_count_after"],
                "acceptance_rate_before": collaborator_prs["acceptance_rate_before"],
                "acceptance_rate_after": collaborator_prs["acceptance_rate_after"]
                }
            
            rows.append(out)
            pd.DataFrame(rows).to_csv(output, index=False)
            time.sleep(0.5)

        except Exception as e:
            print(f"Error processing user {username}: {e}")
            continue

if __name__ == "__main__":
    main()

        