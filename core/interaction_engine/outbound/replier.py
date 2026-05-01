class InteractionReplier:
    def __init__(self, logger, client):
        self.logger = logger
        self.client = client

    def post_reply(self, target_post_id, reply_text):
        """
        Executes Meta's required 2-step process for replying to a Threads post.
        """
        self.logger.info(f"[REPLIER] Creating reply container for target {target_post_id}...")
        
        try:
            # STEP 1: Create the container attached to the target post
            container_response = self.client.post(
                "me/threads", 
                data={
                    "media_type": "TEXT",
                    "text": reply_text,
                    "reply_to_id": target_post_id
                }
            )
            
            creation_id = container_response.get("id")
            if not creation_id:
                self.logger.error("[REPLIER] Meta failed to return a creation_id.")
                return None

            self.logger.info(f"[REPLIER] Container created (ID: {creation_id}). Publishing...")

            # STEP 2: Publish the container to make it live
            publish_response = self.client.post(
                "me/threads_publish",
                data={"creation_id": creation_id}
            )

            reply_id = publish_response.get("id")
            return reply_id

        except Exception as e:
            self.logger.error(f"[REPLIER] Failed to post reply: {str(e)}")
            return None