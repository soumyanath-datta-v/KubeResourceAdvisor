import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import List
from logs.log_config import setup_logging
from .models import PodMetrics

class MetricsVisualizer:
    def __init__(self):
        self.base_output_dir = "visualizations"
        self.logger = setup_logging()
        os.makedirs(self.base_output_dir, exist_ok=True)
    
    def _get_service_dir(self, service_name: str) -> str:
        """Create and return service-specific output directory."""
        service_dir = os.path.join(self.base_output_dir, service_name)
        os.makedirs(service_dir, exist_ok=True)
        self.logger.debug(f"Created output directory for service: {service_dir}")
        return service_dir

    def visualize_metrics(self, metrics: List[PodMetrics], service_name: str):
        """
        Visualize metrics for a specific service.
        
        Args:
            metrics (List[PodMetrics]): Metrics data to visualize
            service_name (str): Name of the service being analyzed
        
        Returns:
            None
        """
        if not metrics:
            self.logger.warning(f"No metrics to visualize for service {service_name}")
            return
            
        self.logger.info(f"Creating visualization for service: {service_name}")
        
        service_dir = self._get_service_dir(service_name)
        
        # Create DataFrame
        df = pd.DataFrame([vars(m) for m in metrics])
        self.logger.debug(f"Created DataFrame with columns: {df.columns.tolist()}")
        
        # Create subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Plot CPU
        for pod in df['name'].unique():
            pod_data = df[df['name'] == pod]
            cpu_values = pod_data['cpu'].str.replace('m', '').astype(float)
            ax1.plot(pod_data['timestamp'], cpu_values, label=pod, marker='.')
        
        ax1.set_title(f'{service_name} - CPU Usage Over Time')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('CPU (millicores)')
        ax1.grid(True)
        ax1.legend()
        
        # Plot Memory
        for pod in df['name'].unique():
            pod_data = df[df['name'] == pod]
            memory_values = pod_data['memory'].str.replace('Mi', '').astype(float)
            ax2.plot(pod_data['timestamp'], memory_values, label=pod, marker='.')
        
        ax2.set_title(f'{service_name} - Memory Usage Over Time')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Memory (Mi)')
        ax2.grid(True)
        ax2.legend()
        
        plt.tight_layout()
        output_path = os.path.join(service_dir, 'metrics.png')
        plt.savefig(output_path)
        plt.close()
        
        self.logger.info(f"Saved metrics visualization to {output_path}")
    
    def _plot_cpu(self, ax, df: pd.DataFrame):
        for pod in df['name'].unique():
            pod_data = df[df['name'] == pod]
            cpu_values = pod_data['cpu'].str.replace('m', '').astype(float)
            ax.plot(pod_data['timestamp'], cpu_values, label=pod.split('-')[-1], marker='.')
        
        ax.set_title('CPU Usage')
        ax.set_ylabel('CPU (millicores)')
        ax.grid(True)
        ax.legend()
    
    def _plot_memory(self, ax, df: pd.DataFrame):
        for pod in df['name'].unique():
            pod_data = df[df['name'] == pod]
            memory_values = pod_data['memory'].str.replace('Mi', '').astype(float)
            ax.plot(pod_data['timestamp'], memory_values, label=pod.split('-')[-1], marker='.')
        
        ax.set_title('Memory Usage')
        ax.set_ylabel('Memory (Mi)')
        ax.grid(True)
        ax.legend()

    def create_resource_analysis(self, metrics: List[PodMetrics], service_name: str):
        """Create detailed resource usage visualizations for a given service.
        This method generates a comprehensive visualization of resource metrics including:
        1. Resource Distribution Plot (CPU and Memory usage distribution)
        2. Usage Patterns over time with average and peak CPU usage
        3. Pod scaling patterns showing pod count over time
        4. Resource efficiency distribution
        Args:
            metrics (List[PodMetrics]): List of pod metric objects containing resource usage data
            service_name (str): Name of the service to analyze
        Returns:
            None. Saves the generated plot as 'resource_analysis.png' in the service directory
        The generated plot contains four subplots:
        - Top left: Box plot showing CPU and Memory usage distribution
        - Top right: Time series plot of CPU usage with average and peak lines
        - Bottom left: Pod count variation over time
        - Bottom right: Histogram showing resource efficiency distribution
        """
        """Create detailed resource usage visualizations."""
        service_dir = self._get_service_dir(service_name)
        df = pd.DataFrame([vars(m) for m in metrics])
        
        _ = plt.figure(figsize=(20, 15))
        
        # Resource Distribution Plot
        ax1 = plt.subplot(221)
        cpu_values = df['cpu'].str.replace('m', '').astype(float)
        memory_values = df['memory'].str.replace('Mi', '').astype(float)
        ax1.boxplot([cpu_values, memory_values], labels=['CPU', 'Memory'])
        ax1.set_title('Resource Usage Distribution')
        
        # Usage Patterns
        ax2 = plt.subplot(222)
        ax2.plot(df['timestamp'], cpu_values, label='CPU Usage')
        ax2.axhline(y=cpu_values.mean(), color='r', linestyle='--', label='Avg CPU')
        ax2.axhline(y=cpu_values.max(), color='g', linestyle='--', label='Peak CPU')
        ax2.set_title('Resource Usage Patterns')
        ax2.legend()
        
        # Pod Scaling
        ax3 = plt.subplot(223)
        pod_counts = df.groupby('timestamp')['name'].nunique()
        ax3.plot(pod_counts.index, pod_counts.values)
        ax3.set_title('Pod Count Over Time')
        
        # Resource Efficiency
        ax4 = plt.subplot(224)
        efficiency_ratio = (cpu_values / cpu_values.max() * 100)
        ax4.hist(efficiency_ratio, bins=20)
        ax4.set_title('Resource Efficiency Distribution')
        ax4.set_xlabel('Efficiency %')
        
        plt.suptitle(f'Resource Analysis - {service_name}')
        plt.tight_layout()
        
        output_path = os.path.join(service_dir, 'resource_analysis.png')
        plt.savefig(output_path)
        plt.close()
        self.logger.info(f"Saved resource analysis to {output_path}")
