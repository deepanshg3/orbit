from core.utils.logger import get_logger
from configs.settings import settings
from core.utils.logger import get_logger
from core.interaction_engine.fetcher import InteractionFetcher
from core.interaction_engine.filter import InteractionFilter
from core.interaction_engine.selector import InteractionSelector
from core.interaction_engine.responder import InteractionResponder
from core.interaction_engine.memory import InteractionMemory
from core.interaction_engine.replier import InteractionReplier
from platforms.threads.client import ThreadsClient
from core.analytics_engine.storage import Storage
import time


def run_interaction():

    pipeline_start_time = time.time() # <--- START MASTER CLOCK

    logger = get_logger("orbit.interaction")

    # -------------------------------
    # SAFETY CHECK
    # -------------------------------
    if not settings.ENABLE_INTERACTIONS:
        logger.info("[INTERACTION] Disabled via settings")
        return

    logger.info("[INTERACTION] Starting interaction pipeline...")

    # -------------------------------
    # INIT DEPENDENCIES
    # -------------------------------
    storage = Storage(logger)
    client = ThreadsClient()

    fetcher = InteractionFetcher(logger)
    memory = InteractionMemory(logger, storage.client)
    filterer = InteractionFilter(logger, memory)
    selector = InteractionSelector(logger)
    responder = InteractionResponder(logger)
    replier = InteractionReplier(logger, client)

    # -------------------------------
    # STEP 1: FETCH POSTS
    # -------------------------------
    fetcher_start_time = time.time() 
    posts = fetcher.fetch_posts()

    if not posts:
        logger.info("[INTERACTION] No posts fetched")
        return
    
    fetcher_duration = time.time() - fetcher_start_time
    
    logger.info(f"[FETCHER] Fetching posts took {fetcher_duration:.2f} seconds")

    # -------------------------------
    # STEP 2: FILTER POSTS
    # -------------------------------
    posts = filterer.filter_posts(posts)

    if not posts:
        logger.info("[INTERACTION] No posts after filtering")
        return

    # -------------------------------
    # STEP 3: SELECT TOP POSTS (LLM)
    # -------------------------------
    llm_start_time = time.time() # <--- START LLM CLOCK
    top_posts = selector.select_top_posts(posts)

    if not top_posts:
        logger.info("[INTERACTION] Selector returned no posts")
        return
    llm_duration = time.time() - llm_start_time
    logger.info(f"[SELECTOR] LLM processing took {llm_duration:.2f} seconds")

    # Limit replies per run
    posts_to_reply = top_posts[:settings.MAX_REPLIES_PER_RUN]

    logger.info(f"[INTERACTION] Will reply to {len(posts_to_reply)} posts")

    # -------------------------------
    # STEP 4: LOOP & REPLY
    # -------------------------------
    for post in posts_to_reply:

        post_id = post["id"]
        post_text = post["text"]
        score = post.get("score")
        reason = post.get("reason")

        logger.info(f"[INTERACTION] Processing post {post_id}")

        # -------------------------------
        # Generate reply
        # -------------------------------
        reply = responder.generate_reply(
            post_text=post_text,
            reason=reason
        )

        if not reply:
            logger.warning(f"[INTERACTION] Skipping post {post_id} (no reply)")
            continue

        # -------------------------------
        # Post reply
        # -------------------------------
        # -------------------------------
        # Post reply (Using new Replier module)
        # -------------------------------
        reply_id = replier.post_reply(post_id, reply)

        if not reply_id:
            logger.error(f"[INTERACTION] Skipping DB save due to publishing failure on {post_id}")
            continue

        logger.info(f"[INTERACTION] Success! Reply live at ID: {reply_id}")

        # -------------------------------
        # Save to DB
        # -------------------------------
        memory.save_interaction(
            post_id=post_id,
            reply_text=reply,
            score=score,
            reason=reason,
            our_reply_id=reply_id
        )

    logger.info("[INTERACTION] Pipeline completed")
    pipeline_duration = time.time() - pipeline_start_time # <--- END MASTER CLOCK
    logger.info(f"[INTERACTION] Pipeline completed successfully in {pipeline_duration:.2f} seconds")


if __name__ == "__main__":
    run_interaction()
