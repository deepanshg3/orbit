from core.utils.logger import get_logger

logger = get_logger("orbit.playbook_reader")

class PlaybookReader:
    def __init__(self, supabase_client):
        self.client = supabase_client

    def get_latest_playbook(self) -> dict:
        """
        Fetches the most recent strategy epoch from the database.
        Returns None if the database is empty or fails.
        """
        logger.info("[PLAYBOOK] Fetching latest audience strategy from database...")
        
        try:
            response = self.client.table("strategy_epochs") \
                .select("*") \
                .order("epoch_end", desc=True) \
                .limit(1) \
                .execute()
            
            if response.data:
                logger.info("[PLAYBOOK] Successfully loaded latest strategy epoch.")
                return response.data[0]
            else:
                logger.warning("[PLAYBOOK] No strategy epochs found. Running entirely on defaults.")
                return None
                
        except Exception as e:
            logger.error(f"[PLAYBOOK ERROR] Failed to fetch strategy: {str(e)}")
            return None