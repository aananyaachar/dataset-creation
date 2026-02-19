import pandas as pd
import random
import uuid
import time
from faker import Faker
from collections import defaultdict

fake = Faker()

# CONFIG
NUM_INFLUENCERS = 100
AVG_POSTS_PER_INFLUENCER = 2000  
AVG_COMMENTS_PER_POST = 15

NICHES = ["Beauty", "Fashion", "Fitness", "Food", "Travel", "Tech", "Lifestyle", "Finance", "Gaming"]
GENDERS = ["Male", "Female", "Mixed"]
COUNTRIES = ["USA", "UK", "India", "Canada", "Australia"]

# STORAGE
influencer_master = []
instagram_posts = []
influencer_relevance = []
post_comments = []
engagement_metrics = []
audience_sentiment = []

engagement_tracker = defaultdict(lambda: {"likes": [], "comments": [], "views": [], "posts": 0})
sentiment_tracker = defaultdict(lambda: {"negative": 0, "total": 0})

print("Generating dataset...")

# GENERATE

for i in range(1, NUM_INFLUENCERS + 1):

    influencer_id = f"influencer_{i}"
    influencer_name = fake.user_name()
    niche = random.choice(NICHES)
    followers = random.randint(10000, 2000000)

    influencer_master.append({
        "influencer_id": influencer_id,
        "influencer_name": influencer_name,
        "niche": niche,
        "audience_age_min": random.randint(15, 20),
        "audience_age_max": random.randint(30, 45),
        "gender": random.choice(GENDERS),
        "followers_count": followers,
        "country": random.choice(COUNTRIES)
    })

    num_posts = AVG_POSTS_PER_INFLUENCER

    print(f"Generating posts for {influencer_id}")

    for _ in range(num_posts):

        content_id = str(uuid.uuid4())
        caption = fake.sentence(nb_words=12)
        timestamp = int(time.time()) - random.randint(0, 10000000)

        likes = int(abs(random.gauss(followers * 0.05, followers * 0.01)))
        comments_count = int(abs(random.gauss(AVG_COMMENTS_PER_POST, 5)))
        views = int(abs(random.gauss(followers * 0.2, followers * 0.05)))

        instagram_posts.append({
            "content_id": content_id,
            "influencer_id": influencer_id,
            "caption_text": caption,
            "likes": likes,
            "comments": comments_count,
            "views": views,
            "timestamp": timestamp
        })

        influencer_relevance.append({
            "influencer_id": influencer_id,
            "content_id": content_id,
            "caption_text": caption,
            "bio_keywords": ",".join(caption.lower().split()[:5]),
            "content_category": niche
        })

        engagement_tracker[influencer_id]["likes"].append(likes)
        engagement_tracker[influencer_id]["comments"].append(comments_count)
        engagement_tracker[influencer_id]["views"].append(views)
        engagement_tracker[influencer_id]["posts"] += 1

        for _ in range(comments_count):
            comment_id = str(uuid.uuid4())
            is_negative = random.random() < 0.25

            if is_negative:
                comment_text = random.choice([
                    "This is disappointing",
                    "Worst post ever",
                    "Not impressed",
                    "Terrible content",
                    "So bad honestly"
                ])
            else:
                comment_text = fake.sentence(nb_words=8)

            post_comments.append({
                "comment_id": comment_id,
                "content_id": content_id,
                "influencer_id": influencer_id,
                "comment_text": comment_text,
                "timestamp": timestamp
            })

            sentiment_tracker[influencer_id]["total"] += 1
            if is_negative:
                sentiment_tracker[influencer_id]["negative"] += 1

# AGGREGATE ENGAGEMENT
for influencer_id, data in engagement_tracker.items():
    avg_likes = sum(data["likes"]) / len(data["likes"])
    avg_comments = sum(data["comments"]) / len(data["comments"])
    avg_views = sum(data["views"]) / len(data["views"])
    ratio = avg_comments / avg_likes if avg_likes > 0 else 0

    engagement_metrics.append({
        "influencer_id": influencer_id,
        "avg_likes": round(avg_likes, 2),
        "avg_comments": round(avg_comments, 2),
        "avg_views": round(avg_views, 2),
        "comment_to_like_ratio": round(ratio, 4),
        "posting_frequency": data["posts"]
    })

# AGGREGATE SENTIMENT
for influencer_id, data in sentiment_tracker.items():
    negative_ratio = data["negative"] / data["total"] if data["total"] > 0 else 0

    if negative_ratio > 0.4:
        label = "Negative"
    elif negative_ratio < 0.2:
        label = "Positive"
    else:
        label = "Neutral"

    audience_sentiment.append({
        "influencer_id": influencer_id,
        "sentiment_label": label,
        "negative_comments_ratio": round(negative_ratio, 3)
    })


# SAVE FILES
pd.DataFrame(influencer_master).to_csv("influencer_master.csv", index=False)
pd.DataFrame(instagram_posts).to_csv("instagram_posts.csv", index=False)
pd.DataFrame(influencer_relevance).to_csv("influencer_relevance.csv", index=False)
pd.DataFrame(post_comments).to_csv("post_comments.csv", index=False)
pd.DataFrame(engagement_metrics).to_csv("engagement_metrics.csv", index=False)
pd.DataFrame(audience_sentiment).to_csv("audience_sentiment.csv", index=False)

print(" Dataset generated successfully.")




