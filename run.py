from performance_test.kubernetes_monitor import KubernetesMonitor

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
    monitor = KubernetesMonitor(
        metrics_file="Input/performance-test.txt",
        restarts_file="Input/performance-test-restarts-end.txt",
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
