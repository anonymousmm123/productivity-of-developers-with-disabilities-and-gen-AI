import pandas as pd

input_file = "../check_developers/github_developers.csv"
output_file = "removed_add_users.csv"

def main():
    df = pd.read_csv(input_file)

    filtered_df = df[df["keyword"] != "add"]
    filtered_df.to_csv(output_file, index=False)

if __name__ == "__main__":
    main()