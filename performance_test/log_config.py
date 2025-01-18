import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging():
    """Configure logging with rotating file handler."""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = RotatingFileHandler(
            os.path.join(log_dir, 'performance_test.log'),
            maxBytes=1024*1024,
            backupCount=5
        )
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
