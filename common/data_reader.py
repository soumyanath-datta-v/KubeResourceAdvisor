from typing import List
from logs.log_config import setup_logging

class DataReader:
    def __init__(self, perf_file: str, health_file: str):
        self.perf_file = perf_file
        self.health_file = health_file
        self.logger = setup_logging()
    
    def read_performance_data(self) -> List[str]:
        try:
            with open(self.perf_file, 'r') as f:
                self.logger.info(f"Reading performance data from {self.perf_file}")
                return f.readlines()
        except FileNotFoundError:
            self.logger.error(f"Performance file not found: {self.perf_file}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading performance file: {e}")
            return []
    
    def read_health_data(self) -> List[str]:
        try:
            with open(self.health_file, 'r') as f:
                self.logger.info(f"Reading health data from {self.health_file}")
                return f.readlines()
        except FileNotFoundError:
            self.logger.error(f"Health file not found: {self.health_file}")
            return []
        except Exception as e:
            self.logger.error(f"Error reading health file: {e}")
            return []
