from telegram_bot import main
from config import setup_development_logging, get_logger

# Set up colored logging
setup_development_logging()
logger = get_logger(__name__)

if __name__ == '__main__':
    logger.info("Starting Personal Assistant v1")
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed with error: {e}", exc_info=True)