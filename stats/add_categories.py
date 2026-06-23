import pandas as pd

input_file = "../ai_use/github_users_with_ai_signals.csv"
df = pd.read_csv(input_file)

physical_keywords = {"deaf", "disabled"}
visual_keywords = {"visually impaired", "blind", "legally blind"}

def categorize(keyword):
    if pd.isna(keyword):
        return ["non-physical"]
    
    k = keyword.lower()
    categories = []

    is_physical = "deaf" in k or "disabled" in k
    is_visual = any(v in k for v in visual_keywords)
    is_disabled = "disabled" in k

    if is_physical:
        categories.append("physical")
    if is_visual:
        categories.append("visual")
    if is_disabled or (not is_physical and not is_visual):
        categories.append("non-physical")
    if is_disabled:
        categories.append("disabled")

    return categories

df["category"] = df["keyword"].apply(categorize)
df = df.explode("category")

cols = list(df.columns)
keyword_index = cols.index("keyword")
cols.insert(keyword_index + 1, cols.pop(cols.index("category")))
df = df[cols]

output_file = "github_users_with_ai_signals_with_category.csv"
df.to_csv(output_file, index=False)
df_physical = df[df["category"] == "physical"]
df_visual = df[df["category"] == "visual"]
df_non_physical = df[df["category"] == "non-physical"]
df_disabled = df[df["category"] == "disabled"]
df_physical.to_csv("github_users_physical.csv", index=False)
df_visual.to_csv("github_users_visual.csv", index=False)
df_non_physical.to_csv("github_users_non_physical.csv", index=False)
df_disabled.to_csv("github_users_disabled.csv", index=False)

non_disabled_input = "../ai_use/non_disabled_github_users_with_ai_signals.csv"
df_non_disabled = pd.read_csv(non_disabled_input)
df_non_disabled["category"] = "non-disabled"
cols = list(df_non_disabled.columns)

if "keyword" in cols:
    keyword_index = cols.index("keyword")
    cols.insert(keyword_index + 1, cols.pop(cols.index("category")))
else:
    cols.insert(1, cols.pop(cols.index("category")))

df_non_disabled = df_non_disabled[cols]
df_non_disabled.to_csv("github_users_non_disabled.csv", index=False)