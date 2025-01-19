import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(log_level: str = "INFO"):
    """Configure logging with rotating file handler."""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=getattr(logging, log_level),
        handlers=[
            RotatingFileHandler(
                os.path.join(log_dir, 'performance_test.log'),
                maxBytes=10485760,  # 10MB
                backupCount=5
            )
        ]
    )
    
    logger = logging.getLogger(__name__)
    return logger
