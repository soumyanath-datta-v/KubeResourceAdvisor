from datetime import datetime
from typing import List, Optional
import pandas as pd
import re
from logs.log_config import setup_logging
from .models import PodMetrics

class MetricsProcessor:
    def __init__(self, date: str = None):
        self.date = date or datetime.now().strftime('%Y-%m-%d')
        self.logger = setup_logging()
    
    def _parse_metric_line(self, line: str, timestamp: datetime) -> PodMetrics:
        parts = line.split()
        if len(parts) >= 3:
            return PodMetrics(
                name=" ".join(parts[:-2]),
                cpu=parts[-2],
                memory=parts[-1],
                timestamp=timestamp
            )
        return None

    def process_metrics(self, lines: List[str]) -> List[PodMetrics]:
        if not lines:
            self.logger.warning("No metrics data provided")
            return []
            
        metrics = []
        
        for line in lines:
            line = line.strip()
            timestamp_match = re.match(r'\[([\d:]+)\]', line)
            
            if not timestamp_match:
                continue
                
            try:
                time_str = timestamp_match.group(1)
                current_timestamp = pd.to_datetime(f"{self.date} {time_str}")
                line = re.sub(r'\[[\d:]+\]\s*', '', line)
                
                if "NAME" not in line and line.strip():
                    metric = self._parse_metric_line(line, current_timestamp)
                    if metric:
                        metrics.append(metric)
            except ValueError as e:
                self.logger.error(f"Error parsing timestamp: {self.date} {time_str}")
            except Exception as e:
                self.logger.error(f"Unexpected error processing line: {line}", exc_info=True)
        
        self.logger.info(f"Processed {len(metrics)} metrics")
        return metrics
