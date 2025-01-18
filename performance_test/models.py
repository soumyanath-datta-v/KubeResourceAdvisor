from dataclasses import dataclass
from typing import List, Protocol
from datetime import datetime
import logging

@dataclass
class PodMetrics:
    name: str
    cpu: str
    memory: str
    timestamp: str

@dataclass
class PodHealth:
    name: str
    restarts: int
    status: str
