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
        num_duplicates = 0  # Track the count

        for trend in trends:
            title = trend["title"]

            if title not in seen:
                seen.add(title)
                unique_trends.append(trend)
            else:
                # 👉 ADD IT HERE: Log the specific duplicate title
                self.logger.warning(
                    f"[PROCESSOR WARNING] Duplicate removed: {title}"
                )
                num_duplicates += 1

        # 👉 Optional: Log the total count if any were removed
        if num_duplicates > 0:
            self.logger.info(
                f"[PROCESSOR INFO] Removed {num_duplicates} duplicate trends in total"
            )

        return unique_trends

    def process(self, trends):
        """
        Main processing pipeline.
        """
        self.logger.info("Processing trends (cleaning + structuring)...")
        
        # 1. Capture the original count immediately
        original_count = len(trends)

        # 2. Step 1: Remove duplicates
        trends = self.remove_duplicates(trends)

        # 3. Step 2: Clean titles
        processed_trends = []

        for i, trend in enumerate(trends, start=1):
            cleaned_title = self.clean_text(trend["title"])

            processed_trends.append({
                "id": i,
                "title": cleaned_title
            })

        self.logger.info(f"{len(processed_trends)} trends ready for LLM")

        # 4. Compare against the original_count, not the modified list
        if len(processed_trends) != original_count:
            self.logger.warning(
                f"[PROCESSOR WARNING] Trend count mismatch: "
                f"{original_count} → {len(processed_trends)}"
            )

        return processed_trends