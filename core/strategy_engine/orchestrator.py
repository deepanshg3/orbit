from datetime import datetime, timedelta, timezone
from core.utils.logger import get_logger
from core.strategy_engine.analyzer import StrategyAnalyzer

logger = get_logger("orbit.strategy_orchestrator")

class StrategyOrchestrator:
    def __init__(self, logger_instance, supabase_client):
        self.logger = logger_instance
        self.client = supabase_client
        self.analyzer = StrategyAnalyzer()

    def execute_weekly_strategy(self):
        """
        The main pipeline: Extracts data, calls AI, and saves the Epoch.
        """
        self.logger.info("=== STARTING WEEKLY STRATEGY EXTRACTION ===")
        
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)
        
        # ---------------------------------------------------------
        # STEP 1: FETCH GRADED POSTS
        # ---------------------------------------------------------
        self.logger.info(f"[ORCHESTRATOR] Fetching posts since {seven_days_ago.strftime('%Y-%m-%d')}")
        
        response = self.client.table("posts") \
            .select("id, hook, content, takeaway, true_impact_score") \
            .gte("created_at", seven_days_ago.isoformat()) \
            .not_.is_("true_impact_score", "null") \
            .execute()
            
        posts = response.data
        
        if not posts or len(posts) < 5:
            self.logger.warning("[ORCHESTRATOR] Not enough graded posts this week to generate a strategy. Aborting.")
            return

        total_posts_analyzed = len(posts)
        average_impact_score = sum(p["true_impact_score"] for p in posts) / total_posts_analyzed
        
        self.logger.info(f"[ORCHESTRATOR] Found {total_posts_analyzed} graded posts. Avg Score: {average_impact_score:.4f}")

        # ---------------------------------------------------------
        # STEP 2: SORT TOP 5 & BOTTOM 5
        # ---------------------------------------------------------
        # Sort posts by impact score descending
        sorted_posts = sorted(posts, key=lambda x: x["true_impact_score"], reverse=True)
        
        top_5 = sorted_posts[:5]
        bottom_5 = sorted_posts[-5:]
        
        top_5_ids = [p["id"] for p in top_5]
        bottom_5_ids = [p["id"] for p in bottom_5]
        
        self.logger.info(f"[ORCHESTRATOR] Top 5 IDs: {top_5_ids}")
        self.logger.info(f"[ORCHESTRATOR] Bottom 5 IDs: {bottom_5_ids}")

        # Format text for the LLM
        top_text = self._format_posts_for_llm(top_5)
        bottom_text = self._format_posts_for_llm(bottom_5)

        # ---------------------------------------------------------
        # STEP 3: FETCH METRICS & CALCULATE MACRO TOTALS
        # ---------------------------------------------------------
        self.logger.info("[ORCHESTRATOR] Aggregating week's raw metrics...")
        post_ids = [p["id"] for p in posts]
        
        metrics_response = self.client.table("post_metrics") \
            .select("time_bucket, views, likes, replies, reposts") \
            .in_("post_id_ref", post_ids) \
            .execute()
            
        macro_stats = self._calculate_epoch_metrics(metrics_response.data)

        # ---------------------------------------------------------
        # STEP 4: GENERATE AI PLAYBOOK
        # ---------------------------------------------------------
        self.logger.info("[ORCHESTRATOR] Handing off text to Strategy Analyzer (Gemini)...")
        playbook = self.analyzer.generate_playbook(top_text, bottom_text)

        # ---------------------------------------------------------
        # STEP 5: SAVE EPOCH TO DATABASE
        # ---------------------------------------------------------
        self.logger.info("[ORCHESTRATOR] Locking Epoch into Database...")
        
        epoch_data = {
            "epoch_start": seven_days_ago.isoformat(),
            "epoch_end": now.isoformat(),
            "total_posts_analyzed": total_posts_analyzed,
            "average_impact_score": average_impact_score,
            
            # Relational Links
            "top_5_post_ids": top_5_ids,
            "bottom_5_post_ids": bottom_5_ids,
            
            # Quantitative Totals (From Step 3)
            "metrics_2h": macro_stats["2h"],
            "metrics_24h": macro_stats["1d"],  # Named 1d in your tracker
            "metrics_72h": macro_stats["3d"]   # Named 3d in your tracker
        }
        
        # Merge the AI Playbook dictionary directly into the epoch data
        epoch_data.update(playbook)

        try:
            self.client.table("strategy_epochs").insert(epoch_data).execute()
            self.logger.info("=== WEEKLY STRATEGY EPOCH SAVED SUCCESSFULLY ===")
        except Exception as e:
            self.logger.error(f"[ORCHESTRATOR] Database Insert Failed: {str(e)}")

    # --- Helper Functions ---
    def _format_posts_for_llm(self, posts_list):
        """Formats the list of post dictionaries into a readable string for Gemini."""
        formatted = ""
        for i, p in enumerate(posts_list, 1):
            formatted += f"\n--- POST {i} (Impact Score: {p['true_impact_score']:.4f}) ---\n"
            formatted += f"HOOK: {p.get('hook', '')}\n"
            formatted += f"CONTENT: {p.get('content', '')}\n"
            formatted += f"TAKEAWAY: {p.get('takeaway', '')}\n"
        return formatted

    def _calculate_epoch_metrics(self, raw_metrics_data):
        """Sums up the views/likes/replies for the entire week, categorized by bucket."""
        totals = {
            "2h": {"views": 0, "likes": 0, "replies": 0, "reposts": 0},
            "1d": {"views": 0, "likes": 0, "replies": 0, "reposts": 0},
            "3d": {"views": 0, "likes": 0, "replies": 0, "reposts": 0}
        }
        
        for row in raw_metrics_data:
            bucket = row["time_bucket"]
            
            # Populate bucket specific JSON
            if bucket in ["2h", "1d", "3d"]:
                totals[bucket]["views"] += row["views"]
                totals[bucket]["likes"] += row["likes"]
                totals[bucket]["replies"] += row["replies"]
                totals[bucket]["reposts"] += row["reposts"]
                
        return totals