from platforms.threads.client import ThreadsClient
import random

class ThreadsTracker:

    def __init__(self, logger):
        self.logger = logger
        self.client = ThreadsClient()

    def fetch_post_metrics(self, post_id):
        """
        Fetch metrics for a single post from Meta API
        """
        try:
            # Note: Ensure your ThreadsClient.get method handles the endpoint correctly
            response = self.client.get(
                f"{post_id}/insights",
                params={"metric": "likes,replies,reposts"}
            )

            # Meta Insights API usually returns a list of metric objects
            data = response.get("data", [])

            metrics = {
                "likes": 0,
                "replies": 0,
                "reposts": 0
            }

            for item in data:
                name = item.get("name")
                # Insights usually return a list of values; we take the first one
                values = item.get("values", [])
                value = values[0].get("value", 0) if values else 0

                if name in metrics:
                    metrics[name] = value

            return metrics

        except Exception as e:
            self.logger.error(f"[TRACKER] Failed to fetch metrics for {post_id}: {str(e)}")
            return {"likes": 0, "replies": 0, "reposts": 0}

    def fetch_thread_metrics(self, post_ids):
        """
        Aggregate metrics for full thread with Adaptive Filtering.
        Protects against undercounting if the API changes its behavior.
        """
        total = {
            "likes": 0,
            "replies": 0,
            "reposts": 0
        }

        # 1. Sum up all raw metrics from the individual posts
        for post_id in post_ids:
            metrics = self.fetch_post_metrics(post_id)
            total["likes"] += metrics["likes"]
            total["replies"] += metrics["replies"]
            total["reposts"] += metrics["reposts"]

        # 2. SMART FILTER LOGIC
        raw_replies = total["replies"]
        # In a thread of 6 parts, there are 5 internal 'reply' links
        internal_links = len(post_ids) - 1
        
        # Scenario Check:
        # If raw_replies is 5 and we have 5 internal links, it's likely counting our own parts.
        # If raw_replies is 0, the API is already excluding them, so we do nothing.
        if raw_replies >= internal_links:
            total["replies"] = raw_replies - internal_links
            self.logger.info(f"[TRACKER] Cleaned {internal_links} self-replies from total.")
        else:
            # The API is likely already giving us 'clean' data
            total["replies"] = raw_replies
            self.logger.info(f"[TRACKER] API appears to be pre-filtering self-replies. Using raw count.")

        self.logger.info(f"[TRACKER] Final Aggregated metrics: {total}")

        return total