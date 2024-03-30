import os
import atexit
import logging
from logging.handlers import RotatingFileHandler

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
log_folder_path = os.path.join(parent_dir, 'logfile')
log_file = os.path.join(log_folder_path, 'app.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def close_logger_handlers():
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)

atexit.register(close_logger_handlers)
