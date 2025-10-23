import logging
import sys

def setup_logger():
    """
    setting up a logger that outputs to both console and file.
    """
    # Create logger object
    logger = logging.getLogger("ai_agent_logger")
    logger.setLevel(logging.DEBUG)  # Set logger's minimum processing level to DEBUG

    # Avoid adding handlers multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # --- Console Handler ---
    # Responsible for outputting logs to the terminal
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)  # Console only shows INFO and above messages
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # --- File Handler ---
    # Responsible for writing logs to a file
    fh = logging.FileHandler('development.log', mode='a', encoding='utf-8')
    fh.setLevel(logging.DEBUG)  # File records all DEBUG and above messages
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

# Create a globally available logger instance
log = setup_logger()