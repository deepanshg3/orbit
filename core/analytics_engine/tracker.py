from platforms.threads.client import ThreadsClient
import time

class ThreadsTracker:

    def __init__(self, logger):
        self.logger = logger
        self.client = ThreadsClient()

    def fetch_post_metrics(self, post_id):
        """
        Fetch metrics for a single post from Meta API
        """
        try:
            # 1. FIX: Added 'views' to the API request
            response = self.client.get(
                f"{post_id}/insights",
                params={"metric": "views,likes,replies,reposts"} 
            )

            data = response.get("data", [])

            # 2. FIX: Added 'views' to the starting dictionary
            metrics = {
                "views": 0,
                "likes": 0,
                "replies": 0,
                "reposts": 0
            }

            for item in data:
                name = item.get("name")
                values = item.get("values", [])
                value = values[0].get("value", 0) if values else 0

                if name in metrics:
                    metrics[name] = value

            return metrics

        except Exception as e:
            self.logger.error(f"[TRACKER] Failed to fetch metrics for {post_id}: {str(e)}")
            return {"views": 0, "likes": 0, "replies": 0, "reposts": 0}

    def fetch_thread_metrics(self, post_ids):
        """
        Aggregate metrics for full thread with Adaptive Filtering.
        """
        # 3. FIX: Added 'views' to the thread total
        total = {
            "views": 0,
            "likes": 0,
            "replies": 0,
            "reposts": 0
        }

        for post_id in post_ids:
            metrics = self.fetch_post_metrics(post_id)
            total["views"] += metrics["views"]
            total["likes"] += metrics["likes"]
            total["replies"] += metrics["replies"]
            total["reposts"] += metrics["reposts"]
            
            # 4. FIX: The safety buffer so Meta doesn't block you
            time.sleep(0.5) 

        raw_replies = total["replies"]
        internal_links = len(post_ids) - 1
        
        if raw_replies >= internal_links:
            total["replies"] = raw_replies - internal_links
            self.logger.info(f"[TRACKER] Cleaned {internal_links} self-replies from total.")
        else:
            total["replies"] = raw_replies
            self.logger.info(f"[TRACKER] API appears to be pre-filtering self-replies. Using raw count.")

        self.logger.info(f"[TRACKER] Final Aggregated metrics: {total}")

        return total