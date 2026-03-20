from core.utils.logger import get_logger
from configs.settings import settings
from core.trend_engine.trend_collector import TrendCollector
from core.trend_engine.trend_processor import TrendProcessor
from core.trend_engine.llm_ranker import LLMRanker


def main():

    # Main logger
    main_logger = get_logger("orbit.main")

    main_logger.info("Orbit AI Growth Engine starting...")

    # Dependency Injection with module-specific loggers
    collector = TrendCollector(
        logger=get_logger("orbit.trend_collector"),
        api_url=settings.REDDIT_API_URL,
        user_agent=settings.USER_AGENT
    )

    processor = TrendProcessor(
        logger=get_logger("orbit.trend_processor")
    )

    ranker = LLMRanker(
        logger=get_logger("orbit.llm_ranker")
    )

    # Fetch trends
    trends = collector.fetch_trends()

    main_logger.info("Top Trends:")

    for i, trend in enumerate(trends[:settings.TOP_TRENDS_LIMIT], start=1):
        main_logger.info(f"{i}. {trend['title']}")

    # Process trends
    processed_trends = processor.process(trends)

    main_logger.info("Processed Trends:")

    for trend in processed_trends[:settings.TOP_TRENDS_LIMIT]:
        main_logger.info(trend["title"])

    # Rank trends
    ranked_output = ranker.rank(processed_trends)

    main_logger.info("Top Ranked Trends:")

    if not ranked_output:
        main_logger.error("No valid LLM output received")
        return

    for item in ranked_output:
        main_logger.info(f"{item.id} | Score: {item.score}")
        main_logger.info(item.title)
        main_logger.info(item.reason)
        main_logger.info("-" * 50)


if __name__ == "__main__":
    main()