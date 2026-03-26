from platforms.threads.client import ThreadsClient
from core.utils.logger import get_logger
import time
import re

logger = get_logger(__name__)


class ThreadsPublisher:

    def __init__(self):
        self.client = ThreadsClient()

    # -------------------------------
    # PUBLIC ENTRY POINT
    # -------------------------------
    def publish(self, generated_content) -> list:
        """
        Routes publishing based on content type.
        """
        if generated_content.content_type in ["short", "medium"]:
            return self.publish_single(generated_content)

        elif generated_content.content_type == "thread":
            return self.publish_thread(generated_content)

        else:
            raise ValueError(f"Unsupported content_type: {generated_content.content_type}")

    # -------------------------------
    # SINGLE POST (SHORT / MEDIUM)
    # -------------------------------
    def publish_single(self, generated_content) -> list:
        try:
            # For short/medium → ONLY content (no hook, no takeaway)
            content = generated_content.content

            # If mistakenly list, join it
            if isinstance(content, list):
                content = " ".join(content)

            # Remove any accidental numbering
            content = re.sub(r"^\d+/\s*", "", content).strip()

            # Enforce Threads limit
            if len(content) > 500:
                logger.warning(f"[THREADS WARNING] Post too long ({len(content)}), trimming")
                content = content[:500]

            logger.info(f"[THREADS] Publishing single post ({len(content)} chars)")

            # Step 1: Create container
            container_response = self.client.post(
                "me/threads",
                data={
                    "media_type": "TEXT",
                    "text": content
                }
            )

            creation_id = container_response.get("id")

            # Step 2: Publish
            publish_response = self.client.post(
                "me/threads_publish",
                data={"creation_id": creation_id}
            )

            post_id = publish_response.get("id")

            logger.info(f"[THREADS] Posted single post ID: {post_id}")

            return [post_id]

        except Exception as e:
            logger.error(f"[THREADS] Single post failed: {str(e)}")
            raise

    # -------------------------------
    # THREAD POST (MULTI-PART)
    # -------------------------------
    def publish_thread(self, generated_content) -> list:
        try:
            # -------------------------------
            # Build structured thread
            # -------------------------------
            thread_parts = []

            # 1. Hook
            thread_parts.append(generated_content.hook)

            # 2. Main content
            if isinstance(generated_content.content, list):
                thread_parts.extend(generated_content.content)
            else:
                thread_parts.append(generated_content.content)

            # 3. Takeaway
            thread_parts.append(generated_content.takeaway)

            total_parts = len(thread_parts)

            logger.info(f"[THREADS] Total posts in thread: {total_parts}")

            # -------------------------------
            # Publish thread
            # -------------------------------
            post_ids = []
            reply_to_id = None

            for idx, chunk in enumerate(thread_parts):
                logger.info(f"[THREADS] Posting part {idx+1}/{total_parts}")

                # Clean existing numbering
                clean_chunk = re.sub(r"^\d+/\s*", "", chunk).strip()

                # Add numbering (UX)
                numbered_chunk = f"{idx+1}/{total_parts}\n{clean_chunk}"

                # Enforce 500 char limit
                if len(numbered_chunk) > 500:
                    logger.warning(
                        f"[THREADS WARNING] Chunk too long ({len(numbered_chunk)} chars), trimming"
                    )
                    numbered_chunk = numbered_chunk[:500]

                container_data = {
                    "media_type": "TEXT",
                    "text": numbered_chunk,
                }

                # Thread chaining
                if reply_to_id:
                    container_data["reply_to_id"] = reply_to_id

                # Step 1: Create container
                container_response = self.client.post(
                    "me/threads",
                    data=container_data
                )

                creation_id = container_response.get("id")

                # Step 2: Publish with retry
                MAX_RETRIES = 3
                RETRY_DELAY = 2

                publish_response = None

                for attempt in range(MAX_RETRIES):
                    try:
                        time.sleep(RETRY_DELAY)

                        publish_response = self.client.post(
                            "me/threads_publish",
                            data={"creation_id": creation_id}
                        )

                        logger.info(f"[THREADS] Publish succeeded on attempt {attempt+1}")
                        break

                    except Exception as e:
                        logger.warning(
                            f"[THREADS] Publish retry {attempt+1}/{MAX_RETRIES}: {str(e)}"
                        )

                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                            logger.error("[THREADS] Rate limit hit. Stopping publishing.")
                            raise

                        if attempt == MAX_RETRIES - 1:
                            raise

                post_id = publish_response.get("id")

                post_ids.append(post_id)
                reply_to_id = post_id

                logger.info(f"[THREADS] Posted part ID: {post_id}")

            return post_ids

        except Exception as e:
            logger.error(f"[THREADS] Thread publishing failed: {str(e)}")
            raise