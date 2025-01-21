# KubeResourceAdvisor

A Python-based tool for analyzing and optimizing Kubernetes resource allocations through performance monitoring and intelligent recommendations.

## Project Structure

- `performance_test/` - Core performance analysis modules
  - `kubernetes_monitor.py` - Kubernetes cluster monitoring
  - `health_analyzer.py` - System health analysis
  - `metrics_processor.py` - Process and analyze metrics
  - `metrics_visualizer.py` - Visualization of metrics
  - `data_reader.py` - Data ingestion utilities
  - `models.py` - Data models and structures

- `recommender_system/` - Resource recommendation engine
  - `resource_recommender.py` - Generates resource allocation recommendations

- `visualizations/` - Output directory for generated visualizations

## Getting Started

### Prerequisites

- Python 3.x
- Virtual environment (venv)
- Access to a Kubernetes cluster

### Installation

1. Clone the repository
2. Create and activate virtual environment:
```sh
python -m venv venv
venv/Scripts/activate  # On Windows
pip install pandas matplotlib scikit-learn prophet
python run.py
```

