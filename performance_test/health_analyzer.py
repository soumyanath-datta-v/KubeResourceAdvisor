
from typing import Set, List
import re
from .log_config import setup_logging

class HealthAnalyzer:
    def analyze_pods(self, lines: List[str]) -> Set[str]:
        problematic_services = set()
        self.logger = setup_logging()
        
        for line in lines:
            if "NAME" not in line and line.strip():
                parts = line.strip().split()
                if len(parts) >= 6:
                    name = parts[1]
                    status = parts[3]
                    restarts = parts[4]
                    self.logger.info(f"Pod: {name}, Status: {status}, Restarts: {restarts}")
                    service_name = re.match(r'([\w-]+)-[a-f0-9]', name)
                    self.logger.debug(f"Processing pod {name} with status {status} and restarts {restarts}")
                    if service_name and (int(restarts.split()[0]) > 0 or status == "CrashLoopBackOff"):
                        problematic_services.add(service_name.group(1))
        
        return problematic_services
