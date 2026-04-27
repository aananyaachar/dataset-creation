import os
import json
import pandas as pd

DATASET_FOLDER = r"C:\Users\Downloads\dataset_folder"
POST_INFO_FOLDER = os.path.join(DATASET_FOLDER, "posts_info", "info")

POSTS_OUTPUT = os.path.join(DATASET_FOLDER, "posts.csv")
COMMENTS_OUTPUT = os.path.join(DATASET_FOLDER, "comments.csv")
INFLUENCERS_OUTPUT = os.path.join(DATASET_FOLDER, "influencers.csv")


if not os.path.exists(POST_INFO_FOLDER):
    print("ERROR: Folder does not exist:", POST_INFO_FOLDER)
    exit()

print("Folder found:", POST_INFO_FOLDER)

posts_data = []
comments_data = []
influencers_data = {}

valid_files = 0
invalid_files = 0

for root, dirs, files in os.walk(POST_INFO_FOLDER):
    for file in files:

        if not file.endswith(".info"):
            continue

        file_path = os.path.join(root, file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                post = json.load(f)

            post_id = post.get("id")
            owner = post.get("owner", {})
            username = owner.get("username")

            caption_edges = post.get("edge_media_to_caption", {}).get("edges", [])
            caption_text = ""
            if caption_edges:
                caption_text = caption_edges[0]["node"].get("text", "")

            likes = post.get("edge_media_preview_like", {}).get("count", 0)
            timestamp = post.get("taken_at_timestamp")


            posts_data.append({
                "post_id": post_id,
                "username": username,
                "caption": caption_text,
                "likes": likes,
                "timestamp": timestamp
            })

            comment_section = post.get("edge_media_to_parent_comment", {}).get("edges", [])

            for comment in comment_section:
                comment_node = comment["node"]

                comment_id = comment_node.get("id")
                comment_text = comment_node.get("text")
                comment_owner = comment_node.get("owner", {}).get("username")
                comment_likes = comment_node.get("edge_liked_by", {}).get("count", 0)
                comment_time = comment_node.get("created_at")

                comments_data.append({
                    "post_id": post_id,
                    "influencer_username": username,
                    "comment_id": comment_id,
                    "comment_text": comment_text,
                    "comment_owner": comment_owner,
                    "comment_likes": comment_likes,
                    "comment_timestamp": comment_time
                })

                replies = comment_node.get("edge_threaded_comments", {}).get("edges", [])

                for reply in replies:
                    reply_node = reply["node"]

                    comments_data.append({
                        "post_id": post_id,
                        "influencer_username": username,
                        "comment_id": reply_node.get("id"),
                        "comment_text": reply_node.get("text"),
                        "comment_owner": reply_node.get("owner", {}).get("username"),
                        "comment_likes": reply_node.get("edge_liked_by", {}).get("count", 0),
                        "comment_timestamp": reply_node.get("created_at")
                    })

            if username not in influencers_data:
                influencers_data[username] = {
                    "username": username,
                    "full_name": owner.get("full_name"),
                    "is_verified": owner.get("is_verified"),
                    "is_private": owner.get("is_private"),
                    "profile_id": owner.get("id")
                }

            valid_files += 1

            if valid_files % 10000 == 0:
                print(f"Processed {valid_files} files...")

        except Exception as e:
            invalid_files += 1
            continue

print("Saving CSV files...")

pd.DataFrame(posts_data).to_csv(POSTS_OUTPUT, index=False)
pd.DataFrame(comments_data).to_csv(COMMENTS_OUTPUT, index=False)
pd.DataFrame(list(influencers_data.values())).to_csv(INFLUENCERS_OUTPUT, index=False)

print("Processing Complete")
print("Valid files:", valid_files)
print("Invalid files:", invalid_files)
print("Posts saved to:", POSTS_OUTPUT)
print("Comments saved to:", COMMENTS_OUTPUT)
print("Influencers saved to:", INFLUENCERS_OUTPUT)
