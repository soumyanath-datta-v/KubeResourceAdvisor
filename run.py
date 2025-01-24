from colorama import init, Fore, Style
import argparse
import os
from metric_analyzer.kubernetes_monitor import KubernetesMonitor
from data_fetch_module.MetricsCollector import MetricsCollector

# Initialize colorama
init()

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
        '--duration',
        type=int,
        default=120,
        help='Duration in minutes to collect metrics (default: 120)'
    )
    parser.add_argument(
        '--namespace',
        type=str,
        default='test',
        help='Kubernetes namespace to monitor (default: test)'
    )
    parser.add_argument(
        '--metrics-file',
        type=str,
        required=True,
        help='Path to the metrics file containing pod performance data'
    )
    parser.add_argument(
        '--restarts-file',
        type=str,
        required=True,
        help='Path to the file containing pod restart information'
    )
    return parser.parse_args()

def get_file_paths():
    args = parse_arguments()
    
    # If both arguments provided via CLI, validate and use them
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
    args = parse_arguments()
    
    try:
        # Initialize the metrics collector
        collector = MetricsCollector(
            namespace=args.namespace,
            duration_minutes=args.duration,
            cache_ttl=300
        )
        
        print(f"\n{Fore.GREEN}Starting metrics collection for {args.duration} minutes...{Style.RESET_ALL}")
        collector.log_metrics(metrics_file=args.metrics_file, health_file=args.restarts_file)
        
        print(f"\n{Fore.GREEN}Collection complete. Running analysis...{Style.RESET_ALL}")
        
        # After collection complete, run analysis
        monitor = KubernetesMonitor(
            metrics_file=args.metrics_file,
            restarts_file=args.restarts_file
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
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Collection stopped by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        raise
    finally:
        # Cleanup temporary files
        for file in [args.metrics_file, args.restarts_file]:
            if os.path.exists(file):
                os.remove(file)

if __name__ == "__main__":
    main()
