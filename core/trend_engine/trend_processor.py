import re


class TrendProcessor:
    """
    Prepares trend data for LLM processing.
    """

    def __init__(self, logger):
        self.logger = logger

    def clean_text(self, text):
        """
        Basic cleaning (light, not aggressive).
        """
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)  # remove extra spaces
        return text

    def remove_duplicates(self, trends):
        """
        Remove duplicate titles.
        """
        seen = set()
        unique_trends = []

        for trend in trends:
            title = trend["title"]

            if title not in seen:
                seen.add(title)
                unique_trends.append(trend)

        return unique_trends

    def process(self, trends):
        """
        Main processing pipeline.
        """

        self.logger.info("Processing trends (cleaning + structuring)...")

        # Step 1: Remove duplicates
        trends = self.remove_duplicates(trends)

        # Step 2: Clean titles
        processed_trends = []

        for i, trend in enumerate(trends, start=1):
            cleaned_title = self.clean_text(trend["title"])

            processed_trends.append({
                "id": i,
                "title": cleaned_title
            })

        self.logger.info(f"{len(processed_trends)} trends ready for LLM")

        return processed_trends