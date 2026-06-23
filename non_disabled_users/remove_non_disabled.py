import pandas as pd

non_disabled = "non_disabled_users.csv"
final_dataset= "../clean_dataset/final_dataset.csv"
disabled_output = "disabled_final_dataset.csv"
non_disabled_output = "non_disabled_final_dataset.csv"


non_disabled_df = pd.read_csv(non_disabled)
final_df = pd.read_csv(final_dataset)

user_column = "username"
non_disabled_users = set(non_disabled_df[user_column])
non_disabled_filtered_df = final_df[final_df[user_column].isin(non_disabled_users)]
non_disabled_filtered_df.to_csv(non_disabled_output, index=False)

filtered_df = final_df[~final_df[user_column].isin(non_disabled_users)]
filtered_df.to_csv(disabled_output, index=False)