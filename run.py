import argparse
import glob
import os
import shutil
import subprocess
import sys
from datetime import datetime
from metric_analyzer.kubernetes_monitor import KubernetesMonitor

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COLLECT_SCRIPT = os.path.join(SCRIPT_DIR, "collect-metrics.ps1")
DATA_DIR = os.path.join(SCRIPT_DIR, "collected-data")


def get_interactive_input():
    while True:
        metrics_file = input("Enter path to metrics file: ").strip()
        restarts_file = input("Enter path to restarts file: ").strip()

        if os.path.exists(metrics_file) and os.path.exists(restarts_file):
            return metrics_file, restarts_file

        print("\nError: One or both files not found. Please try again.\n")


def collect_metrics_interactive():
    """Prompt for collection parameters."""
    print("\n============================================")
    print(" Kubernetes Resource Advisor - Data Collection")
    print("============================================")

    namespace = input("Enter Kubernetes namespace (e.g. test): ").strip()
    while not namespace:
        namespace = input("Namespace cannot be empty. Enter namespace: ").strip()

    service_names = input(
        "Enter service names (space-separated, e.g. tiger-daemon workflowservice): "
    ).strip()
    while not service_names:
        service_names = input("Service names cannot be empty. Enter service names: ").strip()

    duration = input("Enter collection duration in minutes (e.g. 5): ").strip()
    while not duration.isdigit() or int(duration) <= 0:
        duration = input("Please enter a positive integer for duration (minutes): ").strip()

    return namespace, service_names, int(duration)


def run_collector(namespace: str, service_names: str, duration_minutes: int) -> tuple:
    """Run the PowerShell collector script and return (metrics_file, restarts_file) paths."""
    if not os.path.exists(COLLECT_SCRIPT):
        print(f"Error: Collector script not found at {COLLECT_SCRIPT}")
        sys.exit(1)

    if not shutil.which("kubectl"):
        print("Error: kubectl is not installed or not in PATH.")
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Pre-generate file names matching the PS1 script's naming convention
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metrics_file = os.path.join(DATA_DIR, f"metrics_{timestamp}.txt")
    restarts_file = os.path.join(DATA_DIR, f"restarts_{timestamp}.txt")

    print(f"\nCollecting data for {duration_minutes} minute(s)...")
    print(f"  Metrics  -> {metrics_file}")
    print(f"  Restarts -> {restarts_file}")
    print()

    cmd = [
        "powershell", "-ExecutionPolicy", "Bypass", "-File", COLLECT_SCRIPT,
        "-Namespace", namespace,
        "-ServiceNames", service_names,
        "-DurationMinutes", str(duration_minutes),
    ]

    result = subprocess.run(cmd, cwd=SCRIPT_DIR)

    if result.returncode != 0:
        print(f"\nWarning: Collector script exited with code {result.returncode}")

    # The PS1 script generates its own timestamp — find the actual files if ours
    # don't exist (slight timing difference may cause filename mismatch)
    if not os.path.exists(metrics_file) or not os.path.exists(restarts_file):
        metric_files = sorted(
            glob.glob(os.path.join(DATA_DIR, "metrics_*.txt")),
            key=os.path.getmtime, reverse=True,
        )
        restart_files = sorted(
            glob.glob(os.path.join(DATA_DIR, "restarts_*.txt")),
            key=os.path.getmtime, reverse=True,
        )
        if metric_files and restart_files:
            metrics_file = metric_files[0]
            restarts_file = restart_files[0]
        else:
            print("Error: Output files were not created by the collector.")
            sys.exit(1)

    return metrics_file, restarts_file


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Kubernetes Resource Advisor - Analyzes pod metrics and restarts'
    )
    parser.add_argument(
        '--metrics-file',
        type=str,
        required=False,
        help='Path to the metrics file containing pod performance data'
    )
    parser.add_argument(
        '--restarts-file',
        type=str,
        required=False,
        help='Path to the file containing pod restart information'
    )
    parser.add_argument(
        '--collect',
        action='store_true',
        default=False,
        help='Collect live metrics from the cluster before analysis'
    )
    parser.add_argument(
        '--namespace', '-n',
        type=str,
        required=False,
        help='Kubernetes namespace (used with --collect)'
    )
    parser.add_argument(
        '--services', '-s',
        type=str,
        required=False,
        help='Space-separated service names in quotes (used with --collect)'
    )
    parser.add_argument(
        '--duration', '-d',
        type=int,
        required=False,
        help='Collection duration in minutes (used with --collect)'
    )
    return parser.parse_args()


def get_file_paths():
    args = parse_arguments()

    # Mode 1: Collect live metrics then analyse
    if args.collect:
        if args.namespace and args.services and args.duration:
            namespace, service_names, duration = args.namespace, args.services, args.duration
        else:
            namespace, service_names, duration = collect_metrics_interactive()
        return run_collector(namespace, service_names, duration)

    # Mode 2: Pre-existing files provided via CLI
    if args.metrics_file and args.restarts_file:
        if os.path.exists(args.metrics_file) and os.path.exists(args.restarts_file):
            return args.metrics_file, args.restarts_file

    # Mode 3: Interactive menu
    print("\nHow would you like to provide data?")
    print("  1. Collect live metrics from the cluster")
    print("  2. Use existing data files")
    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        namespace, service_names, duration = collect_metrics_interactive()
        return run_collector(namespace, service_names, duration)
    else:
        return get_interactive_input()


def print_resource_recommendation(resource_type: str, metrics: dict):
    print(f"\n{resource_type.upper()} Resources:")
    print(f"  Recommendation: {metrics['recommendation']}")
    print("  Factors:")
    for factor, value in metrics['factors'].items():
        print(f"    - {factor}: {value:.2f}")
    print("  Forecast:")
    print("    - Next 24h prediction range:")
    forecast = metrics['forecast']
    if forecast and len(forecast) > 0:
        latest = forecast[-1]  # Get last forecast entry directly
        print(f"      Min: {latest['yhat_lower']:.0f}")
        print(f"      Max: {latest['yhat_upper']:.0f}")


def main():
    metrics_file, restarts_file = get_file_paths()

    print("\n============================================")
    print(" Analysing collected data...")
    print("============================================")
    print(f"  Metrics file  : {metrics_file}")
    print(f"  Restarts file : {restarts_file}\n")

    monitor = KubernetesMonitor(
        metrics_file=metrics_file,
        restarts_file=restarts_file
    )
    problematic_services, recommendations = monitor.run_analysis()

    print("\nProblematic Services Analysis")
    print("============================")
    print(f"\nFound {len(problematic_services)} problematic services:")

    if problematic_services:
        for service in problematic_services:
            print(f"- {service}")

        print("\nResource Recommendations")
        print("======================")
        for service, rec in recommendations.items():
            print(f"\nService: {service}")
            print_resource_recommendation('cpu', rec['metrics']['cpu'])
            print_resource_recommendation('memory', rec['metrics']['memory'])
    else:
        print("No problematic services found.")


if __name__ == "__main__":
    main()
