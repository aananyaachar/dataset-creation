import pandas as pd

FILE_1 = "users_with_country_mer.csv"      
FILE_2 = "USER1.csv"  
OUTPUT = "merged.csv"

print("Loading files...")
df1 = pd.read_csv(FILE_1, encoding="utf-8")
df2 = pd.read_csv(FILE_2, encoding="utf-8")

df2.columns = df2.columns.str.strip().str.lower()

df2 = df2.loc[:, ~df2.columns.str.startswith("unnamed")]

print(f"   {FILE_1}: {len(df1)} rows (master)")
print(f"   {FILE_2}: {len(df2)} rows (patch)")

patch_map = {
    str(k).strip().lower(): v
    for k, v in df2.set_index("username")["country"].to_dict().items()
}

before_unknown = (df1["country"].astype(str).str.strip().str.lower() == "unknown").sum()
before_empty   = df1["country"].isna().sum()
print(f"\n Before update:")
print(f"   Unknown : {before_unknown}")
print(f"   Empty   : {before_empty}")


def update_country(row):
    current = str(row["country"]).strip().lower() if pd.notna(row["country"]) else ""
    if current in ("unknown", "", "nan"):
        key = str(row["username"]).strip().lower()
        return patch_map.get(key, row["country"])
    return row["country"]

df1["country"] = df1.apply(update_country, axis=1)

after_unknown = (df1["country"].astype(str).str.strip().str.lower() == "unknown").sum()
after_empty   = df1["country"].isna().sum()
filled = (before_unknown + before_empty) - (after_unknown + after_empty)

print(f"\nAfter update:")
print(f"   Unknown : {after_unknown}")
print(f"   Empty   : {after_empty}")
print(f"   Filled  : {filled} countries updated")
print(f"   Total rows: {len(df1)} (should be 33393)")

df1.to_csv(OUTPUT, index=False, encoding="utf-8")
print(f"\nSaved → {OUTPUT}")