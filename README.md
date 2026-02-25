# KubeResourceAdvisor

A Python-based tool for analyzing and optimizing Kubernetes resource allocations through performance monitoring and intelligent recommendations. Automatically collects metrics from your Kubernetes cluster, identifies problematic services, and provides data-driven resource recommendations.

## Features

- **Automated Data Collection**: PowerShell script that captures live `kubectl top pods` and `kubectl get po` metrics at 30-second intervals
- **Health Analysis**: Identifies services with restarts or CrashLoopBackOff status
- **Time-Series Forecasting**: Uses Prophet for 24-hour resource usage prediction
- **Resource Recommendations**: Generates CPU and memory recommendations based on usage patterns
- **Visualization**: Creates charts for resource usage trends

## Project Structure

- `run.py` - Main entry point with integrated collection and analysis
- `collect-metrics.ps1` - PowerShell script for capturing Kubernetes metrics
- `common/` - Shared utilities
  - `data_reader.py` - File ingestion utilities
- `metric_analyzer/` - Core analysis modules
  - `kubernetes_monitor.py` - Orchestrates monitoring and analysis
  - `health_analyzer.py` - Health status analysis
  - `metrics_processor.py` - Parses and processes metrics
  - `metrics_visualizer.py` - Generates visualizations
  - `models.py` - Data models
- `recommender_system/` - Resource recommendation engine
  - `resource_recommender.py` - Prophet-based forecasting and recommendations
- `logs/` - Logging configuration
- `collected-data/` - Output directory for collected metrics (auto-created)
- `visualizations/` - Output directory for generated charts

## Prerequisites

- **Python 3.8+** with `venv` support
- **kubectl** installed and configured with access to your Kubernetes cluster
- **PowerShell** (Windows) or **PowerShell Core** (cross-platform)
- Python packages: `pandas`, `matplotlib`, `scikit-learn`, `prophet`

## Installation

1. Clone the repository:
```sh
git clone <repository-url>
cd KubeResourceAdvisor
```

2. Create and activate virtual environment:
```sh
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```sh
pip install pandas matplotlib scikit-learn prophet
```

## Usage

### Mode 1: Collect + Analyse (Fully CLI)

Collect live metrics and immediately analyze them with all parameters via command line:

```sh
python run.py --collect -n <namespace> -s "<service-names>" -d <duration-minutes>
```

**Example:**
```sh
python run.py --collect -n test -s "tiger-daemon workflowservice" -d 5
```

### Mode 2: Collect + Analyse (Interactive)

Run with `--collect` flag and interactively provide collection parameters:

```sh
python run.py --collect
```

You'll be prompted for:
- Kubernetes namespace
- Service names (space-separated)
- Collection duration (minutes)

### Mode 3: Analyse Existing Files

Process pre-collected metrics and restart files:

```sh
python run.py --metrics-file <path-to-metrics.txt> --restarts-file <path-to-restarts.txt>
```

**Example:**
```sh
python run.py --metrics-file collected-data/metrics_20260225_142158.txt --restarts-file collected-data/restarts_20260225_142158.txt
```

### Mode 4: Fully Interactive

Run without arguments to get an interactive menu:

```sh
python run.py
```

Choose between:
1. Collect live metrics from cluster
2. Use existing data files

## PowerShell Collector Script

The `collect-metrics.ps1` script can also be run standalone:

```powershell
.\collect-metrics.ps1 -Namespace <namespace> -ServiceNames "<services>" -DurationMinutes <minutes>
```

**Example:**
```powershell
.\collect-metrics.ps1 -Namespace test -ServiceNames "tiger-daemon workflowservice" -DurationMinutes 10
```

### Output Format

The collector generates two files in `collected-data/`:

- **`metrics_YYYYMMDD_HHMMSS.txt`**: CPU and memory usage with timestamps
  ```
  [14:30:00] tiger-daemon-7b844fcf65-kqns4    13m    225Mi
  [14:30:00] workflowservice-57646fd97c-nxr58 6m     574Mi
  ```

- **`restarts_YYYYMMDD_HHMMSS.txt`**: Pod status, restarts, and age
  ```
  1 tiger-daemon-7b844fcf65-kqns4      2/2  Running  0                123m
  2 workflowservice-57646fd97c-zpwnc   2/2  Running  1 (5d22h ago)    6d1h
  ```

## Output

The tool generates:

1. **Console output**: Problematic services list with CPU/memory recommendations
2. **Visualizations** (in `visualizations/`):
   - Resource usage charts
   - Trend analysis graphs

## CLI Arguments Reference

| Argument | Short | Description |
|----------|-------|-------------|
| `--collect` | - | Enable live data collection mode |
| `--namespace` | `-n` | Kubernetes namespace (with --collect) |
| `--services` | `-s` | Space-separated service names in quotes (with --collect) |
| `--duration` | `-d` | Collection duration in minutes (with --collect) |
| `--metrics-file` | - | Path to existing metrics file |
| `--restarts-file` | - | Path to existing restarts file |

## Troubleshooting

**"kubectl is not installed or not in PATH"**
- Ensure `kubectl` is installed and accessible from your terminal

**"Collector script exited with code 1"**
- Verify namespace exists: `kubectl get namespaces`
- Check service names match pods: `kubectl get pods -n <namespace>`
- Ensure you have permissions to query the cluster

**No problematic services found**
- This means no services had restarts or crashes in the last 2 hours
- Try collecting data over a longer period to capture more events

## License

[Add your license here]

