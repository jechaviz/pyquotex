import logging
logger = logging.getLogger(__name__)

def setup_logger(log_level=logging.DEBUG, log_file=None):
  # log_level: [DEBUG, INFO, WARNING, ERROR, etc.]
  # log_file: log file path
  formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
  handler = logging.StreamHandler()
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  logger.setLevel(log_level)
  if log_file:
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

setup_logger()  # Configure with defaults
