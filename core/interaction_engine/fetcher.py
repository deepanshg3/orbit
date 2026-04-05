from configs.settings import settings
from platforms.threads.client import ThreadsClient


class InteractionFetcher:

    def __init__(self, logger):
        self.logger = logger
        self.client = ThreadsClient()

    def fetch_posts(self):
        """
        Fetch posts using keyword search
        """
        all_posts = []
        seen_ids = set()

        self.logger.info("[FETCHER] Fetching posts via keywords...")

        for keyword in settings.INTERACTION_KEYWORDS:
            try:
                self.logger.info(f"[FETCHER] Searching for keyword: {keyword}")

                # THE REAL META ENDPOINT
                response = self.client.get(
                    "keyword_search", 
                    params={
                        "q": keyword,
                        "fields": "id,text,username,permalink", # <-- DEMAND THE TEXT
                        "limit": 5  # <-- 1. Tell Meta to only send 5
                    }
                )

                # 2. Slice to enforce the 5-post limit locally just in case
                posts = response.get("data", [])[:5]

                # 🛑 ADD THIS TEMPORARY DEBUG LINE:
                # if posts:
                #     self.logger.info(f"[FETCHER] RAW API DATA: {posts[0]}")

                for post in posts:
                    post_id = post.get("id")

                    if post_id and post_id not in seen_ids:
                        seen_ids.add(post_id)

                        all_posts.append({
                            "id": post_id,
                            "text": post.get("text", ""),
                            "author": post.get("username", ""),
                        })

                if len(all_posts) >= settings.MAX_POSTS_FETCH:
                    break

            except Exception as e:
                self.logger.warning(f"[FETCHER] Failed for keyword {keyword}: {str(e)}")

        self.logger.info(f"[FETCHER] Total posts fetched: {len(all_posts)}")

        return all_posts