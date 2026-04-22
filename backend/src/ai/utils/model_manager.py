"""
Model Management System for AI Agents
Handles model loading, saving, versioning, and lifecycle management
"""
import os
import pickle
import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

import mlflow
import mlflow.sklearn
import mlflow.pytorch
import mlflow.tensorflow
from mlflow.tracking import MlflowClient

from ..config import ModelConfig, ModelType, AIConfig


@dataclass
class ModelMetadata:
    """Metadata for ML models"""
    model_id: str
    model_type: ModelType
    version: str
    created_at: datetime
    last_updated: datetime
    performance_metrics: Dict[str, float]
    training_data_hash: str
    hyperparameters: Dict[str, Any]
    deployment_status: str = "inactive"
    model_size_mb: float = 0.0


class ModelManager:
    """Manages ML models for AI agents"""
    
    def __init__(self, config: AIConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize MLflow
        mlflow.set_tracking_uri(config.mlflow_tracking_uri)
        mlflow.set_experiment(config.mlflow_experiment_name)
        self.mlflow_client = MlflowClient()
        
        # Model registry
        self.models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, ModelMetadata] = {}
        
        # Performance tracking
        self.model_performance: Dict[str, List[float]] = {}
        
        # Create model cache directory
        os.makedirs(config.model_cache_dir, exist_ok=True)
    
    def register_model(self, model: Any, config: ModelConfig, 
                      training_data_hash: str, 
                      performance_metrics: Dict[str, float]) -> str:
        """Register a new model with the manager"""
        
        model_id = self._generate_model_id(config.model_name, config.model_type)
        
        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            model_type=config.model_type,
            version=self.config.model_version,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            performance_metrics=performance_metrics,
            training_data_hash=training_data_hash,
            hyperparameters=config.hyperparameters,
            deployment_status="active"
        )
        
        # Store model and metadata
        self.models[model_id] = model
        self.model_metadata[model_id] = metadata
        
        # Log to MLflow
        with mlflow.start_run(run_name=f"{config.model_name}_{model_id}"):
            # Log parameters
            mlflow.log_params(config.hyperparameters)
            
            # Log metrics
            mlflow.log_metrics(performance_metrics)
            
            # Log model based on type
            self._log_model_to_mlflow(model, config.model_type)
            
            # Log metadata
            mlflow.log_dict(asdict(metadata), "model_metadata.json")
        
        self.logger.info(f"Registered model {model_id} of type {config.model_type}")
        return model_id
    
    def get_model(self, model_id: str) -> Optional[Any]:
        """Get a model by ID"""
        return self.models.get(model_id)
    
    def get_model_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID"""
        return self.model_metadata.get(model_id)
    
    def list_models(self, model_type: Optional[ModelType] = None) -> List[str]:
        """List all registered models, optionally filtered by type"""
        if model_type is None:
            return list(self.models.keys())
        
        return [
            model_id for model_id, metadata in self.model_metadata.items()
            if metadata.model_type == model_type
        ]
    
    def update_model_performance(self, model_id: str, metrics: Dict[str, float]) -> None:
        """Update model performance metrics"""
        if model_id not in self.model_metadata:
            raise ValueError(f"Model {model_id} not found")
        
        # Update metadata
        metadata = self.model_metadata[model_id]
        metadata.performance_metrics.update(metrics)
        metadata.last_updated = datetime.now()
        
        # Track performance history
        if model_id not in self.model_performance:
            self.model_performance[model_id] = []
        
        # Store primary metric (assume first metric is primary)
        primary_metric = list(metrics.values())[0] if metrics else 0.0
        self.model_performance[model_id].append(primary_metric)
        
        # Log to MLflow
        with mlflow.start_run(run_name=f"performance_update_{model_id}"):
            mlflow.log_metrics(metrics)
        
        self.logger.info(f"Updated performance for model {model_id}: {metrics}")
    
    def should_retrain_model(self, model_id: str, 
                           performance_threshold: float = 0.1) -> bool:
        """Check if a model should be retrained based on performance degradation"""
        if model_id not in self.model_performance:
            return False
        
        performance_history = self.model_performance[model_id]
        if len(performance_history) < 5:  # Need at least 5 data points
            return False
        
        # Check if performance has degraded significantly
        recent_avg = sum(performance_history[-3:]) / 3
        historical_avg = sum(performance_history[:-3]) / len(performance_history[:-3])
        
        degradation = (historical_avg - recent_avg) / historical_avg
        return degradation > performance_threshold
    
    def archive_model(self, model_id: str) -> None:
        """Archive a model (mark as inactive)"""
        if model_id in self.model_metadata:
            self.model_metadata[model_id].deployment_status = "archived"
            self.logger.info(f"Archived model {model_id}")
    
    def delete_model(self, model_id: str) -> None:
        """Delete a model from the registry"""
        if model_id in self.models:
            del self.models[model_id]
        if model_id in self.model_metadata:
            del self.model_metadata[model_id]
        if model_id in self.model_performance:
            del self.model_performance[model_id]
        
        self.logger.info(f"Deleted model {model_id}")
    
    def save_model_to_disk(self, model_id: str) -> str:
        """Save a model to disk"""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.models[model_id]
        metadata = self.model_metadata[model_id]
        
        # Create model directory
        model_dir = os.path.join(self.config.model_cache_dir, model_id)
        os.makedirs(model_dir, exist_ok=True)
        
        # Save model based on type
        model_path = os.path.join(model_dir, "model.pkl")
        
        try:
            if metadata.model_type in [ModelType.LSTM, ModelType.TRANSFORMER]:
                # PyTorch/TensorFlow models
                import torch
                if hasattr(model, 'state_dict'):
                    torch.save(model.state_dict(), model_path.replace('.pkl', '.pth'))
                else:
                    # TensorFlow model
                    model.save(model_path.replace('.pkl', '.h5'))
            else:
                # Scikit-learn and other models
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
            
            # Save metadata
            metadata_path = os.path.join(model_dir, "metadata.json")
            with open(metadata_path, 'w') as f:
                # Convert datetime objects to strings for JSON serialization
                metadata_dict = asdict(metadata)
                metadata_dict['created_at'] = metadata.created_at.isoformat()
                metadata_dict['last_updated'] = metadata.last_updated.isoformat()
                metadata_dict['model_type'] = metadata.model_type.value
                json.dump(metadata_dict, f, indent=2)
            
            self.logger.info(f"Saved model {model_id} to {model_dir}")
            return model_dir
            
        except Exception as e:
            self.logger.error(f"Failed to save model {model_id}: {e}")
            raise
    
    def load_model_from_disk(self, model_id: str) -> Optional[Any]:
        """Load a model from disk"""
        model_dir = os.path.join(self.config.model_cache_dir, model_id)
        
        if not os.path.exists(model_dir):
            self.logger.warning(f"Model directory {model_dir} not found")
            return None
        
        try:
            # Load metadata first
            metadata_path = os.path.join(model_dir, "metadata.json")
            with open(metadata_path, 'r') as f:
                metadata_dict = json.load(f)
            
            model_type = ModelType(metadata_dict['model_type'])
            
            # Load model based on type
            if model_type in [ModelType.LSTM, ModelType.TRANSFORMER]:
                # PyTorch model
                model_path = os.path.join(model_dir, "model.pth")
                if os.path.exists(model_path):
                    import torch
                    model = torch.load(model_path)
                else:
                    # TensorFlow model
                    model_path = os.path.join(model_dir, "model.h5")
                    import tensorflow as tf
                    model = tf.keras.models.load_model(model_path)
            else:
                # Scikit-learn and other models
                model_path = os.path.join(model_dir, "model.pkl")
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
            
            # Reconstruct metadata
            metadata = ModelMetadata(
                model_id=metadata_dict['model_id'],
                model_type=model_type,
                version=metadata_dict['version'],
                created_at=datetime.fromisoformat(metadata_dict['created_at']),
                last_updated=datetime.fromisoformat(metadata_dict['last_updated']),
                performance_metrics=metadata_dict['performance_metrics'],
                training_data_hash=metadata_dict['training_data_hash'],
                hyperparameters=metadata_dict['hyperparameters'],
                deployment_status=metadata_dict['deployment_status'],
                model_size_mb=metadata_dict.get('model_size_mb', 0.0)
            )
            
            # Register loaded model
            self.models[model_id] = model
            self.model_metadata[model_id] = metadata
            
            self.logger.info(f"Loaded model {model_id} from disk")
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_id}: {e}")
            return None
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered models"""
        stats = {
            "total_models": len(self.models),
            "models_by_type": {},
            "active_models": 0,
            "archived_models": 0,
            "average_performance": {}
        }
        
        for metadata in self.model_metadata.values():
            # Count by type
            model_type = metadata.model_type.value
            stats["models_by_type"][model_type] = stats["models_by_type"].get(model_type, 0) + 1
            
            # Count by status
            if metadata.deployment_status == "active":
                stats["active_models"] += 1
            elif metadata.deployment_status == "archived":
                stats["archived_models"] += 1
            
            # Calculate average performance
            if metadata.performance_metrics:
                primary_metric = list(metadata.performance_metrics.values())[0]
                if model_type not in stats["average_performance"]:
                    stats["average_performance"][model_type] = []
                stats["average_performance"][model_type].append(primary_metric)
        
        # Calculate averages
        for model_type, performances in stats["average_performance"].items():
            stats["average_performance"][model_type] = sum(performances) / len(performances)
        
        return stats
    
    def _generate_model_id(self, model_name: str, model_type: ModelType) -> str:
        """Generate a unique model ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content = f"{model_name}_{model_type.value}_{timestamp}"
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{model_name}_{hash_suffix}"
    
    def _log_model_to_mlflow(self, model: Any, model_type: ModelType) -> None:
        """Log model to MLflow based on its type"""
        try:
            if model_type in [ModelType.LSTM, ModelType.TRANSFORMER]:
                # PyTorch/TensorFlow models
                if hasattr(model, 'state_dict'):
                    mlflow.pytorch.log_model(model, "model")
                else:
                    mlflow.tensorflow.log_model(model, "model")
            else:
                # Scikit-learn and other models
                mlflow.sklearn.log_model(model, "model")
        except Exception as e:
            self.logger.warning(f"Failed to log model to MLflow: {e}")
    
    def cleanup_old_models(self, max_age_days: int = 30) -> None:
        """Clean up old archived models"""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        models_to_delete = []
        for model_id, metadata in self.model_metadata.items():
            if (metadata.deployment_status == "archived" and 
                metadata.last_updated < cutoff_date):
                models_to_delete.append(model_id)
        
        for model_id in models_to_delete:
            self.delete_model(model_id)
            # Also remove from disk
            model_dir = os.path.join(self.config.model_cache_dir, model_id)
            if os.path.exists(model_dir):
                import shutil
                shutil.rmtree(model_dir)
        
        self.logger.info(f"Cleaned up {len(models_to_delete)} old models")