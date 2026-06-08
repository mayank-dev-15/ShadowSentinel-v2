"""
ML-based anomaly detector using ensemble of models.
"""
import numpy as np
import pickle
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from .features import FlowFeatures

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Ensemble anomaly detection with Isolation Forest + statistical baselines."""

    def __init__(self, model_path: Optional[str] = None, contamination: float = 0.01):
        self.contamination = contamination
        self.scaler = StandardScaler()
        self.model = None
        self.feature_mean = None
        self.feature_std = None
        self.threshold = 0.0

        if model_path and Path(model_path).exists():
            self.load(model_path)
        else:
            self.model = IsolationForest(
                n_estimators=100,
                max_samples='auto',
                contamination=contamination,
                bootstrap=True,
                n_jobs=-1,
                random_state=42,
            )

    def train(self, features: List[FlowFeatures]): # ... rest handled
        """Train detector on labeled or unlabeled flow data."""
        X = np.array([f.to_vector() for f in features])
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)

        scores = self.model.decision_function(X_scaled)
        self.feature_mean = np.mean(X_scaled, axis=0)
        self.feature_std = np.std(X_scaled, axis=0)
        self.threshold = np.percentile(scores, self.contamination * 100)
        logger.info(f"Trained on {len(features)} samples, threshold={self.threshold:.4f}")

    def predict(self, flow: FlowFeatures) -> Tuple[bool, float]:
        """Predict if flow is anomalous. Returns (is_anomaly, confidence)."""
        X = flow.to_vector().reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        score = self.model.decision_function(X_scaled)[0]
        is_anomaly = score < self.threshold

        # Statistical deviation score
        dev = np.mean(np.abs(X_scaled[0] - self.feature_mean) / (self.feature_std + 1e-8))
        confidence = float(1.0 / (1.0 + np.exp(-dev)))

        return is_anomaly, confidence

    def save(self, path: str):
        """Serialize model to disk."""
        artifact = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_mean': self.feature_mean,
            'feature_std': self.feature_std,
            'threshold': self.threshold,
        }
        with open(path, 'wb') as f:
            pickle.dump(artifact, f)
        logger.info(f"Model saved to {path}")

    def load(self, path: str):
        """Load serialized model."""
        with open(path, 'rb') as f:
            artifact = pickle.load(f)
        self.model = artifact['model']
        self.scaler = artifact['scaler']
        self.feature_mean = artifact['feature_mean']
        self.feature_std = artifact['feature_std']
        self.threshold = artifact['threshold']
        logger.info(f"Model loaded from {path}")
