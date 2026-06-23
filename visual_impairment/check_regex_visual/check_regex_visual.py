import os
import requests
import pandas as pd
import re
import time
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("GITHUB_TOKEN")
URL = "https://api.github.com/graphql"

input_file = "../collect_users_vi/github_users_visually_impaired.csv"
output_file = "github_users_vi_regex_checked.csv"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

keywords = ["visually impaired", "blind", "low vision", "partially blind", "partially sighted", "legally blind", "sight loss", "blv", "bvi"]

def keyword_valid(keyword, bio):
    if pd.isna(bio):
        return False
    
    pattern = r"\b" + re.escape(keyword) + r"\b"
    
    return bool(re.search(pattern, bio, re.IGNORECASE))

def run_query(query, variables):
    r = requests.post(
        URL,
        json={"query": query, "variables": variables},
        headers=headers
    )

    if r.status_code != 200:
        raise Exception(r.text)
    
    return r.json()

bio_query = """
query ($login:String!) {
    user(login:$login) {
        bio
    }
}
"""

def get_bio(login):
    result = run_query(bio_query, {"login": login})
    user = result["data"]["user"]

    if user is None:
        return None

    return user["bio"]

def main():

    df = pd.read_csv(input_file)
    cleaned_rows = []

    for _, row in df.iterrows():
        username = row["username"]
        keyword = row["keyword"]

        print("Checking:", username)
        
        try:
            bio = get_bio(username)
        except:
            continue

        if keyword_valid(keyword, bio):
            cleaned_rows.append(row)

        time.sleep(0.5)

    clean_df = pd.DataFrame(cleaned_rows)
    clean_df.to_csv(output_file, index=False)

if __name__ == "__main__":
    main()