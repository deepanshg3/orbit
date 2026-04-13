from core.utils.logger import get_logger

class ImpactCalculator:
    def __init__(self, logger, supabase_client):
        self.logger = logger
        self.client = supabase_client

    def calculate_and_save(self, post_id):
        """
        Fetches existing time buckets for a post, runs the 50/30/20 math, 
        and permanently grades the post.
        """
        self.logger.info(f"[CALCULATOR] Grading Post ID: {post_id}")

        try:
            # 1. Fetch whatever metrics exist for this post
            response = self.client.table("post_metrics") \
                .select("time_bucket, engagement_score") \
                .eq("post_id_ref", post_id) \
                .execute()

            metrics = response.data
            
            if not metrics:
                self.logger.warning(f"[CALCULATOR] Post {post_id} has absolutely zero metric data. Defaulting to 0.0")
                self._update_post_score(post_id, 0.0)
                return

            # 2. Extract the engagement scores into a dictionary
            scores = {row["time_bucket"]: row["engagement_score"] for row in metrics}

            # 3. Data Imputation: Find the average of available scores to plug holes
            available_scores = list(scores.values())
            avg_score = sum(available_scores) / len(available_scores)

            # 4. Safely get scores (fallback to the average if a bucket is missing)
            score_2h = scores.get("2h", avg_score)
            score_1d = scores.get("1d", avg_score)
            score_3d = scores.get("3d", avg_score)

            # 5. THE MATH: 50% hook, 30% daily, 20% evergreen
            true_impact_score = (score_2h * 0.50) + (score_1d * 0.30) + (score_3d * 0.20)

            # 6. Save it permanently
            self._update_post_score(post_id, true_impact_score)

        except Exception as e:
            self.logger.error(f"[CALCULATOR] Failed to calculate impact for {post_id}: {str(e)}")

    def _update_post_score(self, post_id, score):
        """Helper function to update the posts table"""
        try:
            self.client.table("posts") \
                .update({"true_impact_score": score}) \
                .eq("id", post_id) \
                .execute()
            self.logger.info(f"[CALCULATOR] Successfully graded Post {post_id} with Impact Score: {score:.4f}")
        except Exception as e:
            self.logger.error(f"[CALCULATOR] Database update failed for {post_id}: {str(e)}")


    def sweep_orphaned_posts(self):
        """
        The Safety Net: Finds posts older than 75 hours that never got graded 
        due to server downtime or API limits, and forces a grade.
        """
        self.logger.info("[CALCULATOR] Sweeping for orphaned, ungraded posts...")
        
        # Calculate the timestamp for 75 hours ago
        from datetime import datetime, timedelta, timezone
        cutoff_time = (datetime.now(timezone.utc) - timedelta(hours=75)).isoformat()

        try:
            # Query posts older than 75h where true_impact_score is still NULL
            response = self.client.table("posts") \
                .select("id") \
                .lt("created_at", cutoff_time) \
                .is_("true_impact_score", "null") \
                .execute()

            orphans = response.data

            if not orphans:
                self.logger.info("[CALCULATOR] No orphaned posts found. Database is clean.")
                return

            self.logger.info(f"[CALCULATOR] Found {len(orphans)} orphaned posts. Initiating emergency grading...")
            
            for post in orphans:
                self.calculate_and_save(post["id"])

        except Exception as e:
            self.logger.error(f"[CALCULATOR] Orphan sweep failed: {str(e)}")
