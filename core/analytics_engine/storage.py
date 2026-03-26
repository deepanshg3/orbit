from supabase import create_client
from configs.settings import settings
from datetime import datetime, timezone


class Storage:

    def __init__(self, logger):
        self.logger = logger
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    # -------------------------------
    # SAVE POST
    # -------------------------------
    def save_post(self, generated_content, post_ids, trend):
        try:
            # Count parts (for threads)
            if isinstance(generated_content.content, list):
                content_parts = len(generated_content.content)
            else:
                content_parts = 1

            total_parts = 1 + content_parts + 1  # hook + content + takeaway

            data = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "post_ids": post_ids,
                "content_type": generated_content.content_type,
                "topic_title": trend.title,
                "llm_score": trend.score,
                "hook": generated_content.hook,
                "content": generated_content.content,
                "takeaway": generated_content.takeaway,
                "total_parts": total_parts,
                "status": "published"
            }

            response = self.client.table("posts").insert(data).execute()

            post_db_id = response.data[0]["id"]

            self.logger.info(f"[STORAGE] Post saved in DB with id: {post_db_id}")

            return post_db_id

        except Exception as e:
            self.logger.error(f"[STORAGE] Failed to save post: {str(e)}")
            raise

    # -------------------------------
    # SAVE METRICS
    # -------------------------------
    def save_metrics(self, post_db_id, time_bucket, metrics, time_since_post_hr):
        try:
            data = {
                "post_id_ref": post_db_id,
                "time_bucket": time_bucket,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "likes": metrics.get("likes", 0),
                "replies": metrics.get("replies", 0),
                "reposts": metrics.get("reposts", 0),
                "time_since_post_hr": time_since_post_hr
            }

            self.client.table("post_metrics").insert(data).execute()

            self.logger.info(f"[STORAGE] Metrics saved for {time_bucket}")

        except Exception as e:
            self.logger.error(f"[STORAGE] Failed to save metrics: {str(e)}")
            raise