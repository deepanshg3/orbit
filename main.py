from core.utils.logger import get_logger
from configs.settings import settings
from core.trend_engine.trend_collector import TrendCollector
from core.trend_engine.trend_processor import TrendProcessor

logger = get_logger("orbit")


def main():

    logger.info("Orbit AI Growth Engine starting...")

    # Dependency Injection
    collector = TrendCollector(
        logger=logger,
        api_url=settings.REDDIT_API_URL,
        user_agent=settings.USER_AGENT
    )

    trends = collector.fetch_trends()

    logger.info("Top Trends:")

    for i, trend in enumerate(trends[:settings.TOP_TRENDS_LIMIT], start=1):
        logger.info(f"{i}. {trend['title']}")

    processor = TrendProcessor(logger=logger)

    processed_trends = processor.process(trends)

    logger.info("Processed Trends:")

    for trend in processed_trends[:5]:
        logger.info(trend["title"])


if __name__ == "__main__":
    main()