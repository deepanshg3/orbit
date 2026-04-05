import time
from datetime import datetime, timedelta, timezone
from core.utils.logger import get_logger
from core.analytics_engine.storage import Storage
from core.analytics_engine.tracker import ThreadsTracker
from dateutil import parser  

logger = get_logger("orbit.fetch_metrics")

class MetricsFetcher:

    def __init__(self):
        self.storage = Storage(logger)
        self.tracker = ThreadsTracker(logger)

    def fetch_active_posts(self):
        four_days_ago = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()

        response = self.storage.client.table("posts") \
            .select("id, post_ids, created_at") \
            .gte("created_at", four_days_ago) \
            .execute()

        return response.data

    def get_existing_metrics(self, post_ids):
        if not post_ids:
            return {}

        response = self.storage.client.table("post_metrics") \
            .select("post_id_ref, time_bucket") \
            .in_("post_id_ref", post_ids) \
            .execute()

        existing = {}

        for row in response.data:
            post_id = row["post_id_ref"]
            bucket = row["time_bucket"]

            existing.setdefault(post_id, []).append(bucket)

        return existing

    def is_eligible(self, created_at, target_hours):
        # This parser is much "smarter" than the built-in one
        post_time = parser.isoparse(created_at)
        
        # Ensure it's UTC-aware to match our 'now' variable
        if post_time.tzinfo is None:
            post_time = post_time.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        age = (now - post_time).total_seconds() / 3600

        # GRACE PERIOD LOGIC:
        # It must be older than target_hours, BUT no older than target_hours + 4
        # E.g., for the 2h bucket, age must be strictly between 2.0 and 6.0 hours.
        is_valid_window = (target_hours <= age <= target_hours + 4)

        return is_valid_window, age

    def run(self):
        logger.info("[FETCHER] Checking metrics...")

        posts = self.fetch_active_posts()

        if not posts:
            logger.info("[FETCHER] No recent posts. Exiting.")
            return

        post_ids_db = [p["id"] for p in posts]

        existing_metrics = self.get_existing_metrics(post_ids_db)

        batch_2h, batch_1d, batch_3d = [], [], []

        for post in posts:
            db_id = post["id"]
            thread_ids = post["post_ids"]
            created_at = post["created_at"]

            completed = existing_metrics.get(db_id, [])

            eligible, age = self.is_eligible(created_at, 2)
            if eligible and "2h" not in completed:
                batch_2h.append((db_id, thread_ids, age))

            eligible, age = self.is_eligible(created_at, 24)
            if eligible and "1d" not in completed:
                batch_1d.append((db_id, thread_ids, age))

            eligible, age = self.is_eligible(created_at, 72)
            if eligible and "3d" not in completed:
                batch_3d.append((db_id, thread_ids, age))

        self.process_batch(batch_2h, "2h")
        self.process_batch(batch_1d, "1d")
        self.process_batch(batch_3d, "3d")

        logger.info("[FETCHER] All metrics updated.")

    def process_batch(self, batch, bucket):
        if not batch:
            logger.info(f"[FETCHER] No posts for {bucket}")
            return

        logger.info(f"[FETCHER] Processing {len(batch)} posts for {bucket}")

        for db_id, thread_ids, age in batch:
            try:
                logger.info(f"[FETCHER] → Post {db_id} ({bucket})")

                metrics = self.tracker.fetch_thread_metrics(thread_ids)

                self.storage.save_metrics(
                    post_db_id=db_id,
                    time_bucket=bucket,
                    metrics=metrics,
                    time_since_post_hr=age
                )

                time.sleep(2)

            except Exception as e:
                logger.error(f"[FETCHER] Failed for {db_id}: {str(e)}")

if __name__ == "__main__":
    fetcher = MetricsFetcher()
    fetcher.run()