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
            response = requests.get(self.api_url, headers=headers, timeout=10)

            response.raise_for_status()

            data = response.json()

            posts = data["data"]["children"]

            trends = []

            for post in posts:
                title = post["data"]["title"]
                trends.append({"title": title})

            self.logger.info(f"Fetched {len(trends)} trends")
            return trends

        except requests.exceptions.Timeout:
            self.logger.error("Request to Reddit timed out")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")

        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")

        return []