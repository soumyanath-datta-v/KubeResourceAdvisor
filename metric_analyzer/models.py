from dataclasses import dataclass

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
