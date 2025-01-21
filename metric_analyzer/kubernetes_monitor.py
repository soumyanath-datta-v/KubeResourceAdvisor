from datetime import datetime
from typing import List, Set, Dict, Any
import re
import logging
import pandas as pd
from common.data_reader import DataReader
from metric_analyzer.models import PodMetrics
from recommender_system.resource_recommender import ResourceRecommenderProphet
from .metrics_visualizer import MetricsVisualizer
from .metrics_processor import MetricsProcessor

class KubernetesMonitor:
    def __init__(self, 
                 metrics_file: str, 
                 restarts_file: str):
        self.metrics_file = metrics_file
        self.restarts_file = restarts_file
        self.reader = DataReader(self.metrics_file, self.restarts_file)
        self.processor = MetricsProcessor(datetime.now().strftime("%Y-%m-%d"))
        self.visualizer = MetricsVisualizer()
        self.logger = logging.getLogger(__name__)

    def _extract_service_name(self, pod_name: str) -> str:
        pattern = r'^([a-zA-Z-]+)-[a-f0-9]{8,10}-[a-z0-9]{5}'
        match = re.match(pattern, pod_name)
        return match.group(1) if match else pod_name
    
    def _process_health_data(self, health_data: List[str]) -> Set[str]:
        problematic_services = set()
        for line in health_data:
            if "NAME" not in line and line.strip():
                try:
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        name = parts[1]
                        status = parts[3]
                        restarts = parts[4]
                        service = self._extract_service_name(name)                                            
                        
                        restart_count = int(restarts.split('(')[0].strip())
                        if restart_count > 0 or status == "CrashLoopBackOff":
                            problematic_services.add(service)
                except Exception as e:
                    self.logger.error(f"Failed to process line: {line.strip()}", exc_info=True)
                    continue
        
        return problematic_services

    def analyze_resource_usage(self, metrics_list: List[PodMetrics], service_name: str) -> Dict[str, Any]:
        """Analyze resource usage and generate recommendations."""
        try:
            # Convert list of PodMetrics to DataFrame
            df = pd.DataFrame([{
                'timestamp': m.timestamp,
                'cpu': m.cpu,
                'memory': m.memory,
                'name': m.name
            } for m in metrics_list])
            
            if df.empty:
                self.logger.warning(f"No metrics data for service: {service_name}")
                return {}
                
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            recommender = ResourceRecommenderProphet()
            cpu_rec = recommender.generate_recommendation(df, 'cpu')
            memory_rec = recommender.generate_recommendation(df, 'memory')
            
            # Create recommendations dict
            recommendations = {
                'service': service_name,
                'metrics': {
                    'cpu': {
                        'recommendation': cpu_rec['recommendation']['formatted'],
                        'forecast': cpu_rec['forecast'],
                        'factors': cpu_rec['factors']
                    },
                    'memory': {
                        'recommendation': memory_rec['recommendation']['formatted'],
                        'forecast': memory_rec['forecast'],
                        'factors': memory_rec['factors']
                    }
                }
            }
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to analyze resource usage for {service_name}: {str(e)}")
            return {}

    def run_analysis(self):
        perf_data = self.reader.read_performance_data()
        health_data = self.reader.read_health_data()
        metrics = self.processor.process_metrics(perf_data)
        problematic_services = self._process_health_data(health_data)
        
        service_recommendations = {}
        for service in problematic_services:
            service_metrics = [m for m in metrics if service in self._extract_service_name(m.name)]
            if service_metrics:
                self.visualizer.visualize_metrics(service_metrics, service)
                self.visualizer.create_resource_analysis(service_metrics, service)
                service_recommendations[service] = self.analyze_resource_usage(service_metrics, service)
        
        return problematic_services, service_recommendations
