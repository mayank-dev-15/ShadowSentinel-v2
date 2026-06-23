import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from core.features import FlowFeatures, FlowKey
from core.detector import AnomalyDetector


def _make_dummy_flow():
    key = FlowKey("10.0.0.1", "10.0.0.2", 12345, 80, 6)
    return FlowFeatures(
        flow_key=key, start_time=0.0, last_time=1.0, duration=1.0,
        fwd_packets=10, bwd_packets=8, fwd_bytes=1200, bwd_bytes=600,
        fwd_payload_bytes=800, bwd_payload_bytes=400,
        fwd_packet_lengths=[100, 120, 140, 160, 100, 120, 140, 160, 100, 60],
        bwd_packet_lengths=[80, 60, 80, 60, 80, 60, 80, 60],
        fwd_iat=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
        bwd_iat=[0.12, 0.1, 0.11, 0.1, 0.12, 0.1, 0.11],
        flags={'SYN': 1, 'ACK': 10, 'FIN': 1, 'RST': 0, 'PSH': 5, 'URG': 0},
        payload_entropy=[3.5, 4.0, 3.8],
    )


def test_detector_initialization():
    d = AnomalyDetector(contamination=0.05)
    assert d.contamination == 0.05
    assert d.model is not None


def test_detector_train_predict():
    d = AnomalyDetector(contamination=0.1)
    flows = [_make_dummy_flow() for _ in range(50)]
    d.train(flows)
    is_anomaly, confidence = d.predict(_make_dummy_flow())
    assert isinstance(is_anomaly, (bool, np.bool_))
    assert 0.0 <= confidence <= 1.0


def test_detector_save_load(tmp_path):
    d = AnomalyDetector(contamination=0.1)
    flows = [_make_dummy_flow() for _ in range(50)]
    d.train(flows)
    model_path = str(tmp_path / "test_model.pkl")
    d.save(model_path)
    d2 = AnomalyDetector(model_path=model_path)
    is_anomaly, confidence = d2.predict(_make_dummy_flow())
    assert isinstance(is_anomaly, (bool, np.bool_))


if __name__ == '__main__':
    test_detector_initialization()
    test_detector_train_predict()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_detector_save_load(tmp)
    print("All detector tests passed.")
