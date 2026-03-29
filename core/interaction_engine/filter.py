from configs.settings import settings


class InteractionFilter:

    def __init__(self, logger, memory):
        self.logger = logger
        self.memory = memory

    def filter_posts(self, posts):
        """
        Remove low-quality, self-authored, and already-processed posts
        """

        filtered = []

        # Metrics
        removed_empty = 0
        removed_short = 0
        removed_noise = 0
        removed_duplicates = 0
        removed_self = 0 # <--- ADD THIS METRIC

        self.logger.info("[FILTER] Filtering posts...")

        for post in posts:
            post_id = post.get("id")
            text = post.get("text", "").strip()
            author = post.get("author", "") # <--- GRAB THE AUTHOR

            # -------------------------------
            # 1. Empty check
            # -------------------------------
            if not text:
                removed_empty += 1
                continue

            # -------------------------------
            # 2. Self-Awareness Check (NO REPLYING TO YOURSELF)
            # -------------------------------
            if author == "hard.truths_": # (Or use settings.BOT_USERNAME if you have one)
                removed_self += 1
                continue

            # -------------------------------
            # 3. Length check
            # -------------------------------
            if len(text) < settings.MIN_POST_LENGTH:
                removed_short += 1
                continue

            # ... Keep your existing Noise and Duplicate checks ...

            # -------------------------------
            # 4. Noise filter
            # -------------------------------
            if text.lower() in ["hello", "hi", "good morning"]:
                removed_noise += 1
                continue

            # -------------------------------
            # 5. Duplicate check (DB)
            # -------------------------------
            if self.memory.already_replied(post_id):
                removed_duplicates += 1
                continue

            filtered.append(post)

        # -------------------------------
        # Logging (VERY IMPORTANT)
        # -------------------------------
        self.logger.info(f"[FILTER] Input posts: {len(posts)}")
        self.logger.info(f"[FILTER] Removed empty: {removed_empty}")
        self.logger.info(f"[FILTER] Removed short: {removed_short}")
        self.logger.info(f"[FILTER] Removed noise: {removed_noise}")
        self.logger.info(f"[FILTER] Removed duplicates: {removed_duplicates}")
        self.logger.info(f"[FILTER] Removed self: {removed_self}") 
        self.logger.info(f"[FILTER] Final posts: {len(filtered)}")

        return filtered