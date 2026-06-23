import pandas as pd

input_file1 = "../remove_add/removed_add_users.csv"
input_file2 = "../visual_impairment/check_developers_vi/github_developers_vi.csv"
output_file = "final_dataset.csv"

def main():
    df1 = pd.read_csv(input_file1)
    df2 = pd.read_csv(input_file2)

    combined_df = pd.concat([df1, df2], ignore_index=True)
    combined_df.to_csv(output_file, index=False)

if __name__ == "__main__":
    main()