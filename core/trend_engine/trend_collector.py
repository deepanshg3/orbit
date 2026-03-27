import requests
import time

class TrendCollector:
    """
    Collects trending data from Hacker News (Algolia API).
    """

    def __init__(self, logger, api_url, user_agent):
        self.logger = logger
        self.api_url = api_url
        self.user_agent = user_agent

    def fetch_trends(self):
        """
        Fetch trending posts from Hacker News.
        """
        self.logger.info("Fetching real-time tech buzz from Hacker News...")

        # Algolia API doesn't strictly require User-Agent, but it's good practice
        headers = {"User-Agent": self.user_agent}
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = requests.get(self.api_url, headers=headers, timeout=10)
                
                # Hacker News is very stable, but we check for standard server errors
                if response.status_code in [429, 503]:
                    self.logger.warning(f"Server busy. Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(5)
                    continue 
                
                response.raise_for_status()
                data = response.json()

                # CHANGE HERE: Hacker News returns a list called 'hits'
                posts = data.get("hits", [])
                
                trends = []
                for post in posts:
                    # CHANGE HERE: Hacker News uses the key 'title' inside each hit
                    title = post.get("title")
                    if title:
                        trends.append({"title": title})

                self.logger.info(f"Fetched {len(trends)} trends from Hacker News")
                return trends

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2)
        
        return []