import argparse
import os
from metric_analyzer.kubernetes_monitor import KubernetesMonitor

def get_interactive_input():
    while True:
        metrics_file = input("Enter path to metrics file: ").strip()
        restarts_file = input("Enter path to restarts file: ").strip()
        
        if os.path.exists(metrics_file) and os.path.exists(restarts_file):
            return metrics_file, restarts_file
        
        print("\nError: One or both files not found. Please try again.\n")

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
    return parser.parse_args()

def get_file_paths():
    args = parse_arguments()
    
    # If both arguments provided via CLI, validate and use them
    if args.metrics_file and args.restarts_file:
        if os.path.exists(args.metrics_file) and os.path.exists(args.restarts_file):
            return args.metrics_file, args.restarts_file
    
    # Fall back to interactive input
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
