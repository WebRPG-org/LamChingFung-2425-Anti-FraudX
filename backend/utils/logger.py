import logging
import sys
import os

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
    # Use /tmp directory or disable file logging in Docker
    enable_file_log = os.getenv('ENABLE_FILE_LOG', '0') == '1'
    
    if enable_file_log:
        try:
            log_dir = os.getenv('LOG_DIR', '/tmp')
            log_file = os.path.join(log_dir, 'development.log')
            fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            fh.setLevel(logging.DEBUG)  # File records all DEBUG and above messages
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            # If file logging fails, just use console logging
            logger.warning(f"Unable to create file handler: {e}, using console logging only")

    return logger

# Create a globally available logger instance
log = setup_logger()