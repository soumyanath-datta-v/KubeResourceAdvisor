import re
import pandas as pd
from typing import Dict, Any
import logging
from prophet import Prophet

class ResourceParser:
    def __init__(self):
        self.memory_units = {
            'Ki': 1/1024,      # Convert to Mi
            'Mi': 1,           # Base unit
            'Gi': 1024,        # Convert to Mi
            'Ti': 1024*1024    # Convert to Mi
        }
        self.cpu_units = {
            'm': 1,            # Base unit (millicores)
            '': 1000           # Convert cores to millicores
        }

    def _parse_kubernetes_memory(self, value: str) -> float:
        """Convert memory values to Mi"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if not isinstance(value, str):
                return 0.0

            match = re.match(r'^(\d+\.?\d*)([KMGT]i)?$', value)
            if match:
                number = float(match.group(1))
                unit = match.group(2) or ''
                return number * self.memory_units.get(unit, 1)
            return 0.0
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse memory value: {value}")
            return 0.0

    def parse_cpu(self, value: str) -> float:
        """Convert CPU values to millicores (m)"""
        try:
            if isinstance(value, (int, float)):
                return float(value) * 1000  # Convert cores to millicores
            
            if isinstance(value, str):
                if value.endswith('m'):
                    return float(value.rstrip('m'))
                return float(value) * 1000  # Convert cores to millicores
            return 0.0
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse CPU value: {value}")
            return 0.0

    def _preprocess_metrics(self, df: pd.DataFrame, resource_type: str) -> pd.DataFrame:
        """Preprocess metrics DataFrame for Prophet model with standardized units."""
        df_copy = df.copy()
        
        if resource_type == 'cpu':
            df_copy['y'] = df_copy['y'].apply(self.parse_cpu)  # Convert to millicores
        elif resource_type == 'memory':
            df_copy['y'] = df_copy['y'].apply(self._parse_kubernetes_memory)  # Convert to Mi
            
        return df_copy

class ResourceRecommenderProphet:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.memory_units = {
            'Ki': 1024,
            'Mi': 1024**2, 
            'Gi': 1024**3,
            'Ti': 1024**4
        }

    def _parse_kubernetes_cpu(self, value: str) -> float:
        """Convert Kubernetes CPU value (e.g. '393m') to float."""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                if value.endswith('m'):
                    return float(value.rstrip('m'))
                return float(value)
            return 0.0
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse CPU value: {value}")
            return 0.0

    def _parse_kubernetes_memory(self, value: str) -> float:
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            if not isinstance(value, str):
                return 0.0

            match = re.match(r'^(\d+\.?\d*)([KMGT]i)?$', value)
            if match:
                number = float(match.group(1))
                unit = match.group(2) or ''
                return number * self.memory_units.get(unit, 1)
            return 0.0
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse memory value: {value}")
            return 0.0

    def _preprocess_metrics(self, df: pd.DataFrame, resource_type: str) -> pd.DataFrame:
        """Preprocess metrics DataFrame for Prophet model."""
        df_copy = df.copy()
        
        if resource_type == 'cpu':
            df_copy[resource_type] = df_copy[resource_type].apply(self._parse_kubernetes_cpu)
        elif resource_type == 'memory':
            df_copy[resource_type] = df_copy[resource_type].apply(self._parse_kubernetes_memory)
        
        return df_copy.reset_index().rename(
            columns={'timestamp': 'ds', resource_type: 'y'}
        )

    def _format_recommendation(self, value: float, resource_type: str) -> Dict[str, Any]:
        """Format recommendation with proper units and ranges."""
        if resource_type == 'cpu':
            # Floor at 0 and convert to millicores
            cpu_cores = max(0, value)
            return {
                'raw_value': cpu_cores,
                'formatted': f"{int(cpu_cores * 1000)}m",
                'unit': 'millicores'
            }
        else:  # memory
            # Convert bytes to Mi and floor at 0
            memory_mi = max(0, value / (1024 * 1024))
            return {
                'raw_value': memory_mi,
                'formatted': f"{int(memory_mi)}Mi",
                'unit': 'Mi'
            }

    def generate_recommendation(self, metrics_df: pd.DataFrame, resource_type: str = 'cpu') -> Dict[str, Any]:
        try:
            processed_df = self._preprocess_metrics(metrics_df, resource_type)
            current_usage = processed_df['y'].mean()
            
            # Get forecast
            model = Prophet(
                growth='linear',                     # Use a simple linear trend
                # n_changepoints=5,                    # Reduce the number of changepoints
                # changepoint_range=1.0,               # Use the entire dataset for changepoints
                yearly_seasonality=False,            # Disable yearly seasonality
                weekly_seasonality=False,            # Disable weekly seasonality
                daily_seasonality=False,             # Disable daily seasonality
                seasonality_mode='additive',         # Additive seasonality for small datasets
                seasonality_prior_scale=5,           # Reduce flexibility to prevent overfitting
                interval_width=0.6,                  # Narrower confidence intervals
                uncertainty_samples=10,             # Reduce uncertainty sampling
            )

            model.add_seasonality(name='hourly', period=60, fourier_order=3)
            
            model.fit(processed_df)
            future = model.make_future_dataframe(periods=7, freq='T')
            forecast = model.predict(future)
            
            # Calculate recommendation
            peak_forecast = max(0, forecast['yhat_upper'].max())
            recommendation = peak_forecast * 1.2  # 20% buffer
            
            formatted_rec = self._format_recommendation(recommendation, resource_type)
            formatted_current = self._format_recommendation(current_usage, resource_type)
            
            return {
                'current_usage': formatted_current,
                'recommendation': formatted_rec,
                'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict('records'),
                'factors': {
                    'trend': forecast['trend'].mean(),
                    'daily_pattern': bool(model.daily_seasonality),
                    'weekly_pattern': bool(model.weekly_seasonality),
                    'buffer': 1.2
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to generate recommendation: {str(e)}")
            raise


