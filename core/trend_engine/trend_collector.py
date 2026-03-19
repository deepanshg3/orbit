import requests


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
        Fetch trending posts from Reddit.
        """

        self.logger.info("Fetching trends from Reddit...")

        headers = {
            "User-Agent": self.user_agent
        }

        try:
            response = requests.get(self.api_url, headers=headers)

            if response.status_code != 200:
                self.logger.error(f"Failed to fetch data: {response.status_code}")
                return []

            data = response.json()

            posts = data["data"]["children"]

            trends = []

            for post in posts:
                title = post["data"]["title"]

                trends.append({
                    "title": title
                })

            self.logger.info(f"Fetched {len(trends)} trends")

            return trends

        except Exception as e:
            self.logger.error(f"Error fetching trends: {str(e)}")
            return []