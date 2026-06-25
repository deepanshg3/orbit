from core.utils.logger import get_logger
from configs.settings import settings
from core.trend_engine.trend_collector import TrendCollector
from core.trend_engine.trend_processor import TrendProcessor
from core.trend_engine.llm_ranker import LLMRanker
from core.content_engine.content_generator import ContentGenerator
from platforms.threads.publisher import ThreadsPublisher
from core.analytics_engine.storage import Storage

# --- NEW IMPORTS ---
from core.strategy_engine.reader import PlaybookReader 
from core.monitoring.tracing import flush_traces

import time
import sys

def main():

    start_time = time.time()

    # Main logger
    main_logger = get_logger("orbit.main")
    main_logger.info("Orbit AI Growth Engine starting...")

    try:
        # ---------------------------------------------------------
        # 0. INITIALIZE STORAGE & FETCH THE BRAIN (STRATEGY PLAYBOOK)
        # ---------------------------------------------------------
        # We initialize storage early so we can pass its Supabase client to the Reader
        storage = Storage(logger=get_logger("orbit.storage"))
        
        playbook_reader = PlaybookReader(storage.client)
        playbook = playbook_reader.get_latest_playbook()

        # ---------------------------------------------------------
        # 1. DEPENDENCY INJECTION
        # ---------------------------------------------------------
        collector = TrendCollector(
            logger=get_logger("orbit.trend_collector"),
            api_url=settings.HN_API_URL,
            user_agent=settings.HN_USER_AGENT
        )

        processor = TrendProcessor(
            logger=get_logger("orbit.trend_processor")
        )

        ranker = LLMRanker(
            logger=get_logger("orbit.llm_ranker")
        )

        content_engine = ContentGenerator(
            logger=get_logger("orbit.content_generator")
        )
        
        # ---------------------------------------------------------
        # 2. FETCH & PROCESS TRENDS
        # ---------------------------------------------------------
        trends = collector.fetch_trends()

        if not trends:
            main_logger.error("CRITICAL: No trends were fetched. Exiting pipeline immediately.")
            sys.exit(1)

        # Slice them HERE so everything following only sees 20 items
        limited_trends = trends[:settings.TOP_TRENDS_LIMIT]

        main_logger.info(f"Displaying top {len(limited_trends)} trends:")
        for i, trend in enumerate(limited_trends, start=1):
            main_logger.info(f"{i}. {trend['title']}")

        # Process ONLY the limited list
        processed_trends = processor.process(limited_trends)

        main_logger.info("Processed Trends:")
        for trend in processed_trends[:settings.TOP_TRENDS_LIMIT]:
            main_logger.info(trend["title"])

        # ---------------------------------------------------------
        # 3. RANK TRENDS (DYNAMIC STRATEGY INJECTED)
        # ---------------------------------------------------------
        # Pass the playbook to guide the ranking math
        ranked_output = ranker.rank(processed_trends, playbook=playbook)

        main_logger.info("Top Ranked Trends:")

        if not ranked_output:
            main_logger.error("No valid LLM output received")
            return

        for item in ranked_output:
            main_logger.info(f"{item.id} | Score: {item.score}")
            main_logger.info(item.title)
            main_logger.info(item.reason)
            main_logger.info("-" * 50)

        # ---------------------------------------------------------
        # 4. GENERATE CONTENT (DYNAMIC STRATEGY INJECTED)
        # ---------------------------------------------------------
        best_trend = ranked_output[0]   # for now pick top 1

        # Pass the playbook to constrain the formatting and hooks
        generated = content_engine.generate(
            trend=best_trend, 
            content_type=best_trend.content_type,
            playbook=playbook
        )

        if generated:
            main_logger.info("Generated Content:")
            main_logger.info(f"Angle: {generated.angle}")
            main_logger.info(f"Hook: {generated.hook}")
            main_logger.info(f"Content: {generated.content}")
            main_logger.info(f"Takeaway: {generated.takeaway}")

        # ---------------------------------------------------------
        # 5. PUBLISH TO THREADS
        # ---------------------------------------------------------
        publisher = ThreadsPublisher()

        if not generated:
            main_logger.error("[PIPELINE] Content generation failed. Skipping publish.")
            return

        post_ids = publisher.publish_thread(generated)

        main_logger.info(f"[THREADS] Thread Post IDs: {post_ids}") 
        
        # ---------------------------------------------------------
        # 6. SAVE TO DATABASE (FEEDBACK ENGINE)
        # ---------------------------------------------------------
        # Save post after publishing
        post_db_id = storage.save_post(generated, post_ids, best_trend)

        # Total time
        total_time = time.time() - start_time
        main_logger.info(f"[PIPELINE] Total execution time: {total_time:.2f}s")

    except Exception as e:
        main_logger.error(f"[CRITICAL ERROR] Orbit pipeline encountered a fatal exception: {str(e)}", exc_info=True)
        sys.exit(1)

    finally:
        # ---------------------------------------------------------
        # 7. OBSERVABILITY FLUSH (DO NOT REMOVE)
        # ---------------------------------------------------------
        main_logger.info("Holding process to flush LangSmith telemetry...")
        flush_traces()
        main_logger.info("Orbit execution complete. Terminating.")

if __name__ == "__main__":
    main()