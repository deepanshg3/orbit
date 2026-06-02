import os
import requests
from configs.settings import settings
from core.utils.logger import get_logger
        
class ThreadsClient:
    BASE_URL = "https://graph.threads.net/v1.0"

    def __init__(self):
        self.access_token = settings.THREADS_ACCESS_TOKEN

        if not self.access_token:
            raise ValueError("THREADS_ACCESS_TOKEN not found. Run: source ~/.bashrc")

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def post(self, endpoint: str, data: dict):
        url = f"{self.BASE_URL}/{endpoint}"

        response = requests.post(url, json=data, headers=self._get_headers())

        if response.status_code != 200:
            raise Exception(f"Threads API Error: {response.text}")

        return response.json()

    def get(self, endpoint: str, params: dict = None):
        url = f"{self.BASE_URL}/{endpoint}"

        response = requests.get(url, params=params, headers=self._get_headers())

        if response.status_code != 200:
            raise Exception(f"Threads API Error: {response.text}")

        return response.json()
    
    def get_replies(self, post_id: str) -> list:
        local_logger = get_logger("orbit.threads_api")
        local_logger.info(f"[THREADS] Fetching replies for post: {post_id}")
        
        url = f"https://graph.threads.net/v1.0/{post_id}/replies"
        
        # CRITICAL: If you do not send this, Meta will NOT send the username back.
        params = {
            "fields": "id,text,username"
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                local_logger.error(f"[THREADS ERROR] Failed to fetch replies for {post_id}: {response.text}")
                return []
                
        except Exception as e:
            local_logger.error(f"[THREADS ERROR] Network exception while getting replies: {str(e)}")
            return []

    def publish_reply(self, text: str, reply_to_id: str) -> dict:
        """
        Executes Meta's mandatory 2-step publishing process for a reply.
        Step 1: Create the media container.
        Step 2: Publish the container.
        """
        local_logger = get_logger("orbit.threads_api")
        
        # Step 1: Create Container
        local_logger.info(f"[THREADS] Creating reply container for comment: {reply_to_id}")
        container_payload = {
            "media_type": "TEXT",
            "text": text,
            "reply_to_id": reply_to_id
        }
        
        try:
            # Utilizing your existing generic post wrapper
            container_res = self.post("me/threads", data=container_payload)
            container_id = container_res.get("id")
            
            if not container_id:
                local_logger.error("[THREADS ERROR] Meta did not return a container ID.")
                return None
                
            # Step 2: Publish Container
            local_logger.info(f"[THREADS] Publishing container ID: {container_id}")
            publish_payload = {
                "creation_id": container_id
            }
            
            publish_res = self.post("me/threads_publish", data=publish_payload)
            return publish_res
            
        except Exception as e:
            local_logger.error(f"[THREADS ERROR] Failed to publish reply: {str(e)}")
            return None