from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
from configs.settings import settings
from core.utils.logger import get_logger

logger = get_logger("orbit.inbound.sweeper")

class InboundSweeper:
    def __init__(self, threads_client):
        """
        Initializes the Sweeper engine with an active Meta Threads API client
        and a Supabase connection instance acting as the state/memory layer.
        """
        self.threads_client = threads_client
        self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.logger = logger

    def get_recent_posts(self, days_limit=3):
        """
        Queries the Supabase 'posts' table to fetch all parent threads published 
        within the rolling time window. Each row returns the thread's semantic context 
        (hook, takeaway) and an array list of unique Meta post IDs representing the thread parts.
        """
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_limit)).isoformat()
        
        try:
            response = self.supabase.table("posts") \
                .select("post_ids, hook, takeaway") \
                .gte("created_at", cutoff_date) \
                .execute()
            
            return response.data
        except Exception as e:
            self.logger.error(f"[SWEEPER ERROR] Failed to fetch recent posts from DB: {e}")
            return []

    def sweep_for_unanswered(self):
        """
        The Master Execution Loop.
        1. Grabs recent threads and iterates through their individual parts.
        2. Queries the Meta API for live user replies under each specific post ID.
        3. Enforces the depth-limit-of-1 rule by dropping comments if the user has 
           already been replied to anywhere inside that specific post ID.
        4. Compiles a clean payload queue for batch processing.
        """
        self.logger.info("[SWEEPER] Waking up. Starting rolling 72-hour timeline sweep...")
        
        recent_threads = self.get_recent_posts(days_limit=3)
        
        if not recent_threads:
            self.logger.info("[SWEEPER] No recent posts found in the last 72 hours. Going back to sleep.")
            return []

        all_unanswered = []

        # Iterate through each thread container row fetched from 'posts'
        for thread in recent_threads:
            post_ids = thread.get("post_ids", [])
            hook = thread.get("hook", "")
            takeaway = thread.get("takeaway", "")

            # Iterate through each individual media/post sub-component of the thread
            for post_id in post_ids:
                self.logger.info(f"[SWEEPER] Scanning thread component ID: {post_id} for user replies...")
                
                try:
                    # Request live replies array from the Meta API client wrapper
                    raw_replies = self.threads_client.get_replies(post_id) 
                except Exception as e:
                    self.logger.warning(f"[SWEEPER API WARN] Failed to fetch replies from Meta for {post_id}: {e}")
                    continue

                if not raw_replies:
                    continue

                # Process every single incoming reply on this specific sub-post
                for reply in raw_replies:
                    comment_id = reply.get("id")
                    username = reply.get("username", "unknown_user") 
                    text = reply.get("text", "")

                    if username == "unknown_user":
                        self.logger.warning(f"[SWEEPER] Meta didn't return a username for {comment_id}. Skipping.")
                        continue

                    # --- THE CONFIG-DRIVEN BLOCK ---
                    # Clean up the config username just in case it has an '@' symbol
                    my_username = settings.THREADS_USERNAME.replace("@", "").lower()
                    
                    if username.lower() == my_username:
                        self.logger.info(f"[SWEEPER] Dropped self-reply from @{my_username}.")
                        continue
                    # -------------------------------
                    try:
                        # ENFORCE DEPTH LIMIT 1: 
                        # Check if this username has a logging history for this exact post_id
                        db_check = self.supabase.table("inbound_interactions") \
                            .select("id") \
                            .eq("post_id", post_id) \
                            .eq("username", username) \
                            .execute()

                        if len(db_check.data) > 0:
                            self.logger.debug(f"[SWEEPER] Skipping reply from {username} on post {post_id} (Interaction depth limit hit).")
                            continue
                        
                        # Queue valid un-interacted target comment 
                        all_unanswered.append({
                            "post_id": post_id,           # Required to routing the future reply safely
                            "comment_id": comment_id,     # Target ID mapping the reply container
                            "username": username,
                            "text": text,
                            "context": {
                                "hook": hook,
                                "takeaway": takeaway
                            }
                        })
                        
                    except Exception as e:
                        self.logger.error(f"[SWEEPER DB ERROR] Failed verifying interaction state for comment {comment_id}: {e}")

        self.logger.info(f"[SWEEPER] Sweep process finalized. Identified {len(all_unanswered)} fresh comments for queue.")
        return all_unanswered
