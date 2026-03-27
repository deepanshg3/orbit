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
        Fetch trending posts from Reddit with automatic retries for server errors.
        """
        self.logger.info("Fetching trends from Reddit...")

        headers = {
            "User-Agent": self.user_agent
        }

        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = requests.get(self.api_url, headers=headers, timeout=10)

                # Catch Reddit's temporary server overloads (503) or rate limits (429)
                if response.status_code in [503, 429]:
                    self.logger.warning(
                        f"Reddit servers busy (Error {response.status_code}). "
                        f"Retrying in 5 seconds... (Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(5)
                    continue  # Skip the rest of this loop and try the request again

                # For any other error (like a 403 or 404), raise it normally
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
                break  # Exit the loop on a hard timeout

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request failed: {str(e)}")
                break  # Exit the loop on other hard request errors

            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                break  # Exit the loop on unexpected Python errors

        self.logger.error("Failed to fetch trends after multiple attempts.")
        return []