import pandas as pd
from textblob import TextBlob

print("Loading datasets...")


posts = pd.read_csv("posts.csv")
comments = pd.read_csv("comments.csv")
influencers_profile = pd.read_csv("influencers.csv")

# influencer.txt is tab separated
influencer_stats = pd.read_csv("influencers.txt", sep="\t")


posts.columns = posts.columns.str.lower().str.strip()
comments.columns = comments.columns.str.lower().str.strip()
influencers_profile.columns = influencers_profile.columns.str.lower().str.strip()
influencer_stats.columns = influencer_stats.columns.str.lower().str.strip()

# Rename influencer.txt columns to clean names
influencer_stats = influencer_stats.rename(columns={
    "#followers": "followers",
    "#followees": "followees",
    "#posts": "total_posts"
})

influencers_master = pd.merge(
    influencers_profile,
    influencer_stats,
    on="username",
    how="left"
)

influencers_master.to_csv("influencers_master.csv", index=False)

print("Influencer master file created.")