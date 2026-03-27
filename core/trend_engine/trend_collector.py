import requests
import time

class TrendCollector:
    """
    Collects trending data from external sources (Reddit for now).
    """

    def __init__(self, logger, api_url, user_agent):
        self.logger = logger
        self.api_url = api_url
        self.user_agent = user_agent

    def fetch_trends(self):
        """
        Fetch trending posts from Reddit with automatic retries.
        """
        # --- DEBUG LOG ---
        self.logger.info(f"Using REDDIT_USER_AGENT: '{self.user_agent}'")
        # ------------------

        headers = {
            "User-Agent": self.user_agent
        }

        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.get(self.api_url, headers=headers, timeout=10)
                
                # We now include 403 in the retry list to see if a second try works
                if response.status_code in [403, 429, 503]:
                    self.logger.warning(
                        f"Reddit blocked or busy (Error {response.status_code}). "
                        f"Retrying in 5 seconds... (Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(5)
                    continue 
                
                response.raise_for_status()

                data = response.json()
                posts = data["data"]["children"]
                trends = [{"title": post["data"]["title"]} for post in posts]

                self.logger.info(f"Fetched {len(trends)} trends")
                return trends

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    break
        
        return []