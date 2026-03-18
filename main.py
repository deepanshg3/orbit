from core.utils.logger import get_logger
from configs.settings import settings


logger = get_logger("orbit")


def main():

    logger.info("Orbit AI Growth Engine starting...")
    logger.info(f"Application name: {settings.APP_NAME}")
    logger.info(f"Version: {settings.VERSION}")


if __name__ == "__main__":
    main()