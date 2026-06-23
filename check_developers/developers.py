import os
import pandas as pd
import requests
import time
from dotenv import load_dotenv

load_dotenv()

input_file = "../lower_bound/github_users_activity_filtered.csv"
output_file1 = "github_developers.csv"
output_file2 = "github_non_developers.csv"

TOKEN = os.getenv("GITHUB_TOKEN")
URL = "https://api.github.com/graphql"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

languages = {"Python", "JavaScript", "TypeScript", "Java", "C", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Kotlin", "Swift", "Scala", "Dart"}

query = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 20, ownerAffiliations: OWNER) {
      nodes {
        languages(first: 10) {
          nodes {
            name
          }
        }
      }
    }
  }
}
"""

def is_dev(username):
    variables = {"login": username}

    response = requests.post(
        URL,
        json={"query": query, "variables":variables},
        headers=headers
    )

    data = response.json()

    try:
        repos = data["data"]["user"]["repositories"]["nodes"]

        for repo in repos:
            for lang in repo["languages"]["nodes"]:
                if lang["name"] in languages:
                    return True
                
        return False
    except:
        return False
    
def main():
    df = pd.read_csv(input_file)
    developer_rows = []
    non_dev_rows = []

    usernames = df["username"].unique()

    for username in usernames:
        dev = is_dev(username)

        user_data = df[df["username"] == username]

        if dev:
            developer_rows.append(user_data)
        else:
            non_dev_rows.append(user_data)

        time.sleep(0.2)

    dev_df = pd.concat(developer_rows)
    dev_df.to_csv(output_file1, index=False)
    non_dev_df = pd.concat(non_dev_rows)
    non_dev_df.to_csv(output_file2, index=False)
    print("Developers:", len(dev_df))

if __name__ == "__main__":
    main()