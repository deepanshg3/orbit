from core.utils.logger import get_logger
from configs.settings import settings
from core.trend_engine.trend_collector import TrendCollector
from core.trend_engine.trend_processor import TrendProcessor
from core.trend_engine.llm_ranker import LLMRanker

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

    for trend in processed_trends[:settings.TOP_TRENDS_LIMIT]:
        logger.info(trend["title"])

    ranker = LLMRanker(logger=logger)

    ranked_output = ranker.rank(processed_trends)

    logger.info("Top Ranked Trends:")

    if not ranked_output:
        logger.error("No valid LLM output received")
        return
 
    for item in ranked_output:
        logger.info(f"{item['id']} | Score: {item['score']}")
        logger.info(item["title"])
        logger.info(item["reason"])
        logger.info("-" * 50)


if __name__ == "__main__":
    main()