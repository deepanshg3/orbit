class InteractionMemory:

    def __init__(self, logger, client):
        self.logger = logger
        self.client = client

    def already_replied(self, post_id):
        """
        Optional lightweight check (can be skipped if using UNIQUE constraint only)
        """
        try:
            response = self.client.table("interactions") \
                .select("id") \
                .eq("external_post_id", post_id) \
                .limit(1) \
                .execute()

            exists = len(response.data) > 0

            if exists:
                self.logger.info(f"[MEMORY] Already replied to post {post_id}")

            return exists

        except Exception as e:
            self.logger.error(f"[MEMORY] Check failed: {str(e)}")
            return False

    def save_interaction(
        self,
        post_id,
        reply_text,
        keyword=None,
        score=None,
        reason=None,
        our_reply_id=None
    ):
        """
        Save interaction safely (handles duplicates)
        """

        record = {
            "external_post_id": post_id,
            "reply_text": reply_text,
            "keyword": keyword,
            "score": score,
            "reason": reason,
            "our_reply_id": our_reply_id,
            "status": "posted"
        }

        try:
            response = self.client.table("interactions").insert(record).execute()

            self.logger.info(
                f"[MEMORY] Interaction saved | Post: {post_id} | Reply ID: {our_reply_id}"
            )

            return True

        except Exception as e:
            error_msg = str(e)

            # 🔥 Handle duplicate safely
            if "duplicate key value violates unique constraint" in error_msg.lower():
                self.logger.warning(
                    f"[MEMORY] Duplicate prevented for post {post_id}"
                )
                return False

            self.logger.error(f"[MEMORY] Save failed: {error_msg}")
            return False