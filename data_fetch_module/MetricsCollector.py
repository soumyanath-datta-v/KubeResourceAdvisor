import logging
import time
from kubernetes import client, config
from datetime import datetime, timedelta
from colorama import init, Fore, Style
import platform
import os
from cachetools import TTLCache
from ratelimit import limits, sleep_and_retry

class MetricsCollector:
    # API call limits: 100 calls per minute
    CALLS = 100
    RATE_LIMIT = 60

    def __init__(self, namespace="test", duration_minutes=None, cache_ttl=300):
        self.namespace = namespace
        self.duration_minutes = duration_minutes
        self._setup_logging()
        self._setup_kubernetes()
        self._setup_caching(cache_ttl)
        self.start_time = datetime.now()
        self.end_time = (self.start_time + timedelta(minutes=duration_minutes) 
                        if duration_minutes else None)

    def _setup_logging(self):
        """Configure logging"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _setup_kubernetes(self):
        """Initialize Kubernetes clients"""
        try:
            config.load_kube_config()
            self.v1 = client.CoreV1Api()
            self.custom = client.CustomObjectsApi()
            init()  # Initialize colorama
        except Exception as e:
            self.logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def _setup_caching(self, cache_ttl):
        """Initialize caching"""
        self.metrics_cache = TTLCache(maxsize=100, ttl=cache_ttl)
        self.health_cache = TTLCache(maxsize=100, ttl=cache_ttl)

    @sleep_and_retry
    @limits(calls=CALLS, period=RATE_LIMIT)
    async def get_pod_metrics(self):
        """Fetch pod metrics with rate limiting and caching"""
        cache_key = f"metrics_{self.namespace}"
        if cache_key in self.metrics_cache:
            return self.metrics_cache[cache_key]

        try:
            metrics = self.custom.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=self.namespace,
                plural="pods"
            )
            self.metrics_cache[cache_key] = metrics['items']
            return metrics['items']
        except Exception as e:
            self.logger.error(f"Error fetching metrics: {e}")
            return []

    @sleep_and_retry
    @limits(calls=CALLS, period=RATE_LIMIT)
    async def get_pod_health(self):
        """Fetch pod health with rate limiting and caching"""
        cache_key = f"health_{self.namespace}"
        if cache_key in self.health_cache:
            return self.health_cache[cache_key]

        try:
            pods = self.v1.list_namespaced_pod(namespace=self.namespace)
            self.health_cache[cache_key] = pods.items
            return pods.items
        except Exception as e:
            self.logger.error(f"Error fetching pod health: {e}")
            return []

    def cleanup(self):
        """Cleanup resources"""
        self.metrics_cache.clear()
        self.health_cache.clear()
        self.logger.info("Cleaned up resources")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        if exc_type:
            self.logger.error(f"Error occurred: {exc_val}")
            return False
        return True

    def is_collection_complete(self):
        if not self.duration_minutes:
            return False
        return datetime.now() >= self.end_time

    def get_remaining_time(self):
        if not self.duration_minutes:
            return "∞"
        remaining = self.end_time - datetime.now()
        if remaining.total_seconds() <= 0:
            return "00:00:00"
        return str(remaining).split('.')[0]

    def get_container_metrics(self, pod_metrics):
        """Extract metrics for all containers in a pod"""
        containers = []
        for container in pod_metrics.get('containers', []):
            containers.append({
                'name': container.get('name', 'unknown'),
                'cpu': container.get('usage', {}).get('cpu', '0'),
                'memory': container.get('usage', {}).get('memory', '0')
            })
        return containers

    def get_container_statuses(self, pod):
        """Get status for all containers in a pod"""
        statuses = []
        if pod.status.container_statuses:
            for container in pod.status.container_statuses:
                statuses.append({
                    'name': container.name,
                    'ready': container.ready,
                    'restarts': container.restart_count,
                    'state': next(iter(container.state.to_dict().keys()))
                })
        return statuses

    def log_metrics(self, metrics_file="metrics.txt", health_file="restarts.txt"):
        """Collect metrics for the specified duration with live display"""
        try:
            while not self.is_collection_complete():
                self.clear_console()
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Print header with status
                self.print_header()
                
                # Get and display metrics
                metrics = self.get_pod_metrics()
                pods = self.get_pod_health()
                
                # Display live metrics
                self.print_pod_metrics(metrics)
                self.print_pod_health(pods)
                
                # Log to files
                with open(metrics_file, 'a') as f:
                    for pod in metrics:
                        metrics_line = f"[{timestamp}] {pod['metadata']['name']} {pod['containers'][0]['usage']['cpu']} {pod['containers'][0]['usage']['memory']}"
                        f.write(f"{metrics_line}\n")
                
                with open(health_file, 'a') as f:
                    for pod in pods:
                        restart_count = pod.status.container_statuses[0].restart_count if pod.status.container_statuses else 0
                        health_line = f"[{timestamp}] {pod.metadata.name} {pod.status.phase} {restart_count}"
                        f.write(f"{health_line}\n")
                
                # Show collection progress at bottom
                print(f"\n{Fore.CYAN}Collection Progress:")
                print(f"Elapsed: {self.format_duration()}")
                print(f"Remaining: {self.get_remaining_time()}")
                print(f"Writing to: {metrics_file} and {health_file}{Style.RESET_ALL}")
                
                time.sleep(60)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Collection stopped by user{Style.RESET_ALL}")
            raise
        except Exception as e:
            self.logger.error(f"Error during collection: {e}")
            raise

    def clear_console(self):
        os.system('cls' if platform.system() == 'Windows' else 'clear')

    def format_duration(self):
        duration = datetime.now() - self.start_time
        return f"{duration.seconds // 3600:02d}:{(duration.seconds // 60) % 60:02d}:{duration.seconds % 60:02d}"

    def print_header(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"{Fore.CYAN}=== Kubernetes Resource Monitor ===")
        print(f"Namespace: {self.namespace}")
        print(f"Running Time: {self.format_duration()}")
        print(f"Remaining Time: {self.get_remaining_time()}")
        print(f"Last Update: {current_time}{Style.RESET_ALL}\n")

    def print_pod_metrics(self, metrics):
        print(f"{Fore.GREEN}=== Pod Metrics ==={Style.RESET_ALL}")
        for pod in metrics:
            name = pod['metadata']['name']
            print(f"\nPod: {name}")
            for container in self.get_container_metrics(pod):
                print(f"  Container: {container['name']}")
                print(f"    CPU: {container['cpu']}")
                print(f"    Memory: {container['memory']}")

    def print_pod_health(self, pods):
        print(f"{Fore.YELLOW}=== Pod Health ==={Style.RESET_ALL}")
        for pod in pods:
            name = pod.metadata.name
            phase = pod.status.phase
            print(f"\nPod: {name}")
            print(f"  Phase: {phase}")
            for status in self.get_container_statuses(pod):
                status_color = Fore.GREEN if status['ready'] else Fore.RED
                print(f"  Container: {status['name']}")
                print(f"    State: {status_color}{status['state']}{Style.RESET_ALL}")
                print(f"    Restarts: {Fore.RED if status['restarts'] > 0 else Fore.GREEN}{status['restarts']}{Style.RESET_ALL}")
                print(f"    Ready: {status_color}{status['ready']}{Style.RESET_ALL}")

    def print_live_metrics(self):
        while not self.is_collection_complete():
            self.clear_console()
            self.print_header()
            self.print_pod_metrics(self.get_pod_metrics())
            self.print_pod_health(self.get_pod_health())
            time.sleep(60)
        print(f"\n{Fore.GREEN}Collection completed after {self.duration_minutes} minutes{Style.RESET_ALL}")
